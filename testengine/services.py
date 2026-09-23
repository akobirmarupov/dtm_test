"""Test sessiyasi biznes-logikasi.

Bu yerda uchta qoida markazlashtirilgan:

1. **Sessiya yakunlanmaguncha mijoz javobning to'g'ri/noto'g'riligini
   bilmaydi.** Foydalanuvchi savollar bo'ylab xohlagancha oldinga-orqaga
   yurib, javoblarini o'zgartiradi; natija faqat `finish` bosilganda
   hisoblanadi va shundan keyin javoblar qotib qoladi.
2. **Savollar sessiya ochilganda qotiriladi.** Shu tufayli 10-savoldan
   3-savolga qaytganda aynan o'sha savol chiqadi.
3. **Imtihon rejimida muddat serverda.** Mijoz taymeriga ishonib bo'lmaydi.
"""

from __future__ import annotations

import logging
import random
from datetime import timedelta

from django.core.cache import cache
from django.db import models, transaction
from django.db.models import Case, F, When
from django.utils import timezone

from catalog.models import Question
from testengine.models import (
    EXAM_SECONDS_PER_QUESTION,
    MAX_QUESTION_COUNT,
    PRACTICE_MAX_SECONDS_PER_QUESTION,
    Answer,
    MockExam,
    SessionQuestion,
    TestResult,
    TestSession,
)

logger = logging.getLogger('testengine.session')

# Savol havzasi (id + qiyinlik) shuncha soniya keshlanadi. Savol qo'shilsa
# kesh `catalog.signals` orqali darhol tozalanadi, TTL — faqat himoya tarmog'i.
POOL_CACHE_TTL = 120
POOL_CACHE_PREFIX = 'questions:pool'

# Yaqinda ko'rilgan savollarni takrorlamaslik oynasi. Bazasi kichik mavzuda
# bu chegara avtomatik yumshaydi (pastga qarang).
RECENT_WINDOW_DAYS = 14
RECENT_LOOKUP_LIMIT = 5000


def normalize_option(value) -> str:
    """Variant kalitini yagona ko'rinishga keltiradi ('a' -> 'A')."""
    return str(value or '').strip().upper()


# ---------------------------------------------------------------------------
# Savol tanlash
# ---------------------------------------------------------------------------
def topic_pool_key(topic_id) -> str:
    return f'{POOL_CACHE_PREFIX}:topic:{topic_id}'


def subject_pool_key(subject_id) -> str:
    return f'{POOL_CACHE_PREFIX}:subject:{subject_id}'


def _fetch_pool(**filters) -> list[tuple[int, int]]:
    return list(
        Question.objects.available().filter(**filters).values_list('id', 'difficulty')
    )


def question_pool(subject=None, topic_ids=None) -> list[tuple[int, int]]:
    """`[(question_id, difficulty), ...]` — tanlash uchun xom havza.

    Nega `ORDER BY RANDOM()` ISHLATILMAYDI: PostgreSQL uni bajarish uchun
    butun jadvalni skanerlab, HAMMA qatorni saralaydi va shundan keyin 30
    tasini oladi. 100 000 savolda bitta sessiya ochish soniyalab vaqt oladi va
    bazani egallaydi. Bu yerda esa faqat ikkita ustun (id, difficulty)
    o'qiladi, aralashtirish Python tomonda bajariladi.

    Kesh HAR BIR MAVZU uchun alohida saqlanadi, mavzular to'plami uchun emas.
    Sabab: aralash mashqda mavzular to'plami har safar boshqacha bo'ladi va
    to'plam bo'yicha keshlansa kalitlar soni portlab ketardi, kesh esa deyarli
    hech qachon urmasdi.
    """
    if topic_ids:
        keys = {topic_id: topic_pool_key(topic_id) for topic_id in topic_ids}
        cached = cache.get_many(list(keys.values()))

        pool: list[tuple[int, int]] = []
        to_cache = {}
        for topic_id, key in keys.items():
            value = cached.get(key)
            if value is None:
                value = _fetch_pool(topic_id=topic_id)
                to_cache[key] = value
            pool.extend(value)

        if to_cache:
            cache.set_many(to_cache, POOL_CACHE_TTL)
        return pool

    if subject is None:
        return []

    subject_id = getattr(subject, 'id', subject)
    key = subject_pool_key(subject_id)
    cached = cache.get(key)
    if cached is not None:
        return cached

    pool = _fetch_pool(topic__subject_id=subject_id)
    cache.set(key, pool, POOL_CACHE_TTL)
    return pool


