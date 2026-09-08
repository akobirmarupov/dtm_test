"""Yutuqlar (nishonlar) — ta'riflar bazada, tekshiruv shu yerda.

Nega bazada: yutuq ro'yxati mahsulot bilan birga o'sadi. Kodda yozilsa har
bir yangi nishon uchun deploy kerak bo'lardi; admin panelda esa bir daqiqa.

Tekshiruv test yakunlanganda ishlaydi va faqat SHU foydalanuvchining
hisoblarini o'qiydi — butun jadval bo'ylab so'rov yo'q.
"""

from __future__ import annotations

import logging

from django.db import IntegrityError, transaction
from django.db.models import Sum

from .models import Achievement, UserAchievement

logger = logging.getLogger('progress.achievements')


def current_metrics(user) -> dict:
    """Foydalanuvchining barcha o'lchovlari — bitta joyda."""
    from rating.models import Rating, SubjectRating
    from testengine.models import Answer, TestResult

    from .models import Streak

    answers = Answer.objects.filter(session__user=user)
    answered = answers.count()
    correct = answers.filter(is_correct=True).count()

    results = TestResult.objects.filter(session__user=user)
    tests = results.count()
    perfect = results.filter(incorrect_count=0, unanswered_count=0, correct_count__gt=0).count()

    streak = Streak.objects.filter(user=user).values_list('current_streak', flat=True).first() or 0

    best_subject_stars = (
        SubjectRating.objects.filter(user=user).order_by('-stars')
        .values_list('stars', flat=True).first() or 0.0
    )

    return {
        Achievement.Metric.QUESTIONS_ANSWERED: answered,
        Achievement.Metric.CORRECT_ANSWERS: correct,
        Achievement.Metric.TESTS_COMPLETED: tests,
        Achievement.Metric.PERFECT_TESTS: perfect,
        Achievement.Metric.CURRENT_STREAK: streak,
        Achievement.Metric.TOTAL_XP: int(user.xp_total or 0),
        # ⭐ butun son bilan solishtirilishi uchun 10 ga ko'paytiriladi:
        # 4.2 ⭐ -> 42. Shunda admin «42» deb chegara qo'ya oladi.
        Achievement.Metric.SUBJECT_STARS: int(round(float(best_subject_stars) * 10)),
    }


def check_and_award(user) -> list:
    """Yangi qo'lga kiritilgan yutuqlarni beradi va ro'yxatini qaytaradi."""
    unlocked_codes = set(
        UserAchievement.objects.filter(user=user).values_list('achievement__code', flat=True)
    )
    pending = list(Achievement.objects.filter(is_active=True).exclude(code__in=unlocked_codes))
    if not pending:
        return []

    metrics = current_metrics(user)
    newly = []

    for achievement in pending:
        value = metrics.get(achievement.metric)
        if value is None or value < achievement.threshold:
            continue

        try:
            with transaction.atomic():
                UserAchievement.objects.create(
                    user=user, achievement=achievement, value_at_unlock=value,
                )
        except IntegrityError:
            # Parallel so'rov allaqachon bergan.
            continue

        newly.append(achievement)

        if achievement.xp_reward:
            from .services import award_xp
            award_xp(
                user=user, amount=achievement.xp_reward,
                source='bonus', description=f'Yutuq: {achievement.name}',
            )

    if newly:
        _notify(user, newly)
        logger.info(
            'Yutuqlar berildi: user_id=%s -> %s',
            user.id, ', '.join(a.code for a in newly),
        )
    return newly


def _notify(user, achievements):
    from notifications.models import NotificationLog

    NotificationLog.objects.bulk_create([
        NotificationLog(
            user=user,
            type=NotificationLog.Type.RATING_UP,
            message=f"Yangi yutuq: {achievement.icon} {achievement.name}!",
        )
        for achievement in achievements
    ])


def progress_for(user) -> list[dict]:
    """Barcha yutuqlar + foydalanuvchining ularga qanchalik yaqinligi.

    Qulflangan nishonlarni ham qaytaramiz: «100 ta savoldan 73 tasi»
    ko'rsatkichi nishonning o'zidan ko'ra kuchliroq motivatsiya beradi.
    """
    metrics = current_metrics(user)
    unlocked = {
        row.achievement_id: row
        for row in UserAchievement.objects.filter(user=user).select_related('achievement')
    }

    result = []
    for achievement in Achievement.objects.filter(is_active=True):
        value = metrics.get(achievement.metric, 0)
        row = unlocked.get(achievement.id)
        result.append({
            'achievement': achievement,
            'is_unlocked': row is not None,
            'unlocked_at': row.created_at if row else None,
            'current_value': value,
            'threshold': achievement.threshold,
            'progress_percent': (
                100.0 if row is not None
                else round(min(value / achievement.threshold, 1.0) * 100, 1)
                if achievement.threshold else 0.0
            ),
        })
    return result
