from __future__ import annotations

import logging
from datetime import date, timedelta

from django.db import transaction
from django.db.models import F
from django.utils import timezone

from testengine.scoring import raw_accuracy, score_from_result, stars_from_points

from .models import (
    Leaderboard,
    Rating,
    RatingHistory,
    SubjectRating,
    TopicRating,
)

logger = logging.getLogger('rating')
ALL_TIME_START = date(2000, 1, 1)
ALL_TIME_END = date(2100, 1, 1)

LEADERBOARD_LIMIT = 100


# Davrlar
def get_period_dates(period, today=None):
    today = today or timezone.localdate()

    if period == Rating.PeriodChoices.DAILY:
        return today, today

    if period == Rating.PeriodChoices.WEEKLY:
        week_start = today - timedelta(days=today.weekday())
        return week_start, week_start + timedelta(days=6)

    if period == Rating.PeriodChoices.ALL_TIME:
        return ALL_TIME_START, ALL_TIME_END

    return today, today


ALL_PERIODS = (
    Rating.PeriodChoices.DAILY,
    Rating.PeriodChoices.WEEKLY,
    Rating.PeriodChoices.ALL_TIME,
)


# ⭐ hisobi
def calculate_stars(earned_points, possible_points) -> float:
    """To'plangan balldan daraja (0–5)."""
    return stars_from_points(earned_points, possible_points)


# Yangilash
@transaction.atomic
def update_or_create_rating(user, test_session, score):
    for period in ALL_PERIODS:
        start_date, end_date = get_period_dates(period)

        rating, _ = Rating.objects.get_or_create(
            user=user, period=period,
            period_start_date=start_date, period_end_date=end_date,
        )

        old_stars = rating.stars
        old_rank = rating.rank

        rating.tests_completed += 1
        rating.correct_answers += score.correct_count
        rating.incorrect_answers += score.incorrect_count
        rating.unanswered_answers += score.unanswered_count
        rating.earned_points += score.earned
        rating.possible_points += score.possible
        rating.xp += score.xp
        rating.stars = calculate_stars(rating.earned_points, rating.possible_points)
        rating.save()

        if old_stars != rating.stars:
            RatingHistory.objects.create(
                user=user, rating=rating,
                previous_stars=old_stars, new_stars=rating.stars,
                stars_change=round(rating.stars - old_stars, 2),
                previous_rank=old_rank, new_rank=rating.rank,
                test_session=test_session, period=period,
                reason=(
                    f"{score.correct_count} to'g'ri, {score.incorrect_count} xato, "
                    f"{score.unanswered_count} javobsiz -> {rating.stars:.2f} ⭐"
                ),
            )


@transaction.atomic
def update_topic_rating(user, topic, correct_count, incorrect_count,
                        unanswered_count, earned, possible):
    topic_rating, _ = TopicRating.objects.get_or_create(user=user, topic=topic)

    topic_rating.tests_completed += 1
    topic_rating.correct_answers += correct_count
    topic_rating.incorrect_answers += incorrect_count
    topic_rating.unanswered_answers += unanswered_count
    topic_rating.earned_points += earned
    topic_rating.possible_points += possible
    topic_rating.stars = calculate_stars(
        topic_rating.earned_points, topic_rating.possible_points
    )
    topic_rating.save()
    return topic_rating


@transaction.atomic
def update_subject_rating(user, subject, score):
    subject_rating, _ = SubjectRating.objects.get_or_create(user=user, subject=subject)

    subject_rating.tests_completed += 1
    subject_rating.correct_answers += score.correct_count
    subject_rating.incorrect_answers += score.incorrect_count
    subject_rating.unanswered_answers += score.unanswered_count
    subject_rating.earned_points += score.earned
    subject_rating.possible_points += score.possible
    subject_rating.stars = calculate_stars(
        subject_rating.earned_points, subject_rating.possible_points
    )
    subject_rating.topics_completed = (
        TopicRating.objects.filter(user=subject_rating.user, topic__subject=subject).count()
    )
    subject_rating.save()
    return subject_rating


def _topic_breakdown(session):
    """Sessiyani mavzular kesimida ballga ajratadi.

    Fan bo'yicha aralash testda savollar bir necha mavzudan keladi va har
    biri o'z `TopicRating` iga tushishi kerak.
    """
    from testengine.models import Answer, SessionQuestion
    from testengine.scoring import difficulty_weight

    answers = {
        answer.question_id: answer
        for answer in Answer.objects.filter(session=session)
    }

    breakdown = {}
    items = (
        SessionQuestion.objects
        .filter(session=session)
        .select_related('question')
        .order_by('order')
    )
    for item in items:
        bucket = breakdown.setdefault(item.question.topic_id, {
            'correct': 0, 'incorrect': 0, 'unanswered': 0,
            'earned': 0.0, 'possible': 0.0,
        })
        weight = difficulty_weight(item.question.difficulty)
        bucket['possible'] += weight

        answer = answers.get(item.question_id)
        if answer is None:
            bucket['unanswered'] += 1
        elif answer.is_correct:
            bucket['correct'] += 1
            bucket['earned'] += weight
        else:
            bucket['incorrect'] += 1

    return breakdown


