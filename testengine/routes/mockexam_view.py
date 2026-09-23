"""DTM blok imtihoni — bir nechta fan ketma-ket, bitta umumiy taymer.

Javob berish uchun alohida endpoint kerak emas: imtihon ichidagi har bir fan
oddiy `TestSession`, shuning uchun mijoz mavjud
`/testengine/sessions/<id>/...` endpointlaridan foydalanadi. Bu yerda faqat
imtihonni ochish, holatini ko'rish va yakunlash bor.
"""

from __future__ import annotations

import logging

from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema, inline_serializer
from rest_framework import serializers, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from billing.entitlements import entitlements_for_request, history_cutoff
from common.i18n import resolve_language
from common.pagination import StandardResultsPagination
from common.permissions import HasFeature
from common.throttles import BurstUserRateThrottle
from testengine.models import MockExam
from testengine.routes.serializers import MockExamSerializer, MockExamStartSerializer
from testengine.services import (
    NotEnoughQuestionsForExam,
    create_mock_exam,
    ensure_exam_not_expired,
    finish_mock_exam,
)

logger = logging.getLogger('testengine.session')

CanTakeMockExam = HasFeature.named(
    'mock_exam', message="DTM blok imtihoni sizning tarifingizda mavjud emas."
)


def _error(name):
    return inline_serializer(name=name, fields={
        'detail': serializers.CharField(),
        'code': serializers.CharField(required=False),
    })


class MockExamBaseView(APIView):
    permission_classes = [IsAuthenticated]
    throttle_classes = [BurstUserRateThrottle]

    def context(self, request):
        return {'request': request, 'language': resolve_language(request)}

    def get_exam(self, request, pk) -> MockExam:
        exam = get_object_or_404(MockExam, pk=pk, user=request.user)
        ensure_exam_not_expired(exam)
        return exam


class MockExamListCreateAPIView(MockExamBaseView):
    def get_permissions(self):
        if self.request.method == 'POST':
            return [IsAuthenticated(), CanTakeMockExam()]
        return [IsAuthenticated()]

    @extend_schema(
        responses=MockExamSerializer(many=True),
        tags=['MockExam'],
        description="Foydalanuvchining blok imtihonlari. Tarifdagi «Natijalar "
                    "tarixi» chegarasi bu yerda ham amal qiladi.",
    )
    def get(self, request):
        queryset = MockExam.objects.filter(user=request.user).order_by('-created_at')

        cutoff = history_cutoff(entitlements_for_request(request))
        if cutoff is not None:
            queryset = queryset.filter(created_at__gte=cutoff)

        paginator = StandardResultsPagination()
        page = paginator.paginate_queryset(queryset, request, view=self)
        serializer = MockExamSerializer(page, many=True, context=self.context(request))
        return paginator.get_paginated_response(serializer.data)

    @extend_schema(
        request=MockExamStartSerializer,
        responses={
            201: MockExamSerializer,
            400: _error('MockExamStartError'),
            403: _error('MockExamUnavailable'),
        },
        tags=['MockExam'],
        description="Blok imtihonini boshlaydi: har bir fan uchun alohida "
                    "sessiya ochiladi, taymer esa hammasi uchun yagona.",
    )
    def post(self, request):
        serializer = MockExamStartSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        entitlements = entitlements_for_request(request)
        question_count = data['question_count']
        if question_count > entitlements.max_question_count:
            return Response(
                {
                    'detail': f"Sizning tarifingizda bir fanda ko'pi bilan "
                              f"{entitlements.max_question_count} ta savol bo'lishi mumkin.",
                    'code': 'question_count_exceeded',
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        open_exam = MockExam.objects.filter(
            user=request.user, finished_at__isnull=True
        ).first()
        if open_exam is not None and not ensure_exam_not_expired(open_exam):
            return Response(
                {
                    'detail': "Sizda tugallanmagan blok imtihoni bor. Avval uni "
                              "yakunlang.",
                    'code': 'exam_already_open',
                    'exam_id': open_exam.id,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            exam = create_mock_exam(
                user=request.user,
                subjects=data['subjects'],
                question_count=question_count,
            )
        except NotEnoughQuestionsForExam as error:
            return Response(
                {
                    'detail': f"«{error.subject}» fanida yetarli savol yo'q. "
                              f"Boshqa fan tanlang yoki savollar sonini kamaytiring.",
                    'code': 'not_enough_questions',
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(
            MockExamSerializer(exam, context=self.context(request)).data,
            status=status.HTTP_201_CREATED,
        )


class MockExamDetailAPIView(MockExamBaseView):
    @extend_schema(responses=MockExamSerializer, tags=['MockExam'])
    def get(self, request, pk):
        exam = self.get_exam(request, pk)
        return Response(
            MockExamSerializer(exam, context=self.context(request)).data
        )


class MockExamFinishAPIView(MockExamBaseView):
    @extend_schema(
        request=None,
        responses={200: MockExamSerializer},
        tags=['MockExam'],
        description="Imtihonni yakunlaydi: ochiq qolgan fanlar ham yopiladi "
                    "va umumiy natija hisoblanadi.",
    )
    def post(self, request, pk):
        exam = self.get_exam(request, pk)
        finish_mock_exam(exam)
        exam.refresh_from_db()

        logger.info(
            'Blok imtihoni qo\'lda yakunlandi: exam_id=%s user_id=%s',
            exam.id, request.user.id,
        )
        return Response(
            MockExamSerializer(exam, context=self.context(request)).data,
            status=status.HTTP_200_OK,
        )
