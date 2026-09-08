from __future__ import annotations

import logging
from datetime import timedelta

from django.db import IntegrityError, transaction
from django.db.models import F
from django.utils import timezone

from .models import ReviewCard, Streak, XPTransaction

logger = logging.getLogger('progress')


QUALITY_AGAIN = 2
QUALITY_HARD = 3
QUALITY_GOOD = 4
QUALITY_EASY = 5
PASS_THRESHOLD = 3

MIN_EASE_FACTOR = 1.3
DEFAULT_EASE_FACTOR = 2.5
FIRST_INTERVAL = 1
SECOND_INTERVAL = 6
MAX_INTERVAL_DAYS = 365


SLOW_ANSWER_SECONDS = 60


def quality_from_answer(is_correct, response_time_seconds=None) -> int:
    if not is_correct:
        return QUALITY_AGAIN
    if response_time_seconds and response_time_seconds > SLOW_ANSWER_SECONDS:
        return QUALITY_HARD
    if response_time_seconds is not None and response_time_seconds <= 10:
        return QUALITY_EASY
    return QUALITY_GOOD


def _apply_sm2(card, quality):
    quality = max(0, min(5, int(quality)))

    if quality < PASS_THRESHOLD:
        card.repetitions = 0
        card.interval_days = FIRST_INTERVAL
        card.lapses += 1
    else:
        if card.repetitions == 0:
            card.interval_days = FIRST_INTERVAL
        elif card.repetitions == 1:
            card.interval_days = SECOND_INTERVAL
        else:
            card.interval_days = min(
                int(round(card.interval_days * card.ease_factor)), MAX_INTERVAL_DAYS
            )
        card.repetitions += 1

    card.ease_factor = max(
        MIN_EASE_FACTOR,
        card.ease_factor + (0.1 - (5 - quality) * (0.08 + (5 - quality) * 0.02)),
    )

    now = timezone.now()
    card.last_reviewed_at = now
    card.next_review_date = timezone.localdate() + timedelta(days=card.interval_days)
    card.stability_days = float(card.interval_days)
    return card


def create_or_update_review_card(user, question, is_correct=False, response_time_seconds=None):
    card = ReviewCard.objects.filter(user=user, question=question).first()

    if card is None:
        if is_correct:
            return None
        card = ReviewCard(
            user=user,
            question=question,
            ease_factor=DEFAULT_EASE_FACTOR,
            interval_days=0,
            repetitions=0,
            next_review_date=timezone.localdate(),
        )
        _apply_sm2(card, quality_from_answer(is_correct, response_time_seconds))
        try:
            with transaction.atomic():
                card.save()
        except IntegrityError:
            card = ReviewCard.objects.get(user=user, question=question)
        return card

    _apply_sm2(card, quality_from_answer(is_correct, response_time_seconds))
    card.save(update_fields=[
        'ease_factor', 'interval_days', 'repetitions', 'lapses',
        'last_reviewed_at', 'next_review_date', 'stability_days', 'updated_at',
    ])
    return card


def submit_review_card_answer(card, is_correct, response_time=None):
    _apply_sm2(card, quality_from_answer(is_correct, response_time))
    card.save(update_fields=[
        'ease_factor', 'interval_days', 'repetitions', 'lapses',
        'last_reviewed_at', 'next_review_date', 'stability_days', 'updated_at',
    ])
    return card


def due_cards(user, limit=None):
    """Bugun takrorlash kerak bo'lgan kartalar."""
    queryset = (
        ReviewCard.objects
        .filter(user=user, next_review_date__lte=timezone.localdate())
        .select_related('question', 'question__topic', 'question__topic__subject')
        .order_by('next_review_date', 'id')
    )
    return queryset[:limit] if limit else queryset


# Streak
def update_streak_on_activity(user):
    streak, _ = Streak.objects.get_or_create(user=user)
    today = timezone.localdate()

    if streak.last_activity_date == today:
        return streak

    if streak.last_activity_date == today - timedelta(days=1):
        streak.current_streak += 1
    else:
        streak.current_streak = 1

    streak.longest_streak = max(streak.longest_streak, streak.current_streak)
    streak.last_activity_date = today
    streak.save(update_fields=['current_streak', 'longest_streak', 'last_activity_date'])
    return streak


def use_streak_freeze(streak):
    if streak.freezes_available > 0:
        streak.freezes_available -= 1
        streak.save(update_fields=['freezes_available'])
    return streak


# XP
@transaction.atomic
def award_xp(user, amount, source, description=''):
    amount = int(amount)
    if amount == 0:
        return None

    transaction_row = XPTransaction.objects.create(
        user=user, amount=amount, source=source, description=description,
    )

    type(user).objects.filter(pk=user.pk).update(
        xp_total=F('xp_total') + max(amount, 0)
    )
    user.refresh_from_db(fields=['xp_total'])
    return transaction_row


def total_xp(user) -> int:
    return int(user.xp_total or 0)
