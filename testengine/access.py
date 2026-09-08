from __future__ import annotations

import random
from datetime import datetime, time, timedelta

from django.db import IntegrityError, transaction
from django.db.models import F
from django.utils import timezone

from billing.entitlements import GUEST_QUESTION_COUNT, Entitlements, entitlements_for
from testengine.models import MIN_TIER, QUESTION_COUNT_TIERS, DailyTopicUsage


def get_available_tiers(total_questions: int) -> list[int]:
    if total_questions is None or total_questions < MIN_TIER:
        return []
    return [tier for tier in QUESTION_COUNT_TIERS if total_questions >= tier]


def tiers_for(entitlements: Entitlements, total_questions: int) -> list[int]:
    tiers = get_available_tiers(total_questions)
    if not tiers:
        return []

    if not entitlements.can_choose_question_count:
        fixed = min(GUEST_QUESTION_COUNT, entitlements.max_question_count)
        return [fixed] if total_questions >= fixed else []

    return [tier for tier in tiers if tier <= entitlements.max_question_count]


def next_reset_at(now=None):
    now = now or timezone.localtime()
    tomorrow = timezone.localdate(now) + timedelta(days=1)
    naive_midnight = datetime.combine(tomorrow, time.min)
    return timezone.make_aware(naive_midnight, timezone.get_current_timezone())


def topics_used_today(user, date=None) -> int:
    if user is None or not getattr(user, 'is_authenticated', False):
        return 0
    return DailyTopicUsage.objects.filter(
        user=user, date=date or timezone.localdate()
    ).count()


def topic_access(user, topic, entitlements=None) -> dict:
    entitlements = entitlements or entitlements_for(user)
    reset_at = next_reset_at()

    if entitlements.is_guest or entitlements.has_unlimited_topics:
        return {
            'allowed': True,
            'code': 'ok',
            'detail': '',
            'limit': None,
            'used': 0,
            'remaining': None,
            'reset_at': reset_at,
        }

    today = timezone.localdate()
    limit = entitlements.daily_topic_limit
    used = topics_used_today(user, today)
    already_used = DailyTopicUsage.objects.filter(user=user, topic=topic, date=today).exists()

    allowed = already_used or used < limit
    remaining = max(limit - used, 0)

    return {
        'allowed': allowed,
        'code': 'ok' if allowed else 'daily_topic_limit_reached',
        'detail': '' if allowed else (
            f"Bugungi kunlik limitingiz ({limit} ta mavzu) tugadi. Ertaga 00:00 dan "
            f"keyin yangi mavzular ochiladi, yoki Pro sotib olib cheksiz mavzuda "
            f"test ishlang."
        ),
        'limit': limit,
        'used': used,
        'remaining': remaining,
        'reset_at': reset_at,
    }


def register_topic_usage(user, topic, date=None):
    if user is None or not getattr(user, 'is_authenticated', False) or topic is None:
        return None

    date = date or timezone.localdate()
    try:
        with transaction.atomic():
            usage, created = DailyTopicUsage.objects.get_or_create(
                user=user, topic=topic, date=date
            )
    except IntegrityError:
        created = False
        usage = DailyTopicUsage.objects.get(user=user, topic=topic, date=date)

    if not created:
        DailyTopicUsage.objects.filter(pk=usage.pk).update(
            sessions_started=F('sessions_started') + 1
        )
    return usage


def limit_response_payload(access: dict) -> dict:
    return {
        'detail': access['detail'],
        'code': access['code'],
        'daily_topic_limit': access['limit'],
        'topics_used_today': access['used'],
        'reset_at': access['reset_at'],
        'upgrade_required': True,
    }


