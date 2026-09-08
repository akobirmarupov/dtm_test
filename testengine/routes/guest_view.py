from __future__ import annotations

import logging

from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema, inline_serializer
from rest_framework import serializers, status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from billing.entitlements import GUEST_QUESTION_COUNT
from catalog.models import Question, Topic
from common.i18n import resolve_language
from common.throttles import AnonBurstRateThrottle
from testengine.guest import GuestTokenError, build_guest_session, read_token, registration_prompt
from testengine.routes.serializers import (
    GuestQuestionSerializer,
    GuestResultSerializer,
    GuestStartSerializer,
    GuestSubmitSerializer,
)
from testengine.services import pick_questions

logger = logging.getLogger('testengine.session')


def _error(name):
    return inline_serializer(name=name, fields={
        'detail': serializers.CharField(),
        'code': serializers.CharField(required=False),
    })


class GuestStartTestAPIView(APIView):
    permission_classes = [AllowAny]
    throttle_classes = [AnonBurstRateThrottle]
    authentication_classes = []

    @extend_schema(
        request=GuestStartSerializer,
        responses={
            201: inline_serializer(name='GuestSessionResponse', fields={
                'token': serializers.CharField(),
                'question_count': serializers.IntegerField(),
                'questions': GuestQuestionSerializer(many=True),
                'topic': serializers.DictField(),
                'subject': serializers.DictField(),
                'is_guest': serializers.BooleanField(),
                'notice': serializers.CharField(),
            }),
            400: _error('GuestStartError'),
        },
        tags=['Guest'],
        description=f"Ro'yxatdan o'tmasdan test ishlash. Qat'iy "
                    f"{GUEST_QUESTION_COUNT} ta savol, natija ko'rsatilmaydi, "
                    f"hech narsa saqlanmaydi.",
    )
    def post(self, request):
        serializer = GuestStartSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        topic = serializer.validated_data['topic']

        if not topic.is_active or topic.available_question_count < GUEST_QUESTION_COUNT:
            return Response(
                {
                    "detail": f"Bu mavzuda hozircha yetarli savol yo'q "
                              f"(kamida {GUEST_QUESTION_COUNT} ta kerak).",
                    "code": "not_enough_questions",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        questions = pick_questions(
            subject=topic.subject, count=GUEST_QUESTION_COUNT,
            topic_ids=[topic.id], user=None, topic=topic,
        )
        if len(questions) < GUEST_QUESTION_COUNT:
            return Response(
                {
                    "detail": f"Bu mavzuda hozircha yetarli savol yo'q "
                              f"(kamida {GUEST_QUESTION_COUNT} ta kerak).",
                    "code": "not_enough_questions",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        payload = build_guest_session(questions, topic=topic, subject=topic.subject)
        context = {'request': request, 'language': resolve_language(request)}

        for order, question in enumerate(questions, start=1):
            question.order = order

        from testengine.routes.serializers import (
            SubjectMinimalSerializer,
            TopicMinimalSerializer,
        )

        logger.info('Guest testi boshlandi: topic_id=%s savollar=%s', topic.id, len(questions))
        return Response(
            {
                'token': payload['token'],
                'question_count': payload['question_count'],
                'questions': GuestQuestionSerializer(questions, many=True, context=context).data,
                'topic': TopicMinimalSerializer(topic, context=context).data,
                'subject': SubjectMinimalSerializer(topic.subject, context=context).data,
                'is_guest': True,
                'notice': (
                    "Natijani ko'rish uchun test yakunida ro'yxatdan o'tishingiz "
                    "kerak bo'ladi. Bu test saqlanmaydi."
                ),
            },
            status=status.HTTP_201_CREATED,
        )


class GuestSubmitTestAPIView(APIView):
    permission_classes = [AllowAny]
    throttle_classes = [AnonBurstRateThrottle]
    authentication_classes = []

    @extend_schema(
        request=GuestSubmitSerializer,
        responses={200: GuestResultSerializer, 400: _error('GuestSubmitError')},
        tags=['Guest'],
        description="Guest testini yakunlash. Natija ATAYIN qaytarilmaydi — "
                    "javobda ro'yxatdan o'tish taklifi keladi.",
    )
    def post(self, request):
        serializer = GuestSubmitSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        try:
            payload = read_token(data['token'])
        except GuestTokenError as error:
            return Response(
                {"detail": error.message, "code": error.code},
                status=status.HTTP_400_BAD_REQUEST,
            )

        allowed_ids = set(payload['q'])
        answers = data.get('answers') or []
        answered = {
            item['question'] for item in answers
            if item['question'] in allowed_ids and item.get('selected_option')
        }

        logger.info(
            'Guest testi yakunlandi: savollar=%s javoblar=%s',
            len(allowed_ids), len(answered),
        )
        return Response(
            registration_prompt(
                answered_count=len(answered),
                total_questions=len(allowed_ids),
            )
        )


class GuestTopicsAPIView(APIView):
    permission_classes = [AllowAny]
    throttle_classes = [AnonBurstRateThrottle]
    authentication_classes = []

    @extend_schema(
        responses={200: inline_serializer(name='GuestTopicsResponse', fields={
            'count': serializers.IntegerField(),
            'results': serializers.ListField(child=serializers.DictField()),
        })},
        tags=['Guest'],
        parameters=[],
    )
    def get(self, request):
        from common.pagination import StandardResultsPagination

        queryset = (
            Topic.objects
            .filter(is_active=True, available_question_count__gte=GUEST_QUESTION_COUNT)
            .select_related('subject', 'grade')
            .order_by('subject_id', 'grade__order', 'order', 'name')
        )
        subject_id = request.query_params.get('subject')
        if subject_id:
            queryset = queryset.filter(subject_id=subject_id)
        grade_id = request.query_params.get('grade')
        if grade_id:
            queryset = queryset.filter(grade_id=grade_id)

        language = resolve_language(request)
        paginator = StandardResultsPagination()
        page = paginator.paginate_queryset(queryset, request, view=self)

        from common.i18n import translated

        return paginator.get_paginated_response([
            {
                'id': topic.id,
                'name': translated(topic, 'name', language),
                'subject': {
                    'id': topic.subject_id,
                    'name': translated(topic.subject, 'name', language),
                },
                'grade': (
                    {'id': topic.grade_id, 'name': translated(topic.grade, 'name', language)}
                    if topic.grade_id else None
                ),
                'question_count': GUEST_QUESTION_COUNT,
            }
            for topic in page
        ])
