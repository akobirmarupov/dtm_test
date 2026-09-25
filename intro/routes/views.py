"""Kirish testi endpointlari.

Oqim shunday: odam ilovani ochadi -> 4 ta tasodifiy savol oladi -> javob
beradi -> natijani ko'radi va ro'yxatdan o'tish taklifini oladi.

Test ATAYIN ro'yxatdan o'tmagan odamga mo'ljallangan: kirgan foydalanuvchiga
u ko'rsatilmaydi, chunki uning vazifasi — qiziqtirib, ro'yxatdan o'tkazish.
"""

from __future__ import annotations

import logging

from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema, inline_serializer
from rest_framework import serializers, status
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from common.i18n import resolve_language, translated
from common.pagination import StandardResultsPagination
from common.permissions import IsAdmin
from common.throttles import AnonBurstRateThrottle, BurstUserRateThrottle
from intro.models import INTRO_QUESTION_COUNT, IntroQuestion
from intro.routes.serializers import (
    IntroQuestionAdminSerializer,
    IntroQuestionSerializer,
    IntroSubmitSerializer,
)
from intro.tokens import IntroTokenError, issue_token, read_token

logger = logging.getLogger('intro')


def _error(name):
    return inline_serializer(name=name, fields={
        'detail': serializers.CharField(),
        'code': serializers.CharField(required=False),
    })


class GuestOnlyMixin:
    """Ro'yxatdan o'tgan foydalanuvchiga kirish testi ko'rsatilmaydi."""

    def reject_authenticated(self, request):
        if getattr(request.user, 'is_authenticated', False):
            return Response(
                {
                    'detail': "Kirish testi faqat ro'yxatdan o'tmagan "
                              "foydalanuvchilar uchun.",
                    'code': 'already_registered',
                },
                status=status.HTTP_403_FORBIDDEN,
            )
        return None


