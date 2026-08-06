from __future__ import annotations

from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status

from drf_spectacular.utils import extend_schema

from django.db import transaction
from django.shortcuts import get_object_or_404
import logging

from testengine.filters import AnswerFilter
from testengine.models import TestSession, Answer
from testengine.routes.serializers import AnswerSerializer, AnswerCreateSerializer, BulkAnswerSerializer
from common.permissions import IsOwner
from common.pagination import StandardResultsPagination
from common.throttles import BurstUserRateThrottle


answer_logger = logging.getLogger('testengine.answer')


class AnswerListCreateAPIView(APIView):
    throttle_classes = [BurstUserRateThrottle]
    permission_classes = [IsAuthenticated]

    @extend_schema(responses=AnswerSerializer(many=True))
    def get(self, request, session_id):
        session = get_object_or_404(TestSession, id=session_id, user=request.user)

        queryset = session.answers.select_related('question').order_by('-created_at')
        queryset = AnswerFilter(request.query_params, queryset=queryset).qs

        paginator = StandardResultsPagination()
        page = paginator.paginate_queryset(queryset, request, view=self)
        serializer = AnswerSerializer(page, many=True)

        return paginator.get_paginated_response(serializer.data)

    @extend_schema(request=AnswerCreateSerializer, responses=AnswerSerializer)
    def post(self, request, session_id):
        session = get_object_or_404(TestSession, id=session_id, user=request.user)

        if session.finished_at:
            return Response(
                {"detail": "Tugagan sessiyaga javob qo'shish yoki o'zgartirish mumkin emas."},
                status=status.HTTP_400_BAD_REQUEST)

        serializer = AnswerCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        question = serializer.validated_data['question']
        selected_option = serializer.validated_data['selected_option']
        # TODO: `correct_option` — Question modelidagi haqiqiy field nomiga moslang
        is_correct = (selected_option == question.correct_option)

        try:
            with transaction.atomic():
                answer, created = Answer.objects.update_or_create(
                    session=session,
                    question=question,
                    defaults={
                        'selected_option': selected_option,
                        'is_correct': is_correct,
                        'confidence': serializer.validated_data.get('confidence', ''),
                        'time_spent_seconds': serializer.validated_data.get('time_spent_seconds', 0),
                    }
                )
                answer_logger.info(
                    "Javob %s: id=%s session_id=%s question_id=%s user_id=%s",
                    "yaratildi" if created else "yangilandi",
                    answer.id, session.id, answer.question_id, request.user.id)
        except Exception as e:
            answer_logger.error(
                "Javob saqlashda xatolik: session_id=%s xatolik=%s user_id=%s",
                session.id, str(e), request.user.id)
            return Response(
                {"detail": "Javob saqlashda xatolik yuz berdi."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        status_code = status.HTTP_201_CREATED if created else status.HTTP_200_OK
        return Response(AnswerSerializer(answer).data, status=status_code)


class AnswerDetailAPIView(APIView):
    throttle_classes = [BurstUserRateThrottle]
    permission_classes = [IsAuthenticated]

    def get_object(self, session_id, answer_id, user):
        try:
            return Answer.objects.select_related('session', 'question').get(
                id=answer_id,
                session_id=session_id,
                session__user=user
            )
        except Answer.DoesNotExist:
            raise get_object_or_404(Answer)

    @extend_schema(responses=AnswerSerializer)
    def get(self, request, session_id, answer_id):
        answer = self.get_object(session_id, answer_id, request.user)
        return Response(AnswerSerializer(answer).data)

    @extend_schema(responses={204: None})
    def delete(self, request, session_id, answer_id):
        answer = self.get_object(session_id, answer_id, request.user)

        if answer.session.finished_at:
            return Response(
                {"detail": "Tugagan sessiyada javoblarni o'chirish mumkin emas."},
                status=status.HTTP_400_BAD_REQUEST)

        answer_logger.info(
            "Javob o'chirildi: id=%s session_id=%s user_id=%s",
            answer.id, answer.session_id, request.user.id)

        answer.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class AnswerBulkCreateAPIView(APIView):
    throttle_classes = [BurstUserRateThrottle]
    permission_classes = [IsAuthenticated]

    @extend_schema(request=BulkAnswerSerializer, responses=AnswerSerializer(many=True))
    def post(self, request, session_id):
        session = get_object_or_404(TestSession, id=session_id, user=request.user)

        if session.finished_at:
            return Response(
                {"detail": "Tugagan sessiyaga javob qo'shish mumkin emas."},
                status=status.HTTP_400_BAD_REQUEST
            )

        serializer = BulkAnswerSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            with transaction.atomic():
                answers_data = serializer.validated_data.get('answers', [])
                saved_answers = []

                for answer_data in answers_data:
                    question_id = answer_data['question']
                    selected_option = answer_data['selected_option']

                    # TODO: `correct_option` — Question modelidagi haqiqiy field nomiga moslang
                    question = get_object_or_404(session.answers.model.question.field.related_model, id=question_id)
                    is_correct = (selected_option == question.correct_option)

                    answer, created = Answer.objects.update_or_create(
                        session=session,
                        question_id=question_id,
                        defaults={
                            'selected_option': selected_option,
                            'is_correct': is_correct,
                            'confidence': answer_data.get('confidence', ''),
                            'time_spent_seconds': answer_data.get('time_spent_seconds', 0),
                        }
                    )
                    saved_answers.append(answer)

                answer_logger.info(
                    "Ko'p javoblar saqlandi: session_id=%s javoblar_soni=%s user_id=%s",
                    session.id, len(saved_answers), request.user.id
                )
        except Exception as e:
            answer_logger.error(
                "Ko'p javob saqlashda xatolik: session_id=%s xatolik=%s user_id=%s",
                session.id, str(e), request.user.id
            )
            return Response(
                {"detail": "Javoblar saqlashda xatolik yuz berdi."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        return Response(
            AnswerSerializer(saved_answers, many=True).data,
            status=status.HTTP_201_CREATED
        )