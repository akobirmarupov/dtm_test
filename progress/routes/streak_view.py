import logging

from django.core.cache import cache
from django.utils import timezone
from rest_framework import serializers
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from drf_spectacular.utils import extend_schema, inline_serializer

from billing.entitlements import entitlements_for_request
from common.models import DailyFeatureUsage
from common.permissions import IsStudent
from common.throttles import BurstUserRateThrottle, SustainedUserRateThrottle
from common.usage import consume_if_limited, used_this_month

from progress.models import Streak
from progress.routes.serializers import StreakSerializer
from progress.services import use_streak_freeze

logger = logging.getLogger(__name__)


STREAK_CACHE_TTL = 60 * 5
STREAK_CACHE_KEY = 'progress:streak:user:{user_id}'

FREEZE = DailyFeatureUsage.Feature.STREAK_FREEZE


def freeze_quota(request) -> dict:
    """«Muz» bo'yicha OYLIK holat.

    Kunlik emas, oylik hisoblanadi: kun o'tkazib yuborish kamdan-kam bo'ladi,
    kunlik limit bu yerda ma'no bermaydi.
    """
    limit = entitlements_for_request(request).streak_freezes_per_month
    used = 0 if limit is None else used_this_month(request.user, FREEZE)

    return {
        'limit': limit,
        'used': used,
        'remaining': None if limit is None else max(limit - used, 0),
        'allowed': limit is None or used < limit,
    }


class StreakDetailAPIView(APIView):
    permission_classes = [IsStudent]

    def with_quota(self, request, data) -> dict:
        """Kesh ichidagi ma'lumotga oylik «muz» holatini qo'shadi.

        Limit keshlanmaydi — u oy davomida o'zgaradi va tarif ham
        almashishi mumkin.
        """
        quota = freeze_quota(request)
        return {
            **data,
            'freezes_limit_per_month': quota['limit'],
            'freezes_used_this_month': quota['used'],
            'freezes_remaining': quota['remaining'],
        }

    @extend_schema(responses=StreakSerializer)
    def get(self, request):
        cache_key = STREAK_CACHE_KEY.format(user_id=request.user.id)
        cached_data = cache.get(cache_key)
        if cached_data is not None:
            logger.debug('Streak: cache hit user_id=%s', request.user.id)
            return Response(
                self.with_quota(request, cached_data), status=status.HTTP_200_OK
            )

        streak, created = Streak.objects.get_or_create(user=request.user)
        if created:
            logger.info('Streak: yangi yozuv yaratildi user_id=%s', request.user.id)

        data = StreakSerializer(streak).data
        cache.set(cache_key, data, STREAK_CACHE_TTL)
        logger.debug('Streak: cache miss, saqlandi user_id=%s', request.user.id)

        return Response(self.with_quota(request, data), status=status.HTTP_200_OK)


class StreakFreezeAPIView(APIView):
    permission_classes = [IsStudent]
    throttle_classes = [BurstUserRateThrottle, SustainedUserRateThrottle]

    @extend_schema(
        request=None,
        responses={
            200: StreakSerializer,
            400: inline_serializer(
                name='StreakFreezeErrorResponse',
                fields={'detail': serializers.CharField()},
            ),
        },
    )
    def post(self, request):
        streak, _ = Streak.objects.get_or_create(user=request.user)
        quota = freeze_quota(request)

        if quota['limit'] == 0:
            return Response(
                {
                    'detail': "«Muz» sizning tarifingizda mavjud emas.",
                    'code': 'upgrade_required',
                    'upgrade_required': True,
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        if not quota['allowed']:
            logger.info(
                'Streak freeze: oylik limit tugadi user_id=%s limit=%s',
                request.user.id, quota['limit'],
            )
            return Response(
                {
                    'detail': f"Bu oyda {quota['limit']} ta «muz» ishlatdingiz — "
                              f"limitingiz shuncha. Keyingi oy yangilanadi.",
                    'code': 'streak_freeze_limit_reached',
                    'limit': quota['limit'],
                    'used_this_month': quota['used'],
                    'remaining': 0,
                    'upgrade_required': True,
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        consume_if_limited(request.user, FREEZE, quota['limit'])
        remaining = None if quota['remaining'] is None else quota['remaining'] - 1
        updated_streak = use_streak_freeze(streak, remaining=remaining)

        cache.delete(STREAK_CACHE_KEY.format(user_id=request.user.id))

        logger.info(
            'Streak freeze ishlatildi: user_id=%s qolgan=%s',
            request.user.id, remaining,
        )

        return Response(
            {
                **StreakSerializer(updated_streak).data,
                'freezes_limit_per_month': quota['limit'],
                'freezes_used_this_month': quota['used'] + 1,
                'freezes_remaining': remaining,
            },
            status=status.HTTP_200_OK,
        )