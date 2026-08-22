"""Javoblar endpointi (savol ID si bo'yicha).

Tartib raqami bo'yicha ishlash qulayroq (`/questions/<order>/answer/`),
lekin mavjud mijozlar savol ID si bilan ishlaydi — bu endpoint o'shalar
uchun saqlangan va bir xil qoidalarga bo'ysunadi:

* sessiya yakunlanmaguncha javobni xohlagancha o'zgartirish mumkin;
* javob to'g'ri yoki noto'g'riligi YAKUNLASHGACHA qaytarilmaydi;
* yakunlangandan keyin hech narsa o'zgarmaydi.
"""

from __future__ import annotations

import logging

from django.db import transaction
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema, inline_serializer
from rest_framework import serializers, status
from rest_framework.exceptions import NotFound
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from common.i18n import resolve_language
from common.pagination import StandardResultsPagination
from common.throttles import BurstUserRateThrottle
from testengine.filters import AnswerFilter
from testengine.models import Answer, TestSession
from testengine.routes.serializers import (
    AnswerCreateSerializer,
    AnswerResultSerializer,
    AnswerSerializer,
    BulkAnswerSerializer,
)
from testengine.services import authorize_questions, save_answer

answer_logger = logging.getLogger('testengine.answer')


def detail_serializer(name):
    return inline_serializer(name=name, fields={'detail': serializers.CharField()})


def answer_serializer_class(session):
    """Sessiya yakunlangan bo'lsagina to'g'ri javob ko'rinadi."""
    return AnswerResultSerializer if session.is_finished else AnswerSerializer


class AnswerBaseView(APIView):
    throttle_classes = [BurstUserRateThrottle]
    permission_classes = [IsAuthenticated]

    def get_session(self, request, session_id):
        return get_object_or_404(
            TestSession.objects.select_related('subject'),
            id=session_id, user=request.user,
        )

    def context(self, request):
        return {'request': request, 'language': resolve_language(request)}

    def finished_response(self, message):
        return Response({"detail": message}, status=status.HTTP_400_BAD_REQUEST)


class AnswerListCreateAPIView(AnswerBaseView):
    @extend_schema(responses=AnswerSerializer(many=True), tags=['Answer'])
    def get(self, request, session_id):
        session = self.get_session(request, session_id)

        queryset = session.answers.select_related('question').order_by('id')

        # `is_correct` bo'yicha filtrlash sessiya yakunlanmaguncha javobni
        # oshkor qiladi ("is_correct=true bo'lganlari nechta?") — shuning
        # uchun test davomida bu parametr e'tiborga olinmaydi.
        params = request.query_params.copy()
        if not session.is_finished:
            params.pop('is_correct', None)
        queryset = AnswerFilter(params, queryset=queryset).qs

        paginator = StandardResultsPagination()
        page = paginator.paginate_queryset(queryset, request, view=self)
        serializer = answer_serializer_class(session)(
            page, many=True, context=self.context(request)
        )
        return paginator.get_paginated_response(serializer.data)

    @extend_schema(
        request=AnswerCreateSerializer,
        responses={
            200: AnswerSerializer,
            201: AnswerSerializer,
            400: detail_serializer('AnswerCreateError'),
        },
        tags=['Answer'],
        description="Javob berish yoki mavjud javobni o'zgartirish. Javob "
                    "to'g'ri chiqqani javobda KO'RSATILMAYDI.",
    )
    def post(self, request, session_id):
        session = self.get_session(request, session_id)

        if session.is_finished:
            return self.finished_response(
                "Tugagan sessiyaga javob qo'shish yoki o'zgartirish mumkin emas."
            )

        serializer = AnswerCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        question = data['question']

        missing = authorize_questions(session, [question.id])
        if missing:
            return Response(
                {"detail": "Savol bu sessiyaga tegishli emas."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        with transaction.atomic():
            answer, created = save_answer(
                session=session,
                question=question,
                selected_option=data['selected_option'],
                confidence=data.get('confidence', ''),
                time_spent_seconds=data.get('time_spent_seconds', 0),
            )

        answer_logger.info(
            "Javob %s: id=%s session_id=%s question_id=%s user_id=%s",
            "yaratildi" if created else "yangilandi",
            answer.id, session.id, answer.question_id, request.user.id,
        )

        return Response(
            AnswerSerializer(answer, context=self.context(request)).data,
            status=status.HTTP_201_CREATED if created else status.HTTP_200_OK,
        )


class AnswerDetailAPIView(AnswerBaseView):
    def get_object(self, session_id, answer_id, user):
        try:
            return Answer.objects.select_related('session', 'question').get(
                id=answer_id, session_id=session_id, session__user=user
            )
        except Answer.DoesNotExist:
            raise NotFound("Javob topilmadi")

    @extend_schema(responses=AnswerSerializer, tags=['Answer'])
    def get(self, request, session_id, answer_id):
        answer = self.get_object(session_id, answer_id, request.user)
        return Response(
            answer_serializer_class(answer.session)(
                answer, context=self.context(request)
            ).data
        )

    @extend_schema(
        responses={204: None, 400: detail_serializer('AnswerDeleteError')},
        tags=['Answer'],
        description="Tanlovni bekor qilish — savol yana javobsiz bo'ladi.",
    )
    def delete(self, request, session_id, answer_id):
        answer = self.get_object(session_id, answer_id, request.user)

        if answer.session.is_finished:
            return self.finished_response(
                "Tugagan sessiyada javoblarni o'chirish mumkin emas."
            )

        answer_logger.info(
            "Javob o'chirildi: id=%s session_id=%s user_id=%s",
            answer.id, answer.session_id, request.user.id,
        )
        answer.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class AnswerBulkCreateAPIView(AnswerBaseView):
    @extend_schema(
        request=BulkAnswerSerializer,
        responses={
            201: AnswerSerializer(many=True),
            400: inline_serializer(
                name='AnswerBulkErrorResponse',
                fields={
                    'detail': serializers.CharField(),
                    'question_ids': serializers.ListField(
                        child=serializers.IntegerField(), required=False
                    ),
                },
            ),
        },
        tags=['Answer'],
        description="Bir nechta javobni bir so'rovda saqlash. Takroriy "
                    "yuborilsa javoblar yangilanadi, dublikat yaratilmaydi.",
    )
    def post(self, request, session_id):
        session = self.get_session(request, session_id)

        if session.is_finished:
            return self.finished_response("Tugagan sessiyaga javob qo'shish mumkin emas.")

        serializer = BulkAnswerSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        answers_data = serializer.validated_data['answers']
        question_ids = {item['question'] for item in answers_data}

        missing = authorize_questions(session, question_ids)
        if missing:
            return Response(
                {"detail": "Savol bu sessiyaga tegishli emas yoki topilmadi.",
                 "question_ids": sorted(missing)},
                status=status.HTTP_400_BAD_REQUEST,
            )

        from catalog.models import Question
        questions = {q.id: q for q in Question.objects.filter(id__in=question_ids)}

        saved = []
        with transaction.atomic():
            for item in answers_data:
                answer, _ = save_answer(
                    session=session,
                    question=questions[item['question']],
                    selected_option=item['selected_option'],
                    confidence=item.get('confidence', ''),
                    time_spent_seconds=item.get('time_spent_seconds', 0),
                )
                saved.append(answer)

        answer_logger.info(
            "Ko'p javoblar saqlandi: session_id=%s javoblar_soni=%s user_id=%s",
            session.id, len(saved), request.user.id,
        )

        return Response(
            AnswerSerializer(saved, many=True, context=self.context(request)).data,
            status=status.HTTP_201_CREATED,
        )