class IntroStartAPIView(GuestOnlyMixin, APIView):
    permission_classes = [AllowAny]
    throttle_classes = [AnonBurstRateThrottle]

    @extend_schema(
        responses={
            200: inline_serializer(name='IntroStartResponse', fields={
                'token': serializers.CharField(),
                'question_count': serializers.IntegerField(),
                'questions': IntroQuestionSerializer(many=True),
            }),
            403: _error('IntroAlreadyRegistered'),
            503: _error('IntroNotReady'),
        },
        tags=['Intro'],
        description=f"Tasodifiy {INTRO_QUESTION_COUNT} ta savol. Bazada nechta "
                    f"savol bo'lishidan qat'i nazar har safar boshqacha "
                    f"to'plam chiqadi.",
    )
    def get(self, request):
        questions = list(
            IntroQuestion.objects.filter(is_active=True).order_by('?')[:INTRO_QUESTION_COUNT]
        )
        if len(questions) < INTRO_QUESTION_COUNT:
            return Response(
                {
                    'detail': "Kirish testi hozircha tayyor emas.",
                    'code': 'not_enough_questions',
                },
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        context = {'request': request, 'language': resolve_language(request)}
        logger.info('Kirish testi boshlandi: savollar=%s', len(questions))

        return Response({
            'token': issue_token([question.id for question in questions]),
            'question_count': len(questions),
            'questions': IntroQuestionSerializer(questions, many=True, context=context).data,
        })


class IntroSubmitAPIView(GuestOnlyMixin, APIView):
    permission_classes = [AllowAny]
    throttle_classes = [AnonBurstRateThrottle]

    @extend_schema(
        request=IntroSubmitSerializer,
        responses={200: inline_serializer(name='IntroResultResponse', fields={
            'question_count': serializers.IntegerField(),
            'answered_count': serializers.IntegerField(),
            'correct_count': serializers.IntegerField(),
            'scored_count': serializers.IntegerField(),
            'results': serializers.ListField(child=serializers.DictField()),
            'message': serializers.CharField(),
            'registration_required': serializers.BooleanField(),
        }), 400: _error('IntroSubmitError'), 403: _error('IntroSubmitForbidden')},
        tags=['Intro'],
        description="Javoblarni yuboradi va natijani qaytaradi: qaysi savolga "
                    "to'g'ri javob berilgani, izohlar va ro'yxatdan o'tish taklifi.",
    )
    def post(self, request):
        serializer = IntroSubmitSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        try:
            payload = read_token(data['token'])
        except IntroTokenError as error:
            return Response(
                {'detail': error.message, 'code': error.code},
                status=status.HTTP_400_BAD_REQUEST,
            )

        allowed_ids = list(payload['q'])
        chosen = {
            item['question']: (item.get('selected_option') or '').strip()
            for item in data['answers']
            if item['question'] in allowed_ids
        }

        language = resolve_language(request)
        questions = {
            question.id: question
            for question in IntroQuestion.objects.filter(id__in=allowed_ids)
        }

        results, correct_count, scored_count, answered = [], 0, 0, 0
        for question_id in allowed_ids:
            question = questions.get(question_id)
            if question is None:
                continue

            selected = chosen.get(question_id, '')
            is_correct = None
            if selected:
                answered += 1
            if question.has_correct_answer:
                scored_count += 1
                is_correct = bool(selected) and selected == question.correct_option
                correct_count += int(is_correct)

            results.append({
                'question': question_id,
                'kind': question.kind,
                'selected_option': selected or None,
                'correct_option': question.correct_option or None,
                'is_correct': is_correct,
                'explanation': translated(question, 'explanation', language),
            })

        logger.info(
            'Kirish testi yakunlandi: javoblar=%s togri=%s', answered, correct_count
        )

        return Response({
            'question_count': len(results),
            'answered_count': answered,
            'correct_count': correct_count,
            'scored_count': scored_count,
            'results': results,
            'message': (
                "Yaxshi boshladingiz! Ro'yxatdan o'tsangiz, DTM fanlari bo'yicha "
                "haqiqiy testlarni ishlab, natijangizni kuzatib borasiz."
            ),
            'registration_required': True,
        })


# ---------------------------------------------------------------------------
# Admin: savollarni boshqarish
# ---------------------------------------------------------------------------
class IntroQuestionAdminListCreateAPIView(APIView):
    """Admin panel uchun: ro'yxat va yangi savol (rasm/video bilan)."""

    permission_classes = [IsAdmin]
    throttle_classes = [BurstUserRateThrottle]
    parser_classes = [JSONParser, MultiPartParser, FormParser]
    pagination_class = StandardResultsPagination

    @extend_schema(responses=IntroQuestionAdminSerializer(many=True), tags=['Intro admin'])
    def get(self, request):
        queryset = IntroQuestion.objects.all().order_by('order', 'id')

        kind = request.query_params.get('kind')
        if kind:
            queryset = queryset.filter(kind=kind)
        is_active = request.query_params.get('is_active')
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() in ('1', 'true', 'ha'))

        paginator = self.pagination_class()
        page = paginator.paginate_queryset(queryset, request, view=self)
        return paginator.get_paginated_response(
            IntroQuestionAdminSerializer(page, many=True).data
        )

    @extend_schema(
        request=IntroQuestionAdminSerializer,
        responses={201: IntroQuestionAdminSerializer},
        tags=['Intro admin'],
    )
    def post(self, request):
        serializer = IntroQuestionAdminSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        question = serializer.save()

        logger.info(
            'Kirish testi savoli qo\'shildi: id=%s admin=%s', question.id, request.user.id
        )
        return Response(
            IntroQuestionAdminSerializer(question).data, status=status.HTTP_201_CREATED
        )


class IntroQuestionAdminDetailAPIView(APIView):
    permission_classes = [IsAdmin]
    throttle_classes = [BurstUserRateThrottle]
    parser_classes = [JSONParser, MultiPartParser, FormParser]

    def get_object(self, pk):
        return get_object_or_404(IntroQuestion, pk=pk)

    @extend_schema(responses=IntroQuestionAdminSerializer, tags=['Intro admin'])
    def get(self, request, pk):
        return Response(IntroQuestionAdminSerializer(self.get_object(pk)).data)

    @extend_schema(
        request=IntroQuestionAdminSerializer,
        responses=IntroQuestionAdminSerializer,
        tags=['Intro admin'],
    )
    def patch(self, request, pk):
        question = self.get_object(pk)
        serializer = IntroQuestionAdminSerializer(question, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        question = serializer.save()

        logger.info(
            'Kirish testi savoli yangilandi: id=%s admin=%s', question.id, request.user.id
        )
        return Response(IntroQuestionAdminSerializer(question).data)

    @extend_schema(responses={204: None}, tags=['Intro admin'])
    def delete(self, request, pk):
        question = self.get_object(pk)
        question.delete()

        logger.info('Kirish testi savoli o\'chirildi: id=%s admin=%s', pk, request.user.id)
        return Response(status=status.HTTP_204_NO_CONTENT)
