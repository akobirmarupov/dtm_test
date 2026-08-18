import logging

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.generics import get_object_or_404
from drf_spectacular.utils import extend_schema

from common.permissions import IsStudent
from common.pagination import StandardResultsPagination

from rating.models import SubjectRating
from rating.routes.serializers import SubjectRatingSerializer

logger = logging.getLogger(__name__)


class SubjectRatingListAPIView(APIView):
    permission_classes = [IsStudent]
    pagination_class = StandardResultsPagination

    @extend_schema(responses=SubjectRatingSerializer(many=True))
    def get(self, request):
        queryset = (
            SubjectRating.objects.filter(user=request.user)
            .select_related('subject')
            .order_by('stars')
        )
        paginator = self.pagination_class()
        page = paginator.paginate_queryset(queryset, request, view=self)
        serializer = SubjectRatingSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)


class SubjectRatingDetailAPIView(APIView):
    permission_classes = [IsStudent]

    @extend_schema(responses=SubjectRatingSerializer)
    def get(self, request, subject_id):
        rating = get_object_or_404(
            SubjectRating.objects.select_related('subject'),
            user=request.user, subject_id=subject_id,
        )
        return Response(SubjectRatingSerializer(rating).data, status=status.HTTP_200_OK)
