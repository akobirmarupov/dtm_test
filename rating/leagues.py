from __future__ import annotations

import logging

from django.db import IntegrityError, transaction
from django.db.models import Count

from rating.models import League, LeagueMembership, Rating
from rating.services import get_period_dates

logger = logging.getLogger('rating.league')

LEAGUE_SIZE = 30
PROMOTE_COUNT = 7
DEMOTE_COUNT = 5

MIN_TIER = League.Tier.BRONZE
MAX_TIER = League.Tier.DIAMOND


def current_week():
    return get_period_dates(Rating.PeriodChoices.WEEKLY)


def _open_group(tier, start_date, end_date):
    existing = (
        League.objects
        .filter(tier=tier, period_start_date=start_date)
        .annotate(member_count=Count('memberships'))
        .filter(member_count__lt=LEAGUE_SIZE)
        .order_by('group_number')
        .first()
    )
    if existing is not None:
        return existing

    last_number = (
        League.objects
        .filter(tier=tier, period_start_date=start_date)
        .order_by('-group_number')
        .values_list('group_number', flat=True)
        .first()
    ) or 0

    try:
        return League.objects.create(
            tier=tier, group_number=last_number + 1,
            period_start_date=start_date, period_end_date=end_date,
        )
    except IntegrityError:
        return League.objects.get(
            tier=tier, group_number=last_number + 1, period_start_date=start_date
        )


def previous_tier(user, start_date):
    last = (
        LeagueMembership.objects
        .filter(user=user, league__period_start_date__lt=start_date)
        .select_related('league')
        .order_by('-league__period_start_date')
        .first()
    )
    if last is None:
        return MIN_TIER

    tier = last.league.tier
    if last.outcome == LeagueMembership.Outcome.PROMOTED:
        return min(tier + 1, MAX_TIER)
    if last.outcome == LeagueMembership.Outcome.DEMOTED:
        return max(tier - 1, MIN_TIER)
    return tier


@transaction.atomic
def ensure_membership(user, start_date=None, end_date=None):
    if start_date is None or end_date is None:
        start_date, end_date = current_week()

    membership = (
        LeagueMembership.objects
        .select_related('league')
        .filter(user=user, league__period_start_date=start_date)
        .first()
    )
    if membership is not None:
        return membership

    tier = previous_tier(user, start_date)
    league = _open_group(tier, start_date, end_date)

    try:
        return LeagueMembership.objects.create(user=user, league=league, xp=0)
    except IntegrityError:
        return LeagueMembership.objects.get(user=user, league=league)


def add_xp(user, amount, start_date=None, end_date=None):
    if amount <= 0:
        return None

    membership = ensure_membership(user, start_date, end_date)
    LeagueMembership.objects.filter(pk=membership.pk).update(xp=membership.xp + amount)
    membership.refresh_from_db(fields=['xp'])
    return membership


def standings(league):
    rows = list(
        LeagueMembership.objects
        .filter(league=league)
        .select_related('user')
        .order_by('-xp', 'created_at', 'id')
    )
    for index, row in enumerate(rows, start=1):
        row.rank = index
    return rows


def zone_of(rank, member_count) -> str:
    if rank <= PROMOTE_COUNT:
        return 'promotion'
    if member_count - rank < DEMOTE_COUNT:
        return 'demotion'
    return 'safe'


def my_league(user):
    start_date, _ = current_week()
    membership = (
        LeagueMembership.objects
        .select_related('league')
        .filter(user=user, league__period_start_date=start_date)
        .first()
    )
    if membership is None:
        return None, [], None

    rows = standings(membership.league)
    mine = next((row for row in rows if row.user_id == user.id), None)
    return membership.league, rows, mine


@transaction.atomic
def close_week(start_date):
    leagues = League.objects.filter(period_start_date=start_date, is_closed=False)
    closed = 0

    for league in leagues:
        rows = standings(league)
        member_count = len(rows)

        for row in rows:
            if row.rank <= PROMOTE_COUNT and league.tier < MAX_TIER:
                row.outcome = LeagueMembership.Outcome.PROMOTED
            elif (member_count - row.rank) < DEMOTE_COUNT and league.tier > MIN_TIER:
                row.outcome = LeagueMembership.Outcome.DEMOTED
            else:
                row.outcome = LeagueMembership.Outcome.STAYED

        if rows:
            LeagueMembership.objects.bulk_update(rows, ['rank', 'outcome'], batch_size=500)

        league.is_closed = True
        league.save(update_fields=['is_closed', 'updated_at'])
        closed += 1

        _notify(rows)

    if closed:
        logger.info('Ligalar yakunlandi: hafta=%s guruhlar=%s', start_date, closed)
    return closed


def _notify(rows):
    from notifications.models import NotificationLog

    logs = []
    for row in rows:
        if row.outcome == LeagueMembership.Outcome.PROMOTED:
            message = (
                f"Tabriklaymiz! Siz {row.league.get_tier_display()} ligasida "
                f"{row.rank}-o'rinni egallab, yuqori darajaga ko'tarildingiz 🎉"
            )
        elif row.outcome == LeagueMembership.Outcome.DEMOTED:
            message = (
                f"Bu hafta {row.league.get_tier_display()} ligasida "
                f"{row.rank}-o'rindasiz. Keyingi haftada yana urinib ko'ring 💪"
            )
        else:
            continue
        logs.append(NotificationLog(
            user_id=row.user_id,
            type=NotificationLog.Type.RATING_UP,
            message=message,
        ))

    if logs:
        NotificationLog.objects.bulk_create(logs)


def close_previous_week():
    from datetime import timedelta

    start_date, _ = current_week()
    return close_week(start_date - timedelta(days=7))
