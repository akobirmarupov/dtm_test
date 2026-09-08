from __future__ import annotations

import logging

from django.db.models import Max
from drf_spectacular.utils import extend_schema, inline_serializer
from rest_framework import serializers, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from billing.entitlements import entitlements_for_request
from catalog.models import Question
from common.i18n import resolve_language
from common.pagination import StandardResultsPagination
from common.throttles import BurstUserRateThrottle
from testengine.models import MIN_QUESTION_COUNT, Answer, TestSession
from testengine.routes.serializers import (
    QuestionForTestSerializer,
    TestSessionDetailSerializer,
)
from testengine.services import create_session

logger = logging.getLogger('testengine.session')


MISTAKE_LIMIT = 500


def mistake_question_ids(user, subject_id=None, topic_id=None) -> list[int]:
    queryset = Answer.objects.filter(session__user=user)
    if subject_id:
        queryset = queryset.filter(question__topic__subject_id=subject_id)
    if topic_id:
        queryset = queryset.filter(question__topic_id=topic_id)

    latest = (
        queryset
        .values('question_id')
        .annotate(last_answer_id=Max('id'))
        .order_by()
    )
    latest_ids = [row['last_answer_id'] for row in latest]
    if not latest_ids:
        return []

    return list(
        Answer.objects
        .filter(id__in=latest_ids, is_correct=False)
        .order_by('-id')
        .values_list('question_id', flat=True)[:MISTAKE_LIMIT]
    )


class MistakeListAPIView(APIView):
    permission_classes = [IsAuthenticated]
    throttle_classes = [BurstUserRateThrottle]

    @extend_schema(
        responses=QuestionForTestSerializer(many=True),
        tags=['TestSession'],
        description="Oxirgi javobi NOTO'G'RI bo'lgan savollar. Keyinchalik "
                    "to'g'ri yechilgan savol ro'yxatdan avtomatik chiqadi.",
    )
    def get(self, request):
        question_ids = mistake_question_ids(
            request.user,
            subject_id=request.query_params.get('subject'),
            topic_id=request.query_params.get('topic'),
        )
        queryset = (
            Question.objects.available()
            .filter(id__in=question_ids)
            .select_related('topic', 'topic__subject')
        )

        paginator = StandardResultsPagination()
        page = paginator.paginate_queryset(queryset, request, view=self)
        serializer = QuestionForTestSerializer(
            page, many=True,
            context={'request': request, 'language': resolve_language(request)},
        )
        return paginator.get_paginated_response(serializer.data)


class MistakeStartTestAPIView(APIView):
    permission_classes = [IsAuthenticated]
    throttle_classes = [BurstUserRateThrottle]

    @extend_schema(
        request=inline_serializer(name='MistakeStartTestRequest', fields={
            'count': serializers.IntegerField(required=False),
            'subject': serializers.IntegerField(required=False),
            'topic': serializers.IntegerField(required=False),
        }),
        responses={
            201: TestSessionDetailSerializer,
            400: inline_serializer(name='MistakeStartTestError', fields={
                'detail': serializers.CharField(),
                'code': serializers.CharField(),
            }),
        },
        tags=['TestSession'],
    )
    def post(self, request):
        entitlements = entitlements_for_request(request)
        try:
            count = int(request.data.get('count') or 20)
        except (TypeError, ValueError):
            count = 20
        count = max(MIN_QUESTION_COUNT, min(count, entitlements.max_question_count))

        question_ids = mistake_question_ids(
            request.user,
            subject_id=request.data.get('subject'),
            topic_id=request.data.get('topic'),
        )
        questions = list(
            Question.objects.available()
            .filter(id__in=question_ids)
            .select_related('topic', 'topic__subject')[:count]
        )

        if not questions:
            return Response(
                {
                    'detail': "Xatolar bankingiz bo'sh. Avval test ishlang — "
                              "xato qilgan savollaringiz shu yerda to'planadi.",
                    'code': 'no_mistakes',
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        subject = questions[0].topic.subject
        session = TestSession.objects.create(
            user=request.user,
            subject=subject,
            mode=TestSession.Mode.PRACTICE,
            question_count=len(questions),
        )

        from testengine.models import SessionQuestion

        SessionQuestion.objects.bulk_create([
            SessionQuestion(session=session, question=question, order=order)
            for order, question in enumerate(questions, start=1)
        ])

        logger.info(
            'Xatolar ustida test: session_id=%s savollar=%s user_id=%s',
            session.id, len(questions), request.user.id,
        )
        return Response(
            TestSessionDetailSerializer(session, context={
                'request': request,
                'language': resolve_language(request),
                'answers': {},
            }).data,
            status=status.HTTP_201_CREATED,
        )