def invalidate_question_pool():
    """Savol qo'shilganda/tahrirlanganda havza keshini tozalaydi."""
    try:
        cache.delete_pattern(f'{POOL_CACHE_PREFIX}:*')
    except AttributeError:
        # `delete_pattern` — django-redis kengaytmasi. Boshqa backendda
        # (LocMemCache, testlar) TTL ning o'zi yetarli.
        cache.clear()


def recently_seen_ids(user, days=RECENT_WINDOW_DAYS) -> set[int]:
    """Foydalanuvchi oxirgi kunlarda ko'rgan savollar.

    Bularsiz kichik bazada foydalanuvchi bir xil savollarni aylantirib
    yechadi va o'rganish o'rniga yodlab oladi.
    """
    if user is None or not getattr(user, 'is_authenticated', False):
        return set()

    since = timezone.now() - timedelta(days=days)
    return set(
        SessionQuestion.objects
        .filter(session__user=user, session__created_at__gte=since)
        .values_list('question_id', flat=True)[:RECENT_LOOKUP_LIMIT]
    )


def difficulty_weights(skill_stars=None) -> dict[int, float]:
    """Qiyinlik taqsimoti — foydalanuvchi darajasiga moslashtirilgan.

    Kuchli talabaga oson savol berilsa zerikadi, kuchsizga qiyin savol
    berilsa taslim bo'ladi. Daraja `rating.TopicRating`/`SubjectRating`
    yulduzlaridan (0–5) olinadi; daraja noma'lum bo'lsa muvozanatli
    taqsimot ishlatiladi.
    """
    if skill_stars is None:
        return {1: 0.15, 2: 0.20, 3: 0.35, 4: 0.20, 5: 0.10}
    if skill_stars < 2.0:
        return {1: 0.25, 2: 0.30, 3: 0.30, 4: 0.10, 5: 0.05}
    if skill_stars < 3.5:
        return {1: 0.10, 2: 0.20, 3: 0.40, 4: 0.20, 5: 0.10}
    return {1: 0.05, 2: 0.10, 3: 0.30, 4: 0.35, 5: 0.20}


def user_skill_stars(user, subject=None, topic=None) -> float | None:
    """Foydalanuvchining shu mavzu/fandagi joriy darajasi (0–5 yulduz)."""
    if user is None or not getattr(user, 'is_authenticated', False):
        return None

    from rating.models import SubjectRating, TopicRating

    if topic is not None:
        stars = (
            TopicRating.objects
            .filter(user=user, topic=topic)
            .values_list('stars', flat=True)
            .first()
        )
        if stars is not None:
            return float(stars)

    if subject is not None:
        stars = (
            SubjectRating.objects
            .filter(user=user, subject=subject)
            .values_list('stars', flat=True)
            .first()
        )
        if stars is not None:
            return float(stars)

    return None


def _sample_by_difficulty(pool, count, weights) -> list[int]:
    """Havzadan `count` ta savolni qiyinlik taqsimotiga yaqin tanlaydi.

    Biror darajada savol yetmasa, kamomad qolgan savollardan to'ldiriladi —
    "45 ta so'radi, 31 ta chiqdi" degan holat bo'lmasligi kerak.
    """
    buckets: dict[int, list[int]] = {}
    for question_id, difficulty in pool:
        buckets.setdefault(int(difficulty or 3), []).append(question_id)
    for ids in buckets.values():
        random.shuffle(ids)

    selected: list[int] = []
    for level, weight in sorted(weights.items(), key=lambda item: -item[1]):
        bucket = buckets.get(level)
        if not bucket:
            continue
        take = min(round(count * weight), len(bucket))
        selected.extend(bucket[:take])
        del bucket[:take]

    if len(selected) < count:
        leftovers = [qid for ids in buckets.values() for qid in ids]
        random.shuffle(leftovers)
        selected.extend(leftovers[:count - len(selected)])

    selected = selected[:count]
    random.shuffle(selected)
    return selected


