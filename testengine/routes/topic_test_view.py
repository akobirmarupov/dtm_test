from __future__ import annotations

import logging

from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema, inline_serializer
from rest_framework import serializers, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from billing.entitlements import entitlements_for_request
from catalog.models import Topic
from common.i18n import resolve_language
from common.models import Role
from common.throttles import BurstUserRateThrottle
from testengine.access import (
    access_payload,
    limit_response_payload,
    register_topic_usage,
    tiers_for,
    topic_access,
)
from testengine.models import MIN_TIER, TestSession
from testengine.routes.serializers import (
    AvailableCountsSerializer,
    StartTopicTestSerializer,
    TestSessionDetailSerializer,
)
from testengine.services import create_session

logger = logging.getLogger('testengine.session')


def _error(name):
    return inline_serializer(name=name, fields={
        'detail': serializers.CharField(),
        'code': serializers.CharField(required=False),
    })


class TopicTestBaseView(APIView):
    throttle_classes = [BurstUserRateThrottle]
    permission_classes = [IsAuthenticated]

    def get_topic(self, pk):
        return get_object_or_404(
            Topic.objects.select_related('subject', 'grade'), pk=pk, is_active=True
        )

    def context(self, request):
        return {'request': request, 'language': resolve_language(request)}


class TopicAvailableCountsAPIView(TopicTestBaseView):
    @extend_schema(responses={200: AvailableCountsSerializer},tags=['TestSession'])
    def get(self, request, topic_id):
        topic = self.get_topic(topic_id)
        entitlements = entitlements_for_request(request)

        total = topic.available_question_count
        tiers = tiers_for(entitlements, total)
        access = topic_access(request.user, topic, entitlements)

        reason = None
        if not tiers:
            reason = (
                f"Bu mavzuda hozircha yetarli savol yo'q (kamida {MIN_TIER} ta "
                f"kerak). Tez orada qo'shiladi."
            )

        payload = {
            'topic': topic,
            'subject': topic.subject,
            'grade': topic.grade,
            'is_available': bool(tiers) and access['allowed'],
            'tiers': tiers,
            'min_required': MIN_TIER,
            'reason': reason,
            'access': access_payload(access),
            'entitlements': entitlements.as_dict(),
            # Faqat kontent bilan ishlaydiganlar uchun.
            'question_count': (
                total if getattr(request.user, 'role', None) in (Role.MENTOR, Role.ADMIN)
                else None
            ),
        }
        return Response(
            AvailableCountsSerializer(payload, context=self.context(request)).data
        )


class TopicStartTestAPIView(TopicTestBaseView):

    @extend_schema(request=StartTopicTestSerializer,
        responses={
            201: TestSessionDetailSerializer,
            400: _error('StartTestError'),
            403: _error('StartTestLimitReached'),
        },
        tags=['TestSession'],)
    def post(self, request, topic_id):
        topic = self.get_topic(topic_id)
        entitlements = entitlements_for_request(request)

        serializer = StartTopicTestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        tiers = tiers_for(entitlements, topic.available_question_count)
        if not tiers:
            return Response(
                {
                    "detail": f"Bu mavzuda hozircha yetarli savol yo'q "
                              f"(kamida {MIN_TIER} ta kerak).",
                    "code": "not_enough_questions",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        count = data.get('count') or tiers[0]
        if count not in tiers:
            return Response(
                {
                    "detail": f"Bu mavzu uchun {count} ta savol mavjud emas. "
                              f"Tanlash mumkin: {tiers}.",
                    "code": "invalid_count",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        access = topic_access(request.user, topic, entitlements)
        if not access['allowed']:
            logger.info(
                'Kunlik mavzu limiti: user_id=%s topic_id=%s used=%s limit=%s',
                request.user.id, topic.id, access['used'], access['limit'],
            )
            return Response(
                limit_response_payload(access), status=status.HTTP_403_FORBIDDEN
            )

        session = create_session(
            user=request.user,
            subject=topic.subject,
            mode=data['mode'],
            question_count=count,
            topic=topic,
        )
        if session is None:
            return Response(
                {
                    "detail": "Bu mavzu bo'yicha savollar topilmadi.",
                    "code": "not_enough_questions",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        register_topic_usage(request.user, topic)

        context = {
            'request': request,
            'language': resolve_language(request),
            'answers': {},
        }
        return Response(
            TestSessionDetailSerializer(session, context=context).data,
            status=status.HTTP_201_CREATED,
        )


class MyTestLimitsAPIView(APIView):
    throttle_classes = [BurstUserRateThrottle]
    permission_classes = [IsAuthenticated]

    @extend_schema(
        responses={200: inline_serializer(name='MyLimitsResponse', fields={
            'entitlements': serializers.DictField(),
            'daily_topic_limit': serializers.IntegerField(allow_null=True),
            'topics_used_today': serializers.IntegerField(),
            'topics_remaining_today': serializers.IntegerField(allow_null=True),
            'reset_at': serializers.DateTimeField(),
            'question_count_tiers': serializers.ListField(child=serializers.IntegerField()),
        })},
        tags=['TestSession'],
    )
    def get(self, request):
        from testengine.access import next_reset_at, topics_used_today
        from testengine.models import QUESTION_COUNT_TIERS

        entitlements = entitlements_for_request(request)
        used = topics_used_today(request.user)
        limit = entitlements.daily_topic_limit

        return Response({
            'entitlements': entitlements.as_dict(),
            'daily_topic_limit': limit,
            'topics_used_today': used,
            'topics_remaining_today': None if limit is None else max(limit - used, 0),
            'reset_at': next_reset_at(),
            'question_count_tiers': [
                tier for tier in QUESTION_COUNT_TIERS
                if tier <= entitlements.max_question_count
            ],
        })