# Yechim izohlari
def explanation_access(user, session, entitlements=None, *, consume=False) -> dict:
    from testengine.models import ExplanationUsage

    entitlements = entitlements or entitlements_for(user)

    if entitlements.is_guest:
        return {
            'available': False,
            'code': 'registration_required',
            'detail': "Yechim izohlarini ko'rish uchun ro'yxatdan o'ting.",
            'limit_per_day': 0,
            'used_today': 0,
            'remaining_today': 0,
            'upgrade_required': False,
        }

    if not entitlements.can_view_explanations:
        return {
            'available': False,
            'code': 'upgrade_required',
            'detail': "Yechim izohlari Pro tarifda ochiladi.",
            'limit_per_day': 0,
            'used_today': 0,
            'remaining_today': 0,
            'upgrade_required': True,
        }

    limit = entitlements.explanation_limit_per_day
    if limit is None:
        return {
            'available': True,
            'code': 'ok',
            'detail': '',
            'limit_per_day': None,
            'used_today': 0,
            'remaining_today': None,
            'upgrade_required': False,
        }

    today = timezone.localdate()
    already = ExplanationUsage.objects.filter(
        user=user, session=session, date=today
    ).exists()
    used = ExplanationUsage.objects.filter(user=user, date=today).count()

    if already:
        return {
            'available': True,
            'code': 'ok',
            'detail': '',
            'limit_per_day': limit,
            'used_today': used,
            'remaining_today': max(limit - used, 0),
            'upgrade_required': False,
        }

    if used >= limit:
        return {
            'available': False,
            'code': 'explanation_limit_reached',
            'detail': (
                f"Bugungi izoh limitingiz ({limit} ta test) tugadi. Ertaga 00:00 "
                f"dan keyin yangilanadi, yoki cheklovsiz tarifga o'ting."
            ),
            'limit_per_day': limit,
            'used_today': used,
            'remaining_today': 0,
            'upgrade_required': True,
        }

    if consume:
        try:
            with transaction.atomic():
                ExplanationUsage.objects.get_or_create(
                    user=user, session=session, date=today
                )
            used += 1
        except IntegrityError:
            pass

    return {
        'available': True,
        'code': 'ok',
        'detail': '',
        'limit_per_day': limit,
        'used_today': used,
        'remaining_today': max(limit - used, 0),
        'upgrade_required': False,
    }


def access_payload(access: dict) -> dict:
    """`topic_access()` natijasini API javob shakliga o'giradi."""
    return {
        'can_start': access['allowed'],
        'code': access['code'],
        'detail': access['detail'],
        'daily_topic_limit': access['limit'],
        'topics_used_today': access['used'],
        'topics_remaining_today': access['remaining'],
        'reset_at': access['reset_at'],
        'upgrade_required': not access['allowed'],
    }


class DailyTopicLimitExceeded(Exception):
    def __init__(self, payload):
        super().__init__(payload.get('detail', ''))
        self.payload = payload


def session_topic_ids(session) -> list[int]:
    from testengine.models import SessionQuestion

    return list(
        SessionQuestion.objects
        .filter(session=session)
        .order_by()
        .values_list('question__topic_id', flat=True)
        .distinct()
    )


def allowed_topic_ids(user, subject, entitlements=None) -> list[int] | None:
    entitlements = entitlements or entitlements_for(user)
    if entitlements.is_guest or entitlements.has_unlimited_topics:
        return None

    from catalog.models import Topic

    today = timezone.localdate()
    used_ids = set(
        DailyTopicUsage.objects
        .filter(user=user, date=today)
        .values_list('topic_id', flat=True)
    )
    remaining = max(entitlements.daily_topic_limit - len(used_ids), 0)

    candidates = list(
        Topic.objects
        .filter(subject=subject, is_active=True, available_question_count__gt=0)
        .values_list('id', flat=True)
    )
    allowed = [tid for tid in candidates if tid in used_ids]

    if remaining:
        fresh = [tid for tid in candidates if tid not in used_ids]
        random.shuffle(fresh)
        allowed.extend(fresh[:remaining])

    if allowed:
        return allowed
    return [] if remaining <= 0 else None


def register_session_topics(user, session, entitlements=None):
    entitlements = entitlements or entitlements_for(user)
    if entitlements.is_guest or entitlements.has_unlimited_topics:
        return []

    from catalog.models import Topic

    today = timezone.localdate()
    topic_ids = session_topic_ids(session)
    if not topic_ids:
        return []

    used_ids = set(
        DailyTopicUsage.objects
        .filter(user=user, date=today)
        .values_list('topic_id', flat=True)
    )
    new_ids = [tid for tid in topic_ids if tid not in used_ids]
    limit = entitlements.daily_topic_limit

    if len(used_ids) + len(new_ids) > limit:
        raise DailyTopicLimitExceeded(limit_response_payload({
            'allowed': False,
            'code': 'daily_topic_limit_reached',
            'detail': (
                f"Bugungi kunlik limitingiz ({limit} ta mavzu) tugadi. Ertaga "
                f"00:00 dan keyin yangi mavzular ochiladi, yoki Pro sotib olib "
                f"cheksiz mavzuda test ishlang."
            ),
            'limit': limit,
            'used': len(used_ids),
            'remaining': max(limit - len(used_ids), 0),
            'reset_at': next_reset_at(),
        }))

    for topic in Topic.objects.filter(id__in=topic_ids):
        register_topic_usage(user, topic, date=today)
    return topic_ids