def pick_questions(subject=None, count=15, topic_ids=None, *, user=None, topic=None):
    """Sessiya uchun savollarni tanlaydi.

    Uch bosqich: (1) mavjud savollar havzasi, (2) yaqinda ko'rilganlarini
    chetlab o'tish, (3) qiyinlik bo'yicha moslashtirilgan tanlov.
    """
    count = max(int(count or 0), 0)
    if not count:
        return []
    count = min(count, MAX_QUESTION_COUNT)

    if topic is not None and not topic_ids:
        topic_ids = [topic.id]

    pool = question_pool(subject=subject, topic_ids=topic_ids)
    if not pool:
        return []

    seen = recently_seen_ids(user)
    fresh = [item for item in pool if item[0] not in seen]

    # Yangi savol yetmasa eskilaridan ham olamiz — foydalanuvchini "savol
    # qolmadi" deb qaytarib yuborishdan ko'ra takror savol berish afzal.
    working_pool = fresh if len(fresh) >= count else pool

    weights = difficulty_weights(user_skill_stars(user, subject=subject, topic=topic))
    ids = _sample_by_difficulty(working_pool, count, weights)
    if not ids:
        return []

    questions = Question.objects.filter(id__in=ids).select_related('topic')
    by_id = {question.id: question for question in questions}
    # Tanlangan tartibni saqlaymiz: `filter(id__in=...)` tartibi id bo'yicha
    # bo'lib qolardi va aralashtirish bekor bo'lardi.
    return [by_id[qid] for qid in ids if qid in by_id]


# ---------------------------------------------------------------------------
# Sessiya ochish
# ---------------------------------------------------------------------------
def exam_deadline(question_count, seconds_per_question=EXAM_SECONDS_PER_QUESTION, now=None):
    now = now or timezone.now()
    total = max(int(question_count), 1) * seconds_per_question
    return total, now + timedelta(seconds=total)


@transaction.atomic
def create_session(user, subject, mode, question_count, topic_ids=None, *,
                   topic=None, grade=None, time_limit_seconds=None):
    """Sessiya ochadi va savollar ro'yxatini QOTIRADI.

    Savollar yetmasa mavjudicha olinadi va `question_count` shunga
    moslashtiriladi — sessiya "30 ta" deb yozilib, aslida 9 ta savol chiqib
    qolishi mumkin emas.

    Imtihon rejimida server tomonda muddat qo'yiladi: `expires_at` o'tgach
    sessiya avtomatik yakunlanadi (`finish_expired_sessions`).
    """
    if topic is not None:
        subject = subject or topic.subject
        grade = grade or topic.grade
        topic_ids = topic_ids or [topic.id]

    questions = pick_questions(
        subject=subject, count=question_count, topic_ids=topic_ids,
        user=user, topic=topic,
    )
    if not questions:
        return None

    now = timezone.now()
    expires_at = None
    if mode == TestSession.Mode.EXAM:
        if time_limit_seconds:
            expires_at = now + timedelta(seconds=int(time_limit_seconds))
        else:
            time_limit_seconds, expires_at = exam_deadline(len(questions), now=now)

    session = TestSession.objects.create(
        user=user,
        subject=subject,
        topic=topic,
        grade=grade,
        mode=mode,
        question_count=len(questions),
        time_limit_seconds=time_limit_seconds,
        expires_at=expires_at,
    )

    SessionQuestion.objects.bulk_create([
        SessionQuestion(session=session, question=question, order=order)
        for order, question in enumerate(questions, start=1)
    ])

    logger.info(
        'Yangi test sessiyasi: id=%s subject=%s topic=%s mode=%s savollar=%s '
        'muddat=%s user_id=%s',
        session.id, getattr(subject, 'name', subject), getattr(topic, 'id', None),
        mode, len(questions), expires_at, user.id,
    )
    return session


