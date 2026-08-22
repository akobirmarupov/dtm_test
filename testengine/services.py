"""Test sessiyasi biznes-logikasi.

Bu yerda bitta qoida markazlashtirilgan: **sessiya yakunlanmaguncha mijoz
javobning to'g'ri/noto'g'riligini bilmaydi**. Foydalanuvchi 15 ta savol
bo'ylab xohlagancha oldinga-orqaga yurib, javoblarini o'zgartiradi; natija
faqat `finish` bosilganda hisoblanadi va shundan keyin javoblar qotib qoladi.
"""

from __future__ import annotations

import logging

from django.db import models, transaction
from django.utils import timezone

from catalog.models import Question
from testengine.models import (
    MAX_QUESTION_COUNT,
    Answer,
    SessionQuestion,
    TestResult,
    TestSession,
)

logger = logging.getLogger('testengine.session')


def normalize_option(value) -> str:
    """Variant kalitini yagona ko'rinishga keltiradi ('a' -> 'A')."""
    return str(value or '').strip().upper()


def pick_questions(subject, count, topic_ids=None):
    """Sessiya uchun savollarni tanlaydi.

    Qiyinlik bo'yicha aralash bo'lishi uchun tasodifiy tanlanadi. `topic_ids`
    berilsa faqat shu mavzulardan olinadi.
    """
    queryset = Question.objects.filter(topic__subject=subject)
    if topic_ids:
        queryset = queryset.filter(topic_id__in=topic_ids)

    return list(queryset.order_by('?')[:min(count, MAX_QUESTION_COUNT)])


@transaction.atomic
def create_session(user, subject, mode, question_count, topic_ids=None):
    """Sessiya ochadi va savollar ro'yxatini QOTIRADI.

    Ro'yxat qotirilgani uchun foydalanuvchi 10-savoldan 3-savolga qaytganda
    aynan o'sha savolni ko'radi va javobini almashtira oladi.

    Savollar yetmasa mavjudicha olinadi va `question_count` shunga
    moslashtiriladi — sessiya "15 ta" deb yozilib, aslida 9 ta savol chiqib
    qolishi mumkin emas.
    """
    questions = pick_questions(subject, question_count, topic_ids)
    if not questions:
        return None

    session = TestSession.objects.create(
        user=user,
        subject=subject,
        mode=mode,
        question_count=len(questions),
    )

    SessionQuestion.objects.bulk_create([
        SessionQuestion(session=session, question=question, order=order)
        for order, question in enumerate(questions, start=1)
    ])

    logger.info(
        'Yangi test sessiyasi: id=%s subject=%s mode=%s savollar=%s user_id=%s',
        session.id, subject.name, mode, len(questions), user.id,
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
    }


def next_unanswered_order(session):
    """Keyingi javobsiz savolning tartib raqami (yo'q bo'lsa None)."""
    progress = session_progress(session)
    orders = progress['unanswered_orders']
    return orders[0] if orders else None


@transaction.atomic
def finish_session(session):
    """Sessiyani yakunlaydi va natijani hisoblaydi.

    Faqat shu paytdan boshlab javoblar o'zgarmaydi va to'g'ri javoblar
    ochiladi. `select_for_update` — ikkita parallel `finish` so'rovi ikkita
    `TestResult` yaratib yubormasligi uchun.
    """
    session = TestSession.objects.select_for_update().get(pk=session.pk)
    if session.finished_at:
        return None

    answers = list(session.answers.all())
    correct_count = sum(1 for answer in answers if answer.is_correct)
    incorrect_count = len(answers) - correct_count

    total_questions = SessionQuestion.objects.filter(session=session).count() or len(answers)
    unanswered_count = max(total_questions - len(answers), 0)

    session.finished_at = timezone.now()
    session.save(update_fields=['finished_at', 'updated_at'])

    duration = 0
    if session.started_at:
        duration = int((session.finished_at - session.started_at).total_seconds())

    result = TestResult.objects.create(
        session=session,
        total_score=correct_count,
        correct_count=correct_count,
        incorrect_count=incorrect_count,
        unanswered_count=unanswered_count,
        duration_seconds=max(duration, 0),
    )

    logger.info(
        'Test yakunlandi: session_id=%s ball=%s togri=%s xato=%s javobsiz=%s user_id=%s',
        session.id, correct_count, correct_count, incorrect_count,
        unanswered_count, session.user_id,
    )
    return result


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
