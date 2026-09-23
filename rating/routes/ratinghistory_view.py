import logging

from rest_framework.views import APIView
from drf_spectacular.utils import extend_schema

from billing.entitlements import entitlements_for_request, history_cutoff
from common.permissions import CanViewAnalytics, IsStudent
from common.pagination import StandardResultsPagination

from rating.models import RatingHistory
from rating.routes.serializers import RatingHistorySerializer

logger = logging.getLogger(__name__)


class RatingHistoryListAPIView(APIView):
    permission_classes = [IsStudent, CanViewAnalytics]
    pagination_class = StandardResultsPagination

    @extend_schema(responses=RatingHistorySerializer(many=True))
    def get(self, request):
        queryset = RatingHistory.objects.filter(user=request.user).order_by('-created_at')

        # Tarifdagi «Natijalar tarixi (kun)» shu yerda ham amal qiladi.
        cutoff = history_cutoff(entitlements_for_request(request))
        if cutoff is not None:
            queryset = queryset.filter(created_at__gte=cutoff)

        period = request.query_params.get('period')
        if period:
            queryset = queryset.filter(period=period)

        paginator = self.pagination_class()
        page = paginator.paginate_queryset(queryset, request, view=self)
        serializer = RatingHistorySerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)
