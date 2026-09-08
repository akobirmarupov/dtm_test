import logging

from django.core.cache import cache
from drf_spectacular.utils import extend_schema, inline_serializer
from rest_framework import serializers, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from common.throttles import BurstUserRateThrottle
from rating.routes.serializers import LeaderboardEntrySerializer
from rating.services import get_period_dates, leaderboard_rows, user_rank

logger = logging.getLogger('rating')

LEADERBOARD_CACHE_TTL = 60 * 5
LEADERBOARD_CACHE_KEY = 'rating:leaderboard:{period}'
LEADERBOARD_LIMIT = 50

VALID_PERIODS = ('daily', 'weekly', 'all_time')


class LeaderboardListAPIView(APIView):
    permission_classes = [IsAuthenticated]
    throttle_classes = [BurstUserRateThrottle]

    @extend_schema(
        responses={
            200: inline_serializer(name='LeaderboardResponse', fields={
                'period': serializers.CharField(),
                'period_start_date': serializers.DateField(),
                'period_end_date': serializers.DateField(),
                'results': LeaderboardEntrySerializer(many=True),
                'my_position': inline_serializer(name='LeaderboardMyPosition', fields={
                    'rank': serializers.IntegerField(allow_null=True),
                    'total_participants': serializers.IntegerField(),
                    'in_top': serializers.BooleanField(),
                }),
            }),
            400: inline_serializer(
                name='LeaderboardPeriodError',
                fields={'detail': serializers.CharField()},
            ),
        },
        tags=['Rating'],
    )
    def get(self, request, period):
        if period not in VALID_PERIODS:
            return Response(
                {'detail': "period 'daily', 'weekly' yoki 'all_time' bo'lishi kerak."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        cache_key = LEADERBOARD_CACHE_KEY.format(period=period)
        entries = cache.get(cache_key)

        if entries is None:
            entries = [
                {
                    'rank': row.rank,
                    'user_id': row.user_id,
                    'full_name': row.user.full_name or 'Anonim',
                    'avatar_url': row.user.avatar_url or None,
                    'xp': row.xp,
                    'stars': row.stars,
                    'tests_completed': row.tests_completed,
                }
                for row in leaderboard_rows(period, LEADERBOARD_LIMIT)
            ]
            cache.set(cache_key, entries, LEADERBOARD_CACHE_TTL)

        results = [
            {**entry, 'is_current_user': entry['user_id'] == request.user.id}
            for entry in entries
        ]

        my_rank, total = user_rank(request.user, period)
        start_date, end_date = get_period_dates(period)

        return Response({
            'period': period,
            'period_start_date': start_date,
            'period_end_date': end_date,
            'results': LeaderboardEntrySerializer(results, many=True).data,
            'my_position': {
                'rank': my_rank,
                'total_participants': total or 0,
                'in_top': bool(my_rank and my_rank <= LEADERBOARD_LIMIT),
            },
        })
