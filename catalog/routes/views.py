from __future__ import annotations

from rest_framework.parsers import JSONParser, MultiPartParser, FormParser
from rest_framework.filters import SearchFilter, OrderingFilter
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status

from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema

from django.db import IntegrityError, transaction
from django.core.cache import cache
import logging

from rest_framework.exceptions import NotFound

from catalog.filters import SubjectFilter, QuestionFilter, TopicFilter
from catalog.models import Subject, Question, Topic
from common.permissions import IsAdmin, IsMentor, IsMentorOrAdmin, IsOwner, IsStudent
from common.pagination import StandardResultsPagination
from common.throttles import BurstUserRateThrottle
from catalog.routes.serializers import SubjectSerializer, TopicSerializer, QuestionSerializer, QuestionWriteSerializer


subject_logger = logging.getLogger('subject')
topic_logger = logging.getLogger('topic')
question_logger = logging.getLogger('question')


class SubjectListCreateAPIView(APIView):
    throttle_classes = [BurstUserRateThrottle]

    def get_permissions(self):
        if self.request.method == "POST":
            return [IsAuthenticated(), IsMentorOrAdmin()]
        return [IsAuthenticated()]


    @extend_schema(responses=SubjectSerializer(many=True))
    def get(self, request):
        queryset = Subject.objects.all().order_by("name")
        queryset = SubjectFilter(request.query_params, queryset=queryset).qs

        paginator = StandardResultsPagination()
        page = paginator.paginate_queryset(queryset, request, view=self)
        serializer = SubjectSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)


    @extend_schema(request=SubjectSerializer, responses=SubjectSerializer)
    def post(self, request):
        serializer = SubjectSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            with transaction.atomic():
                subject = serializer.save()
        except IntegrityError:
            return Response(
                {"detail": "Bu nomdagi fan allaqachon mavjud."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        subject_logger.info(
            "Fan yaratildi: id=%s nomi=%r foydalanuvchi_id=%s",
            subject.id, subject.name, request.user.id,
        )
        return Response(SubjectSerializer(subject).data, status=status.HTTP_201_CREATED)


class SubjectDetailAPIView(APIView):
    throttle_classes = [BurstUserRateThrottle]

    def get_permissions(self):
        if self.request.method in ("GET", "HEAD", "OPTIONS"):
            return [IsAuthenticated()]
        return [IsAuthenticated(), IsMentorOrAdmin()]

    def get_object(self, pk):
        try:
            return Subject.objects.get(pk=pk)
        except (Subject.DoesNotExist, ValueError, TypeError):
            raise NotFound({"detail": "Bunday fan mavjud emas."})


    @extend_schema(responses=SubjectSerializer)
    def get(self, request, pk):
        subject = self.get_object(pk)
        return Response(SubjectSerializer(subject).data)


    @extend_schema(request=SubjectSerializer, responses=SubjectSerializer)
    def put(self, request, pk):
        return self._update(request, pk, partial=False)


    @extend_schema(request=SubjectSerializer, responses=SubjectSerializer)
    def patch(self, request, pk):
        return self._update(request, pk, partial=True)

    def _update(self, request, pk, *, partial):
        subject = self.get_object(pk)
        serializer = SubjectSerializer(subject, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)

        try:
            with transaction.atomic():
                serializer.save()
        except IntegrityError:
            return Response(
                {"detail": "Bu nomdagi fan allaqachon mavjud."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        subject_logger.info(
            "Fan tahrirlandi: id=%s nomi=%r foydalanuvchi_id=%s",
            subject.id, subject.name, request.user.id,
        )
        return Response(serializer.data)


    @extend_schema(responses={204: None})
    def delete(self, request, pk):
        subject = self.get_object(pk)

        if subject.topics.exists():
            return Response(
                {
                    "detail": (
                        "Bu fanga bog'liq mavzular mavjud. Fanni o'chirishdan oldin "
                        "unga tegishli barcha mavzularni o'chiring yoki boshqa fanga ko'chiring."
                    )
                },
                status=status.HTTP_409_CONFLICT,
            )

        subject_id = subject.id
        with transaction.atomic():
            subject.delete()

        subject_logger.warning(
            "Fan o'chirildi: id=%s foydalanuvchi_id=%s", subject_id, request.user.id,
        )
        return Response(status=status.HTTP_204_NO_CONTENT)




