from __future__ import annotations

from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from django.http import Http404

from drf_spectacular.utils import extend_schema

import logging

from testengine.filters import TestResultFilter
from testengine.models import TestResult
from testengine.routes.serializers import TestResultSerializer
from common.i18n import resolve_language
from common.pagination import StandardResultsPagination
from common.throttles import BurstUserRateThrottle


result_logger = logging.getLogger('testengine.result')


def serializer_context(request):
    return {'request': request, 'language': resolve_language(request)}


RESULT_SELECT_RELATED = ('session', 'session__subject', 'session__user')


class TestResultListAPIView(APIView):
    throttle_classes = [BurstUserRateThrottle]
    permission_classes = [IsAuthenticated]

    @extend_schema(responses=TestResultSerializer(many=True), tags=['TestResult'])
    def get(self, request):
        queryset = TestResult.objects.filter(
            session__user=request.user
        ).select_related(*RESULT_SELECT_RELATED).order_by('-created_at')

        queryset = TestResultFilter(request.query_params, queryset=queryset).qs

        paginator = StandardResultsPagination()
        page = paginator.paginate_queryset(queryset, request, view=self)
        serializer = TestResultSerializer(
            page, many=True, context=serializer_context(request)
        )

        return paginator.get_paginated_response(serializer.data)


class TestResultDetailAPIView(APIView):
    throttle_classes = [BurstUserRateThrottle]
    permission_classes = [IsAuthenticated]

    def get_object(self, pk, user):
        try:
            return TestResult.objects.select_related(*RESULT_SELECT_RELATED).get(
                id=pk, session__user=user
            )
        except TestResult.DoesNotExist:
            raise Http404("Natija topilmadi.")

    @extend_schema(responses=TestResultSerializer, tags=['TestResult'])
    def get(self, request, pk):
        """Bitta test natijasi tafsiloti."""
        result = self.get_object(pk, request.user)
        return Response(
            TestResultSerializer(result, context=serializer_context(request)).data
        )


class MyTestResultsAPIView(APIView):
    throttle_classes = [BurstUserRateThrottle]
    permission_classes = [IsAuthenticated]

    @extend_schema(responses=TestResultSerializer(many=True), tags=['TestResult'])
    def get(self, request):
        queryset = TestResult.objects.filter(
            session__user=request.user
        ).select_related(*RESULT_SELECT_RELATED).order_by('-created_at')

        queryset = TestResultFilter(request.query_params, queryset=queryset).qs

        paginator = StandardResultsPagination()
        page = paginator.paginate_queryset(queryset, request, view=self)
        serializer = TestResultSerializer(
            page, many=True, context=serializer_context(request)
        )

        result_logger.info(
            "Natijalar ro'yxati ko'rildi: user_id=%s", request.user.id
        )

        return paginator.get_paginated_response(serializer.data)
