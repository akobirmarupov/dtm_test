import logging

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.generics import get_object_or_404
from drf_spectacular.utils import extend_schema

from common.permissions import IsAdmin
from common.pagination import StandardResultsPagination

from dashboard.models import AnalyticsSummary
from dashboard.routes.serializers import AnalyticsSummarySerializer

logger = logging.getLogger(__name__)


class AnalyticsSummaryListAPIView(APIView):
    permission_classes = [IsAdmin]
    pagination_class = StandardResultsPagination

    @extend_schema(responses=AnalyticsSummarySerializer(many=True))
    def get(self, request):
        queryset = AnalyticsSummary.objects.all().order_by('-date')

        timeframe = request.query_params.get('timeframe')
        if timeframe:
            queryset = queryset.filter(timeframe=timeframe)

        paginator = self.pagination_class()
        page = paginator.paginate_queryset(queryset, request, view=self)
        serializer = AnalyticsSummarySerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)


class AnalyticsSummaryDetailAPIView(APIView):
    permission_classes = [IsAdmin]

    @extend_schema(responses=AnalyticsSummarySerializer)
    def get(self, request, pk):
        summary = get_object_or_404(AnalyticsSummary, pk=pk)
        return Response(AnalyticsSummarySerializer(summary).data, status=status.HTTP_200_OK)
