import logging

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.generics import get_object_or_404
from drf_spectacular.utils import extend_schema

from common.permissions import IsStudent
from common.pagination import StandardResultsPagination

from rating.models import TopicRating
from rating.routes.serializers import TopicRatingSerializer

logger = logging.getLogger(__name__)


class TopicRatingListAPIView(APIView):
    permission_classes = [IsStudent]
    pagination_class = StandardResultsPagination

    @extend_schema(responses=TopicRatingSerializer(many=True))
    def get(self, request):
        queryset = (
            TopicRating.objects.filter(user=request.user)
            .select_related('topic', 'topic__subject')
            .order_by('stars')
        )
        paginator = self.pagination_class()
        page = paginator.paginate_queryset(queryset, request, view=self)
        serializer = TopicRatingSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)


class TopicRatingDetailAPIView(APIView):
    permission_classes = [IsStudent]

    @extend_schema(responses=TopicRatingSerializer)
    def get(self, request, topic_id):
        rating = get_object_or_404(
            TopicRating.objects.select_related('topic', 'topic__subject'),
            user=request.user, topic_id=topic_id,
        )
        return Response(TopicRatingSerializer(rating).data, status=status.HTTP_200_OK)