def session_questions(session):
    """Sessiyaning qotirilgan savollari (tartib bo'yicha)."""
    return (
        SessionQuestion.objects
        .filter(session=session)
        .select_related('question', 'question__topic')
        .order_by('order')
    )


def answers_by_question(session):
    """{question_id: Answer} — savollar ro'yxatiga javoblarni ulash uchun."""
    return {answer.question_id: answer for answer in session.answers.all()}


def authorize_questions(session, question_ids):
    """Savollar shu sessiyada javob berilishi mumkinmi — tekshiradi.

    Ikki holat bor:

    * Sessiyada savollar qotirilgan (API orqali ochilgan) — faqat o'sha
      ro'yxatdagi savollarga javob berish mumkin.
    * Sessiyada savollar qotirilmagan (eski yozuvlar yoki to'g'ridan-to'g'ri
      yaratilgan sessiya) — sessiya faniga tegishli savollarga ruxsat
      beriladi va ular yo'l-yo'lakay ro'yxatga qo'shiladi.

    Qaytadi: ruxsat berilmagan savol id'lari to'plami (bo'sh bo'lsa hammasi
    joyida).
    """
    question_ids = set(question_ids)
    if not question_ids:
        return set()

    pinned = set(
        SessionQuestion.objects.filter(session=session).values_list('question_id', flat=True)
    )
    if pinned:
        return question_ids - pinned

    allowed = set(
        Question.objects
        .filter(id__in=question_ids, topic__subject=session.subject)
        .values_list('id', flat=True)
    )
    missing = question_ids - allowed
    if missing:
        return missing

    attach_questions(session, sorted(allowed))
    return set()


def attach_questions(session, question_ids):
    """Savollarni sessiya ro'yxati oxiriga qo'shadi (takrorlanmasdan)."""
    existing = set(
        SessionQuestion.objects.filter(session=session).values_list('question_id', flat=True)
    )
    new_ids = [qid for qid in question_ids if qid not in existing]
    if not new_ids:
        return

    last_order = (
        SessionQuestion.objects.filter(session=session)
        .aggregate(models.Max('order'))['order__max'] or 0
    )

    SessionQuestion.objects.bulk_create(
        [
            SessionQuestion(session=session, question_id=qid, order=last_order + offset)
            for offset, qid in enumerate(new_ids, start=1)
        ],
        ignore_conflicts=True,
    )

    total = SessionQuestion.objects.filter(session=session).count()
    if session.question_count < total:
        TestSession.objects.filter(pk=session.pk).update(question_count=total)
        session.question_count = total


def save_answer(session, question, selected_option, confidence='', time_spent_seconds=0):
    """Javobni saqlaydi yoki MAVJUDINI YANGILAYDI.

    Foydalanuvchi bir savolga necha marta qaytsa ham dublikat yozuv
    yaratilmaydi — oxirgi tanlovi kuchda qoladi.
    """
    selected_option = normalize_option(selected_option)
    correct_option = normalize_option(question.correct_option)

    answer, created = Answer.objects.update_or_create(
        session=session,
        question=question,
        defaults={
            'selected_option': selected_option,
            'is_correct': selected_option == correct_option,
            'confidence': confidence or '',
            'time_spent_seconds': time_spent_seconds or 0,
        },
    )
    return answer, created


