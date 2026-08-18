import logging

from rest_framework.views import APIView
from drf_spectacular.utils import extend_schema

from common.permissions import IsStudent
from common.pagination import StandardResultsPagination

from rating.models import RatingHistory
from rating.routes.serializers import RatingHistorySerializer

logger = logging.getLogger(__name__)


class RatingHistoryListAPIView(APIView):
    permission_classes = [IsStudent]
    pagination_class = StandardResultsPagination

    @extend_schema(responses=RatingHistorySerializer(many=True))
    def get(self, request):
        queryset = RatingHistory.objects.filter(user=request.user).order_by('-created_at')

        period = request.query_params.get('period')
        if period:
            queryset = queryset.filter(period=period)

        paginator = self.pagination_class()
        page = paginator.paginate_queryset(queryset, request, view=self)
        serializer = RatingHistorySerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)
