"""Test sessiyasi endpointlari.

Oqim (foydalanuvchi talabi):

1. `POST /testengine/sessions/` — masalan 15 ta savolli sessiya ochiladi.
   Savollar shu paytda qotiriladi.
2. `GET .../questions/` — butun test varaqasi: 15 ta savol + mening
   tanlovlarim. Mijoz shu ro'yxat bo'ylab XOHLAGANCHA yuradi.
3. `POST .../questions/<order>/answer/` — 3-savolga qaytib javobni
   o'zgartirish. Javob qayta yozilaveradi, natija KO'RSATILMAYDI.
4. `POST .../finish/` — faqat shu paytda natija hisoblanadi va to'g'ri
   javoblar ochiladi. Bundan keyin javoblarni o'zgartirib bo'lmaydi.
"""

from __future__ import annotations

import logging

from django.db import transaction
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema, inline_serializer
from rest_framework import serializers, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from catalog.models import Question
from common.i18n import resolve_language
from common.pagination import StandardResultsPagination
from common.throttles import BurstUserRateThrottle
from testengine.filters import TestSessionFilter
from testengine.models import DEFAULT_QUESTION_COUNT, Answer, TestResult, TestSession
from testengine.routes.serializers import (
    AnswerOptionSerializer,
    BulkAnswerSerializer,SessionFinishResponseSerializer,SessionProgressSerializer,
    SessionQuestionReviewSerializer,SessionQuestionSerializer,TestSessionCreateSerializer,
    TestSessionDetailSerializer,TestSessionSerializer,TestSessionUpdateSerializer)
from testengine.services import (
    answers_by_question,authorize_questions,create_session,
    ensure_not_expired,finish_session,save_answer,session_progress,session_questions)

session_logger = logging.getLogger('testengine.session')


def detail_serializer(name):
    return inline_serializer(name=name, fields={'detail': serializers.CharField()})


class _NoQuestions(Exception):
    """Savol topilmadi — tranzaksiyani orqaga qaytarish uchun ichki signal."""


class SessionAccessMixin:
    """Sessiyani egasi bo'yicha oladi va kontekstni tayyorlaydi."""

    throttle_classes = [BurstUserRateThrottle]
    permission_classes = [IsAuthenticated]

    def get_session(self, request, pk, *, check_expiry=True):
        queryset = TestSession.objects.select_related(
            'user', 'subject', 'topic', 'grade')
        session = get_object_or_404(queryset, pk=pk, user=request.user)
        if check_expiry:
            ensure_not_expired(session)
        return session

    def context(self, request, session=None, answers=None, explanations=None):
        data = {'request': request, 'language': resolve_language(request)}
        if answers is not None:
            data['answers'] = answers
        elif session is not None:
            data['answers'] = answers_by_question(session)
        if explanations is not None:
            data['explanations'] = explanations
        return data

    def review_payload(self, request, session, result, *, consume_explanation=False):
        from billing.entitlements import entitlements_for_request
        from testengine.access import explanation_access
        from testengine.explanations import get_explanation_service

        answers = answers_by_question(session)
        items = list(session_questions(session))

        entitlements = entitlements_for_request(request)
        access = explanation_access(
            request.user, session, entitlements, consume=consume_explanation
        )

        explanations = {}
        if access['available']:
            explanations = get_explanation_service().for_review(
                items, language=resolve_language(request), request=request
            )

        context = self.context(
            request, answers=answers, explanations=explanations
        )
        return {
            'session': session,
            'result': result,
            'review': items,
            'explanation_access': access,
        }, context

    def finished_response(self, message="Bu sessiya allaqachon yakunlangan."):
        return Response({"detail": message}, status=status.HTTP_400_BAD_REQUEST)

    def expired_response(self, session):
        return Response(
            {
                "detail": "Test vaqti tugadi va sessiya avtomatik yakunlandi.",
                "code": "session_expired",
                "session_id": session.id,
            },
            status=status.HTTP_409_CONFLICT,
        )


