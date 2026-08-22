import logging

from django.core.cache import cache
from django.utils import timezone
from rest_framework import serializers
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from drf_spectacular.utils import extend_schema, inline_serializer

from common.permissions import IsStudent
from common.throttles import BurstUserRateThrottle, SustainedUserRateThrottle

from progress.models import Streak
from progress.routes.serializers import StreakSerializer
from progress.services import use_streak_freeze

logger = logging.getLogger(__name__)


STREAK_CACHE_TTL = 60 * 5
STREAK_CACHE_KEY = 'progress:streak:user:{user_id}'


class StreakDetailAPIView(APIView):
    permission_classes = [IsStudent]

    @extend_schema(responses=StreakSerializer)
    def get(self, request):
        cache_key = STREAK_CACHE_KEY.format(user_id=request.user.id)
        cached_data = cache.get(cache_key)
        if cached_data is not None:
            logger.debug('Streak: cache hit user_id=%s', request.user.id)
            return Response(cached_data, status=status.HTTP_200_OK)

        streak, created = Streak.objects.get_or_create(user=request.user)
        if created:
            logger.info('Streak: yangi yozuv yaratildi user_id=%s', request.user.id)

        data = StreakSerializer(streak).data
        cache.set(cache_key, data, STREAK_CACHE_TTL)
        logger.debug('Streak: cache miss, saqlandi user_id=%s', request.user.id)

        return Response(data, status=status.HTTP_200_OK)


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

        if streak.freezes_available <= 0:
            logger.info(
                'Streak freeze: rad etildi (freeze yo\'q) user_id=%s',
                request.user.id,
            )
            return Response(
                {'detail': "Sizda ishlatish uchun 'muz' qolmagan."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        updated_streak = use_streak_freeze(streak)

        cache.delete(STREAK_CACHE_KEY.format(user_id=request.user.id))

        logger.info(
            'Streak freeze ishlatildi: user_id=%s qolgan=%s',
            request.user.id, updated_streak.freezes_available,
        )

        return Response(
            StreakSerializer(updated_streak).data,
            status=status.HTTP_200_OK,
        )