from datetime import timedelta
from django.utils import timezone

from .models import ReviewCard, Streak, XPTransaction


def create_or_update_review_card(user, question):
    card, created = ReviewCard.objects.get_or_create(
        user=user,
        question=question,
        defaults={'stability_days': 1.0, 'next_review_date': timezone.now().date()},
    )
    if not created:
        card.stability_days = max(1.0, card.stability_days * 0.5)
        card.next_review_date = timezone.now().date() + timedelta(days=card.stability_days)
        card.save(update_fields=['stability_days', 'next_review_date'])
    return card


def update_streak_on_activity(user):
    streak, _ = Streak.objects.get_or_create(user=user)
    today = timezone.now().date()

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


def award_xp(user, amount, source, description=''):
    return XPTransaction.objects.create(
        user=user, amount=amount, source=source, description=description,
    )

def submit_review_card_answer(card, is_correct, response_time):
    if is_correct:
        card.stability_days = card.stability_days * 2.0 
    else:
        card.stability_days = max(1.0, card.stability_days * 0.5)

    card.next_review_date = timezone.now().date() + timedelta(days=card.stability_days)
    card.save(update_fields=['stability_days', 'next_review_date'])
    return card


def use_streak_freeze(streak):
    if streak.freezes_available > 0:
        streak.freezes_available -= 1
        streak.save(update_fields=['freezes_available'])
    return streak