def update_ratings_for_test_result(test_result):
    session = test_result.session
    user = session.user
    score = score_from_result(test_result)

    if not score.total_questions:
        return False

    update_or_create_rating(user, session, score)
    update_subject_rating(user, session.subject, score)

    from catalog.models import Topic

    breakdown = _topic_breakdown(session)
    if breakdown:
        topics = Topic.objects.filter(id__in=breakdown.keys())
        for topic in topics:
            bucket = breakdown[topic.id]
            update_topic_rating(
                user=user, topic=topic,
                correct_count=bucket['correct'],
                incorrect_count=bucket['incorrect'],
                unanswered_count=bucket['unanswered'],
                earned=bucket['earned'],
                possible=bucket['possible'],
            )

    # Leaderboard keshi eskirdi — keyingi so'rovda qayta hisoblanadi.
    invalidate_leaderboard_cache()
    return True


# Leaderboard (materialized snapshot)
def invalidate_leaderboard_cache():
    from django.core.cache import cache

    try:
        cache.delete_pattern('rating:leaderboard:*')
    except AttributeError:
        for period in ALL_PERIODS:
            cache.delete(f'rating:leaderboard:{period}')


@transaction.atomic
def rebuild_leaderboard(period, limit=LEADERBOARD_LIMIT):
    start_date, end_date = get_period_dates(period)
    rows = list(
        Rating.objects
        .filter(period=period, period_start_date=start_date, period_end_date=end_date)
        .select_related('user')
        .order_by('-xp', '-stars', 'user_id')[:limit]
    )

    Leaderboard.objects.filter(period=period, period_start_date=start_date).delete()

    entries = []
    updated_ratings = []
    for index, rating in enumerate(rows, start=1):
        rating.rank = index
        updated_ratings.append(rating)
        entries.append(Leaderboard(
            period=period,
            period_start_date=start_date,
            period_end_date=end_date,
            rank=index,
            user=rating.user,
            xp=rating.xp,
            stars=rating.stars,
            tests_completed=rating.tests_completed,
        ))

    if entries:
        Leaderboard.objects.bulk_create(entries)
        Rating.objects.bulk_update(updated_ratings, ['rank'], batch_size=500)

    logger.info('Leaderboard qayta hisoblandi: period=%s qatorlar=%s', period, len(entries))
    return len(entries)


def rebuild_all_leaderboards(limit=LEADERBOARD_LIMIT) -> int:
    total = sum(rebuild_leaderboard(period, limit) for period in ALL_PERIODS)
    invalidate_leaderboard_cache()
    return total


def leaderboard_rows(period, limit=50):
    """Snapshot'dan o'qiydi. Bo'sh bo'lsa (birinchi ishga tushirish) —
    yo'l-yo'lakay hisoblab, keyin o'qiydi."""
    start_date, _ = get_period_dates(period)

    queryset = (
        Leaderboard.objects
        .filter(period=period, period_start_date=start_date)
        .select_related('user')
        .order_by('rank')
    )
    if not queryset.exists():
        rebuild_leaderboard(period)

    return list(queryset[:limit])


def user_rank(user, period):
    start_date, end_date = get_period_dates(period)
    rating = Rating.objects.filter(
        user=user, period=period,
        period_start_date=start_date, period_end_date=end_date,
    ).first()
    if rating is None:
        return None, None

    ahead = Rating.objects.filter(
        period=period, period_start_date=start_date, period_end_date=end_date,
        xp__gt=rating.xp,
    ).count()
    total = Rating.objects.filter(
        period=period, period_start_date=start_date, period_end_date=end_date,
    ).count()
    return ahead + 1, total


# Zaif mavzular
MIN_ANSWERS_FOR_WEAKNESS = 10
WEAK_STARS_THRESHOLD = 3.0


def weak_topics(user, limit=10):
    return list(
        TopicRating.objects
        .filter(user=user, stars__lt=WEAK_STARS_THRESHOLD)
        .annotate(answered=F('correct_answers') + F('incorrect_answers'))
        .filter(answered__gte=MIN_ANSWERS_FOR_WEAKNESS)
        .select_related('topic', 'topic__subject', 'topic__grade')
        .order_by('stars', '-answered')[:limit]
    )


def accuracy_of(rating) -> float:
    return raw_accuracy(rating.earned_points, rating.possible_points)