def session_progress(session):
    """Nechta savol javoblangan va qaysi tartib raqamlari bo'sh qolgan."""
    ordered = list(
        SessionQuestion.objects.filter(session=session)
        .order_by('order')
        .values_list('order', 'question_id')
    )
    answered_ids = set(session.answers.values_list('question_id', flat=True))

    unanswered_orders = [order for order, qid in ordered if qid not in answered_ids]
    total = len(ordered) or session.question_count

    return {
        'total_questions': total,
        'answered_count': total - len(unanswered_orders),
        'unanswered_count': len(unanswered_orders),
        'unanswered_orders': unanswered_orders,
        'is_finished': session.is_finished,
        'seconds_left': session.seconds_left,
        'expires_at': session.expires_at,
    }


def next_unanswered_order(session):
    """Keyingi javobsiz savolning tartib raqami (yo'q bo'lsa None)."""
    progress = session_progress(session)
    orders = progress['unanswered_orders']
    return orders[0] if orders else None


# ---------------------------------------------------------------------------
# Yakunlash
# ---------------------------------------------------------------------------
def _effective_duration(session, finished_at) -> int:
    """Sessiya davomiyligi — mantiqiy chegara bilan.

    Foydalanuvchi testni ochib qo'yib ertaga yopishi mumkin. Xom
    `finished_at - started_at` bunda 90 000 soniya bo'lib chiqadi va
    statistikani ham, reytingni ham buzadi.
    """
    if not session.started_at:
        return 0

    raw = int((finished_at - session.started_at).total_seconds())
    if raw <= 0:
        return 0

    if session.time_limit_seconds:
        return min(raw, session.time_limit_seconds)

    ceiling = max(session.question_count, 1) * PRACTICE_MAX_SECONDS_PER_QUESTION
    return min(raw, ceiling)


def _update_question_stats(answers):
    """Savollarning haqiqiy qiyinlik statistikasini yangilaydi.

    Qo'lda qo'yilgan `difficulty` taxminiy bo'ladi; `times_answered` /
    `times_correct` esa savolning haqiqiy p-qiymatini beradi.
    """
    if not answers:
        return

    correct_ids = [a.question_id for a in answers if a.is_correct]
    incorrect_ids = [a.question_id for a in answers if not a.is_correct]

    if correct_ids:
        Question.objects.filter(id__in=correct_ids).update(
            times_answered=F('times_answered') + 1,
            times_correct=F('times_correct') + 1,
        )
    if incorrect_ids:
        Question.objects.filter(id__in=incorrect_ids).update(
            times_answered=F('times_answered') + 1,
        )

    timed = [a for a in answers if a.time_spent_seconds]
    if timed:
        # Har bir savolga o'z vaqti qo'shiladi — bitta so'rovda.
        Question.objects.filter(id__in=[a.question_id for a in timed]).update(
            total_time_seconds=Case(
                *[
                    When(id=a.question_id,
                         then=F('total_time_seconds') + a.time_spent_seconds)
                    for a in timed
                ],
                default=F('total_time_seconds'),
                # `output_field` SHART: `PositiveIntegerField + int` aralash
                # tur beradi va Django uni o'zi aniqlay olmaydi.
                output_field=models.PositiveIntegerField(),
            )
        )


@transaction.atomic
def finish_session(session, *, auto=False):
    """Sessiyani yakunlaydi va natijani hisoblaydi.

    Faqat shu paytdan boshlab javoblar o'zgarmaydi va to'g'ri javoblar
    ochiladi. `select_for_update` — ikkita parallel `finish` so'rovi ikkita
    `TestResult` yaratib yubormasligi uchun.
    """
    session_row = TestSession.objects.select_for_update().get(pk=session.pk)
    if session_row.finished_at:
        return None

    answers = list(session_row.answers.all())
    correct_count = sum(1 for answer in answers if answer.is_correct)
    incorrect_count = len(answers) - correct_count

    total_questions = SessionQuestion.objects.filter(session=session_row).count() or len(answers)
    unanswered_count = max(total_questions - len(answers), 0)

    now = timezone.now()
    # Muddati o'tgan sessiyada yakunlash vaqti — muddat tugagan payt, hozir
    # emas. Aks holda "3 kun ishladi" bo'lib chiqadi.
    finished_at = (
        min(now, session_row.expires_at)
        if session_row.expires_at is not None else now
    )

    session_row.finished_at = finished_at
    session_row.auto_finished = auto
    session_row.save(update_fields=['finished_at', 'auto_finished', 'updated_at'])

    _update_question_stats(answers)

    result = TestResult.objects.create(
        session=session_row,
        total_score=correct_count,
        correct_count=correct_count,
        incorrect_count=incorrect_count,
        unanswered_count=unanswered_count,
        duration_seconds=_effective_duration(session_row, finished_at),
    )

    # Chaqiruvchidagi obyekt eskirib qolmasin.
    session.finished_at = session_row.finished_at
    session.auto_finished = session_row.auto_finished

    logger.info(
        'Test yakunlandi: session_id=%s ball=%s togri=%s xato=%s javobsiz=%s '
        'avtomatik=%s user_id=%s',
        session_row.id, correct_count, correct_count, incorrect_count,
        unanswered_count, auto, session_row.user_id,
    )
    return result


