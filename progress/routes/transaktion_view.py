# progress/routes/transaktion_view.py

import logging

from datetime import timedelta

from django.core.cache import cache
from django.db.models import Sum
from django.utils import timezone
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, extend_schema

from common.permissions import IsStudent
from common.pagination import StandardResultsPagination

from progress.models import XPTransaction
from progress.routes.serializers import (
    XPTransactionSerializer,
    XPSummarySerializer,
    LeaderboardEntrySerializer,
)
from progress.filters import XPTransactionFilter

logger = logging.getLogger(__name__)


SUMMARY_CACHE_TTL = 60 * 5
SUMMARY_CACHE_KEY = 'progress:xp:summary:user:{user_id}'

LEADERBOARD_CACHE_TTL = 60 * 15
LEADERBOARD_CACHE_KEY = 'progress:leaderboard:weekly'
LEADERBOARD_LIMIT = 50


# `XPTransactionFilter` qo'lda qo'llaniladi (bu oddiy APIView, `queryset` atributi yo'q),
# shuning uchun drf-spectacular filtrlarni o'zi topa olmaydi — quyida qo'lda beriladi.
XP_TRANSACTION_FILTER_PARAMETERS = [
    OpenApiParameter('user', OpenApiTypes.INT),
    OpenApiParameter('source', OpenApiTypes.STR, enum=XPTransaction.Source.values),
    OpenApiParameter('amount_min', OpenApiTypes.NUMBER),
    OpenApiParameter('amount_max', OpenApiTypes.NUMBER),
    OpenApiParameter('created_at', OpenApiTypes.DATE),
    OpenApiParameter('created_at_after', OpenApiTypes.DATE),
    OpenApiParameter('created_at_before', OpenApiTypes.DATE),
]


class XPTransactionListAPIView(APIView):
    permission_classes = [IsStudent]
    filter_backends = [DjangoFilterBackend]
    filterset_class = XPTransactionFilter
    pagination_class = StandardResultsPagination

    @extend_schema(
        parameters=XP_TRANSACTION_FILTER_PARAMETERS,
        filters=False,
        responses=XPTransactionSerializer(many=True),
    )
    def get(self, request):
        queryset = XPTransaction.objects.filter(
            user=request.user
        ).order_by('-created_at')
        queryset = XPTransactionFilter(request.GET, queryset=queryset).qs

        paginator = self.pagination_class()
        page = paginator.paginate_queryset(queryset, request, view=self)
        serializer = XPTransactionSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)


class XPSummaryAPIView(APIView):
    permission_classes = [IsStudent]

    @extend_schema(responses=XPSummarySerializer)
    def get(self, request):
        cache_key = SUMMARY_CACHE_KEY.format(user_id=request.user.id)
        cached_data = cache.get(cache_key)
        if cached_data is not None:
            logger.debug('XP summary: cache hit user_id=%s', request.user.id)
            return Response(cached_data, status=status.HTTP_200_OK)

        today = timezone.now().date()
        week_start = today - timedelta(days=today.weekday())  # dushanbadan boshlab

        qs = XPTransaction.objects.filter(user=request.user)

        xp_total = qs.aggregate(total=Sum('amount'))['total'] or 0
        xp_today = qs.filter(created_at__date=today).aggregate(
            total=Sum('amount')
        )['total'] or 0
        xp_this_week = qs.filter(created_at__date__gte=week_start).aggregate(
            total=Sum('amount')
        )['total'] or 0

        data = XPSummarySerializer({
            'xp_total': xp_total,
            'xp_today': xp_today,
            'xp_this_week': xp_this_week,
        }).data

        cache.set(cache_key, data, SUMMARY_CACHE_TTL)
        logger.debug('XP summary: cache miss, saqlandi user_id=%s', request.user.id)

        return Response(data, status=status.HTTP_200_OK)


class WeeklyLeaderboardAPIView(APIView):
    permission_classes = [IsStudent]

    @extend_schema(responses=LeaderboardEntrySerializer(many=True))
    def get(self, request):
        leaderboard = cache.get(LEADERBOARD_CACHE_KEY)

        if leaderboard is None:
            leaderboard = self._build_leaderboard()
            cache.set(LEADERBOARD_CACHE_KEY, leaderboard, LEADERBOARD_CACHE_TTL)
            logger.debug('Leaderboard: cache miss, qayta hisoblandi')
        else:
            logger.debug('Leaderboard: cache hit')

        result = []
        for entry in leaderboard:
            result.append({
                **entry,
                'is_current_user': entry['user_id'] == request.user.id,
            })

        serializer = LeaderboardEntrySerializer(result, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @staticmethod
    def _build_leaderboard():
        today = timezone.now().date()
        week_start = today - timedelta(days=today.weekday())

        rows = (
            XPTransaction.objects
            .filter(created_at__date__gte=week_start)
            .values('user_id', 'user__full_name')
            .annotate(xp_this_week=Sum('amount'))
            .order_by('-xp_this_week')[:LEADERBOARD_LIMIT]
        )

        leaderboard = []
        for rank, row in enumerate(rows, start=1):
            leaderboard.append({
                'rank': rank,
                'user_id': row['user_id'],
                'nickname': row['user__full_name'] or 'Anonim',
                'xp_this_week': row['xp_this_week'] or 0,
            })
        return leaderboard