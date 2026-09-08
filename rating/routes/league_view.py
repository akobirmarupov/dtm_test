from __future__ import annotations

from drf_spectacular.utils import extend_schema, inline_serializer
from rest_framework import serializers
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from common.throttles import BurstUserRateThrottle
from rating.leagues import (
    DEMOTE_COUNT,
    LEAGUE_SIZE,
    PROMOTE_COUNT,
    my_league,
    zone_of,
)
from rating.models import League
from rating.routes.serializers import LeagueStandingSerializer


class MyLeagueAPIView(APIView):
    permission_classes = [IsAuthenticated]
    throttle_classes = [BurstUserRateThrottle]

    @extend_schema(
        responses=inline_serializer(name='MyLeagueResponse', fields={
            'has_league': serializers.BooleanField(),
            'detail': serializers.CharField(required=False),
            'tier': serializers.IntegerField(required=False),
            'tier_name': serializers.CharField(required=False),
            'group_number': serializers.IntegerField(required=False),
            'period_start_date': serializers.DateField(required=False),
            'period_end_date': serializers.DateField(required=False),
            'league_size': serializers.IntegerField(),
            'promote_count': serializers.IntegerField(),
            'demote_count': serializers.IntegerField(),
            'my_rank': serializers.IntegerField(required=False, allow_null=True),
            'my_xp': serializers.IntegerField(required=False),
            'my_zone': serializers.CharField(required=False, allow_null=True),
            'standings': LeagueStandingSerializer(many=True),
        }),
        tags=['Rating'],
        description="Haftalik liga tartibi. `zone`: `promotion` (ko'tariladi), "
                    "`safe` (qoladi), `demotion` (tushadi).",
    )
    def get(self, request):
        league, rows, mine = my_league(request.user)

        if league is None:
            return Response({
                'has_league': False,
                'detail': "Bu hafta hali test ishlamadingiz. Birinchi testdan "
                          "keyin ligaga qo'shilasiz.",
                'league_size': LEAGUE_SIZE,
                'promote_count': PROMOTE_COUNT,
                'demote_count': DEMOTE_COUNT,
                'standings': [],
            })

        member_count = len(rows)
        payload = [
            {
                'rank': row.rank,
                'user_id': row.user_id,
                # Email ATAYIN yo'q: liga ro'yxati begonalarga ko'rinadi.
                'full_name': row.user.full_name or 'Anonim',
                'avatar_url': row.user.avatar_url or None,
                'xp': row.xp,
                'zone': zone_of(row.rank, member_count),
                'is_current_user': row.user_id == request.user.id,
            }
            for row in rows
        ]

        return Response({
            'has_league': True,
            'tier': league.tier,
            'tier_name': league.get_tier_display(),
            'group_number': league.group_number,
            'period_start_date': league.period_start_date,
            'period_end_date': league.period_end_date,
            'league_size': LEAGUE_SIZE,
            'promote_count': PROMOTE_COUNT,
            'demote_count': DEMOTE_COUNT,
            'my_rank': mine.rank if mine else None,
            'my_xp': mine.xp if mine else 0,
            'my_zone': zone_of(mine.rank, member_count) if mine else None,
            'standings': LeagueStandingSerializer(payload, many=True).data,
        })


class LeagueTiersAPIView(APIView):
    permission_classes = [IsAuthenticated]
    throttle_classes = [BurstUserRateThrottle]

    @extend_schema(
        responses=inline_serializer(name='LeagueTiersResponse', fields={
            'tiers': serializers.ListField(child=serializers.DictField()),
            'league_size': serializers.IntegerField(),
            'promote_count': serializers.IntegerField(),
            'demote_count': serializers.IntegerField(),
        }),
        tags=['Rating'],
    )
    def get(self, request):
        return Response({
            'tiers': [
                {'value': value, 'name': label}
                for value, label in League.Tier.choices
            ],
            'league_size': LEAGUE_SIZE,
            'promote_count': PROMOTE_COUNT,
            'demote_count': DEMOTE_COUNT,
        })


class MyLeagueHistoryAPIView(APIView):
    permission_classes = [IsAuthenticated]
    throttle_classes = [BurstUserRateThrottle]

    @extend_schema(
        responses=inline_serializer(name='LeagueHistoryResponse', fields={
            'results': serializers.ListField(child=serializers.DictField()),
        }),
        tags=['Rating'],
    )
    def get(self, request):
        from rating.models import LeagueMembership

        rows = (
            LeagueMembership.objects
            .filter(user=request.user, league__is_closed=True)
            .select_related('league')
            .order_by('-league__period_start_date')[:20]
        )
        return Response({
            'results': [
                {
                    'period_start_date': row.league.period_start_date,
                    'period_end_date': row.league.period_end_date,
                    'tier': row.league.tier,
                    'tier_name': row.league.get_tier_display(),
                    'rank': row.rank,
                    'xp': row.xp,
                    'outcome': row.outcome,
                    'outcome_display': row.get_outcome_display() if row.outcome else None,
                }
                for row in rows
            ]
        })