def ensure_not_expired(session):
    """Muddati o'tgan sessiyani yakunlaydi.

    Har bir sessiya endpointida chaqiriladi: foydalanuvchi taymer tugagandan
    keyin javob yubormoqchi bo'lsa, avval sessiya yopiladi.

    Qaytadi: `True` — sessiya shu chaqiruvda avtomatik yakunlandi.
    """
    if not session.is_expired:
        return False
    finish_session(session, auto=True)
    session.refresh_from_db()
    return True


def finish_expired_sessions(limit=500) -> int:
    """Muddati o'tgan ochiq sessiyalarni yopadi (davriy vazifa uchun)."""
    now = timezone.now()
    expired = TestSession.objects.filter(
        finished_at__isnull=True, expires_at__isnull=False, expires_at__lte=now
    ).order_by('expires_at')[:limit]

    closed = 0
    for session in list(expired):
        if finish_session(session, auto=True) is not None:
            closed += 1

    if closed:
        logger.info('Muddati tugagan sessiyalar yopildi: %s ta', closed)
    return closed


def build_review(session):
    """Yakunlangan sessiya uchun to'liq tahlil: savol, tanlangan javob,
    to'g'ri javob, to'g'ri/noto'g'ri. Sessiya yakunlanmagan bo'lsa
    chaqirilmasligi kerak — bu ma'lumot javoblarni ochib beradi."""
    answers = answers_by_question(session)
    review = []

    for item in session_questions(session):
        answer = answers.get(item.question_id)
        review.append({
            'order': item.order,
            'question': item.question,
            'answer': answer,
        })

    return review


# ---------------------------------------------------------------------------
# DTM blok imtihoni
# ---------------------------------------------------------------------------
class NotEnoughQuestionsForExam(Exception):
    """Tanlangan fanlardan birida yetarli savol yo'q."""

    def __init__(self, subject):
        super().__init__(str(subject))
        self.subject = subject


@transaction.atomic
def create_mock_exam(user, subjects, question_count,
                     seconds_per_question=EXAM_SECONDS_PER_QUESTION):
    """Har bir fan uchun bitta imtihon sessiyasi ochadi.

    Taymer YAGONA: barcha sessiyalar bir vaqtda tugaydi, xuddi haqiqiy
    imtihondagidek. Shuning uchun bir fanda tez ishlagan vaqt boshqasiga
    qoladi.
    """
    total_seconds = len(subjects) * int(question_count) * seconds_per_question
    now = timezone.now()

    exam = MockExam.objects.create(
        user=user,
        time_limit_seconds=total_seconds,
        expires_at=now + timedelta(seconds=total_seconds),
    )

    for order, subject in enumerate(subjects, start=1):
        session = create_session(
            user=user,
            subject=subject,
            mode=TestSession.Mode.EXAM,
            question_count=question_count,
            time_limit_seconds=total_seconds,
        )
        if session is None:
            raise NotEnoughQuestionsForExam(subject)

        # Barcha sessiyalar imtihon bilan bir paytda tugasin — `create_session`
        # har biriga o'z soniyasini qo'yadi, farq bir necha soniya bo'lsa ham
        # foydalanuvchiga g'alati ko'rinadi.
        TestSession.objects.filter(pk=session.pk).update(
            mock_exam=exam, exam_order=order, expires_at=exam.expires_at
        )

    logger.info(
        'Blok imtihoni boshlandi: exam_id=%s fanlar=%s savol=%s user_id=%s',
        exam.id, len(subjects), question_count, user.id,
    )
    return exam


