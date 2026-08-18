import logging

from django.core.cache import cache
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from drf_spectacular.utils import extend_schema

from rating.models import Rating
from rating.services import get_period_dates
from rating.routes.serializers import LeaderboardEntrySerializer

logger = logging.getLogger(__name__)

LEADERBOARD_CACHE_TTL = 60 * 15
LEADERBOARD_CACHE_KEY = 'rating:leaderboard:{period}'
LEADERBOARD_LIMIT = 50

VALID_PERIODS = ('daily', 'weekly', 'all_time')


class LeaderboardListAPIView(APIView):
    """
    GET /rating/leaderboard/{period}/

    Leaderboard modeli hech narsa tomonidan to'ldirilmagani uchun,
    reyting Rating jadvalidan (u har test yakunida avtomatik yangilanadi) hisoblanadi.
    """
    permission_classes = [IsAuthenticated]

    @extend_schema(responses=LeaderboardEntrySerializer(many=True))
    def get(self, request, period):
        if period not in VALID_PERIODS:
            return Response(
                {'detail': "period 'daily', 'weekly' yoki 'all_time' bo'lishi kerak."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        cache_key = LEADERBOARD_CACHE_KEY.format(period=period)
        leaderboard = cache.get(cache_key)

        if leaderboard is None:
            leaderboard = self._build_leaderboard(period)
            cache.set(cache_key, leaderboard, LEADERBOARD_CACHE_TTL)
            logger.debug('Leaderboard: cache miss, qayta hisoblandi period=%s', period)
        else:
            logger.debug('Leaderboard: cache hit period=%s', period)

        result = [
            {**entry, 'is_current_user': entry['user_id'] == request.user.id}
            for entry in leaderboard
        ]

        serializer = LeaderboardEntrySerializer(result, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @staticmethod
    def _build_leaderboard(period):
        start_date, end_date = get_period_dates(period)
        rows = (
            Rating.objects
            .filter(period=period, period_start_date=start_date, period_end_date=end_date)
            .exclude(rank=None)
            .select_related('user')
            .order_by('rank')[:LEADERBOARD_LIMIT]
        )

        leaderboard = []
        for row in rows:
            leaderboard.append({
                'rank': row.rank,
                'user_id': row.user_id,
                'full_name': row.user.full_name or row.user.email,
                'stars': row.stars,
                'tests_completed': row.tests_completed,
            })
        return leaderboard