class TestSessionListCreateAPIView(SessionAccessMixin, APIView):
    @extend_schema(responses=TestSessionSerializer(many=True), tags=['TestSession'])
    def get(self, request):
        queryset = TestSession.objects.filter(
            user=request.user
        ).select_related('user', 'subject').order_by('-created_at')

        queryset = TestSessionFilter(request.query_params, queryset=queryset).qs

        paginator = StandardResultsPagination()
        page = paginator.paginate_queryset(queryset, request, view=self)
        serializer = TestSessionSerializer(page, many=True, context=self.context(request))
        return paginator.get_paginated_response(serializer.data)

    @extend_schema(
        request=TestSessionCreateSerializer,
        responses={
            201: TestSessionDetailSerializer,
            400: detail_serializer('TestSessionCreateError'),
        },
        tags=['TestSession'],
        description=(
            "Yangi test sessiyasi. `question_count` (standart "
            f"{DEFAULT_QUESTION_COUNT}) ta savol shu paytda tanlanib QOTIRILADI — "
            "shuning uchun test davomida savollar tartibi o'zgarmaydi va "
            "istalgan savolga qaytib javobni almashtirish mumkin."
        ),
    )
    def post(self, request):
        from billing.entitlements import entitlements_for_request
        from testengine.access import DailyTopicLimitExceeded, register_session_topics

        serializer = TestSessionCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        entitlements = entitlements_for_request(request)
        requested = data.get('question_count') or DEFAULT_QUESTION_COUNT
        if requested > entitlements.max_question_count:
            return Response(
                {
                    "detail": f"Sizning tarifingizda bir testda ko'pi bilan "
                              f"{entitlements.max_question_count} ta savol bo'lishi mumkin.",
                    "code": "question_count_exceeded",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        topics = data.get('topics', [])
        topic_ids = [topic.id for topic in topics]
        if not topic_ids:
            from testengine.access import allowed_topic_ids

            allowed = allowed_topic_ids(request.user, data['subject'], entitlements)
            if allowed is not None:
                if not allowed:
                    from testengine.access import limit_response_payload, next_reset_at
                    from testengine.access import topics_used_today

                    used = topics_used_today(request.user)
                    return Response(
                        limit_response_payload({
                            'allowed': False,
                            'code': 'daily_topic_limit_reached',
                            'detail': (
                                f"Bugungi kunlik limitingiz "
                                f"({entitlements.daily_topic_limit} ta mavzu) tugadi. "
                                f"Ertaga 00:00 dan keyin yangi mavzular ochiladi, yoki "
                                f"Pro sotib olib cheksiz mavzuda test ishlang."
                            ),
                            'limit': entitlements.daily_topic_limit,
                            'used': used,
                            'remaining': 0,
                            'reset_at': next_reset_at(),
                        }),
                        status=status.HTTP_403_FORBIDDEN,
                    )
                topic_ids = allowed

        try:
            with transaction.atomic():
                session = create_session(
                    user=request.user,
                    subject=data['subject'],
                    mode=data['mode'],
                    question_count=requested,
                    topic_ids=topic_ids,
                    topic=topics[0] if len(topics) == 1 else None,
                )
                if session is None:
                    raise _NoQuestions()
                register_session_topics(request.user, session, entitlements)
        except _NoQuestions:
            return Response(
                {"detail": "Bu fan (yoki tanlangan mavzular) bo'yicha savollar topilmadi."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        except DailyTopicLimitExceeded as error:
            session_logger.info(
                'Kunlik mavzu limiti (fan bo\'yicha sessiya): user_id=%s subject_id=%s',
                request.user.id, data['subject'].id,
            )
            return Response(error.payload, status=status.HTTP_403_FORBIDDEN)

        return Response(
            TestSessionDetailSerializer(session, context=self.context(request, session)).data,
            status=status.HTTP_201_CREATED,
        )


class TestSessionDetailAPIView(SessionAccessMixin, APIView):
    @extend_schema(responses=TestSessionDetailSerializer, tags=['TestSession'])
    def get(self, request, pk):
        session = self.get_session(request, pk)
        return Response(
            TestSessionDetailSerializer(session, context=self.context(request, session)).data
        )

    @extend_schema(
        request=TestSessionUpdateSerializer,
        responses={200: TestSessionDetailSerializer, 400: detail_serializer('TestSessionUpdateError')},
        tags=['TestSession'],
    )
    def patch(self, request, pk):
        session = self.get_session(request, pk)

        if session.is_finished:
            return self.finished_response("Tugagan sessiyani o'zgartirish mumkin emas.")

        serializer = TestSessionUpdateSerializer(session, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(
            TestSessionDetailSerializer(session, context=self.context(request, session)).data
        )

    @extend_schema(responses={204: None, 400: detail_serializer('TestSessionDeleteError')}, tags=['TestSession'])
    def delete(self, request, pk):
        session = self.get_session(request, pk)

        if session.is_finished:
            return self.finished_response("Yakunlangan sessiyani o'chirib bo'lmaydi.")

        session.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class SessionQuestionListAPIView(SessionAccessMixin, APIView):
    @extend_schema(responses=SessionQuestionSerializer(many=True),tags=['TestSession'])
    def get(self, request, pk):
        session = self.get_session(request, pk)
        answers = answers_by_question(session)
        items = session_questions(session)

        serializer_class = (
            SessionQuestionReviewSerializer if session.is_finished else SessionQuestionSerializer
        )
        return Response(
            serializer_class(
                items, many=True, context=self.context(request, answers=answers)
            ).data
        )


class SessionQuestionDetailAPIView(SessionAccessMixin, APIView):
    def get_item(self, session, order):
        item = session_questions(session).filter(order=order).first()
        if item is None:
            from rest_framework.exceptions import NotFound
            raise NotFound(f"{order}-savol bu sessiyada mavjud emas.")
        return item

    @extend_schema(responses={200: SessionQuestionSerializer, 404: detail_serializer('SessionQuestionNotFound')},tags=['TestSession'])
    def get(self, request, pk, order):
        session = self.get_session(request, pk)
        item = self.get_item(session, order)
        answers = answers_by_question(session)

        serializer_class = (
            SessionQuestionReviewSerializer if session.is_finished else SessionQuestionSerializer
        )
        return Response(
            serializer_class(item, context=self.context(request, answers=answers)).data
        )

    @extend_schema(
        request=AnswerOptionSerializer,
        responses={
            200: SessionQuestionSerializer,
            400: detail_serializer('SessionAnswerError'),
        },
        tags=['TestSession'])
    def post(self, request, pk, order):
        session = self.get_session(request, pk)

        if session.is_finished:
            return self.finished_response(
                "Sessiya yakunlangan — javoblarni o'zgartirib bo'lmaydi."
            )

        item = self.get_item(session, order)
        serializer = AnswerOptionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        options = item.question.options if isinstance(item.question.options, dict) else {}
        available = {str(key).strip().upper() for key in options}
        if available and data['selected_option'] not in available:
            return Response(
                {"detail": f"Bu savolda bunday variant yo'q. Mavjud: {sorted(available)}"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        with transaction.atomic():
            save_answer(
                session=session,
                question=item.question,
                selected_option=data['selected_option'],
                confidence=data.get('confidence', ''),
                time_spent_seconds=data.get('time_spent_seconds', 0),
            )

        answers = answers_by_question(session)
        return Response(
            SessionQuestionSerializer(item, context=self.context(request, answers=answers)).data
        )

    @extend_schema(
        responses={200: SessionQuestionSerializer, 400: detail_serializer('SessionAnswerClearError')},
        tags=['TestSession'])
    def delete(self, request, pk, order):
        session = self.get_session(request, pk)

        if session.is_finished:
            return self.finished_response(
                "Sessiya yakunlangan — javoblarni o'zgartirib bo'lmaydi."
            )

        item = self.get_item(session, order)
        Answer.objects.filter(session=session, question=item.question).delete()

        answers = answers_by_question(session)
        return Response(
            SessionQuestionSerializer(item, context=self.context(request, answers=answers)).data
        )


class TestSessionProgressAPIView(SessionAccessMixin, APIView):
    @extend_schema(responses=SessionProgressSerializer, tags=['TestSession'])
    def get(self, request, pk):
        session = self.get_session(request, pk)
        return Response(SessionProgressSerializer(session_progress(session)).data)


class TestSessionNextQuestionAPIView(SessionAccessMixin, APIView):
    @extend_schema(
        responses={
            200: SessionQuestionSerializer,
            400: detail_serializer('NextQuestionSessionFinished'),
            404: detail_serializer('NextQuestionNotFound'),
        },
        tags=['TestSession'],)
    def get(self, request, pk):
        session = self.get_session(request, pk)

        if session.is_finished:
            return self.finished_response("Bu sessiya yakunlangan.")

        answers = answers_by_question(session)
        for item in session_questions(session):
            if item.question_id not in answers:
                return Response(
                    SessionQuestionSerializer(
                        item, context=self.context(request, answers=answers)
                    ).data
                )

        return Response(
            {"detail": "Barcha savollarga javob berildi. Sessiyani yakunlang."},
            status=status.HTTP_404_NOT_FOUND,
        )


class TestSessionFinishAPIView(SessionAccessMixin, APIView):
    @extend_schema(
        request=None,
        responses={
            200: SessionFinishResponseSerializer,
            400: detail_serializer('TestSessionFinishError'),
        },
        tags=['TestSession'])
    def post(self, request, pk):
        session = self.get_session(request, pk, check_expiry=False)

        if session.is_finished:
            return self.finished_response("Bu sessiya allaqachon yakunlangan.")

        result = finish_session(session, auto=session.is_expired)
        if result is None:
            return self.finished_response("Bu sessiya allaqachon yakunlangan.")

        session.refresh_from_db()
        payload, context = self.review_payload(
            request, session, result, consume_explanation=True
        )
        return Response(
            SessionFinishResponseSerializer(payload, context=context).data,
            status=status.HTTP_200_OK,
        )


class TestSessionReviewAPIView(SessionAccessMixin, APIView):
    @extend_schema(
        responses={
            200: SessionFinishResponseSerializer,
            400: detail_serializer('TestSessionReviewNotFinished'),
        },
        tags=['TestSession'])
    def get(self, request, pk):
        session = self.get_session(request, pk)

        if not session.is_finished:
            return Response(
                {"detail": "Sessiya hali yakunlanmagan. Natijani ko'rish uchun "
                           "avval testni yakunlang."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        result = TestResult.objects.filter(session=session).first()
        payload, context = self.review_payload(
            request, session, result, consume_explanation=True
        )
        return Response(SessionFinishResponseSerializer(payload, context=context).data)


class TestSessionSyncAPIView(SessionAccessMixin, APIView):
    @extend_schema(
        request=BulkAnswerSerializer,
        responses={
            200: SessionProgressSerializer,
            400: inline_serializer(
                name='TestSessionSyncErrorResponse',
                fields={
                    'detail': serializers.CharField(),
                    'question_ids': serializers.ListField(
                        child=serializers.IntegerField(), required=False
                    ),
                },
            ),
        },
        tags=['TestSession'],
    )
    def post(self, request, pk):
        session = self.get_session(request, pk)

        if session.is_finished:
            return self.finished_response("Tugagan sessiyada sync qilish mumkin emas.")

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

        questions = {
            question.id: question
            for question in Question.objects.filter(id__in=question_ids)
        }

        with transaction.atomic():
            for item in answers_data:
                save_answer(
                    session=session,
                    question=questions[item['question']],
                    selected_option=item['selected_option'],
                    confidence=item.get('confidence', ''),
                    time_spent_seconds=item.get('time_spent_seconds', 0),
                )

        session_logger.info(
            'Offline javoblar sinxronlandi: session_id=%s javoblar_soni=%s user_id=%s',
            session.id, len(answers_data), request.user.id,
        )

        return Response(
            SessionProgressSerializer(session_progress(session)).data,
            status=status.HTTP_200_OK,
        )