def exam_sessions(exam):
    return (
        exam.sessions
        .select_related('subject')
        .prefetch_related('result')
        .order_by('exam_order', 'id')
    )


@transaction.atomic
def finish_mock_exam(exam, *, auto=False):
    """Imtihonni va uning barcha ochiq sessiyalarini yakunlaydi."""
    exam_row = MockExam.objects.select_for_update().get(pk=exam.pk)
    if exam_row.finished_at:
        return exam_row

    for session in exam_row.sessions.filter(finished_at__isnull=True):
        finish_session(session, auto=auto)

    now = timezone.now()
    exam_row.finished_at = min(now, exam_row.expires_at) if auto else now
    exam_row.auto_finished = auto
    exam_row.save(update_fields=['finished_at', 'auto_finished', 'updated_at'])

    exam.finished_at = exam_row.finished_at
    exam.auto_finished = exam_row.auto_finished

    logger.info(
        'Blok imtihoni yakunlandi: exam_id=%s avtomatik=%s user_id=%s',
        exam_row.id, auto, exam_row.user_id,
    )
    return exam_row


def mock_exam_summary(exam) -> dict:
    """Fanlar kesimidagi va umumiy natija.

    Yakunlanmagan imtihonda ham chaqirsa bo'ladi — u holda faqat tugagan
    fanlar hisobga kiradi.
    """
    subjects = []
    totals = {'correct': 0, 'incorrect': 0, 'unanswered': 0, 'questions': 0}

    for session in exam_sessions(exam):
        result = getattr(session, 'result', None)
        row = {
            'session_id': session.id,
            'order': session.exam_order,
            'subject_id': session.subject_id,
            'subject': session.subject,
            'question_count': session.question_count,
            'is_finished': session.is_finished,
            'correct_count': result.correct_count if result else 0,
            'incorrect_count': result.incorrect_count if result else 0,
            'unanswered_count': result.unanswered_count if result else 0,
            'total_score': result.total_score if result else 0,
        }
        subjects.append(row)

        totals['questions'] += session.question_count
        totals['correct'] += row['correct_count']
        totals['incorrect'] += row['incorrect_count']
        totals['unanswered'] += row['unanswered_count']

    answered = totals['correct'] + totals['incorrect']
    accuracy = round(totals['correct'] / answered * 100, 1) if answered else 0.0

    return {
        'subjects': subjects,
        'total_questions': totals['questions'],
        'correct_count': totals['correct'],
        'incorrect_count': totals['incorrect'],
        'unanswered_count': totals['unanswered'],
        'total_score': totals['correct'],
        'accuracy_percent': accuracy,
    }


def ensure_exam_not_expired(exam) -> bool:
    """Muddati o'tgan imtihonni yopadi. `True` — shu chaqiruvda yopildi."""
    if not exam.is_expired:
        return False
    finish_mock_exam(exam, auto=True)
    exam.refresh_from_db()
    return True


def finish_expired_mock_exams(limit=200) -> int:
    """Muddati o'tgan, lekin yakunlanmagan blok imtihonlari (davriy vazifa)."""
    now = timezone.now()
    expired = MockExam.objects.filter(
        finished_at__isnull=True, expires_at__lte=now
    ).order_by('expires_at')[:limit]

    closed = 0
    for exam in list(expired):
        if finish_mock_exam(exam, auto=True).finished_at is not None:
            closed += 1

    if closed:
        logger.info('Muddati tugagan blok imtihonlari yopildi: %s ta', closed)
    return closed
