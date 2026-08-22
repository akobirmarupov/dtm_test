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
    BulkAnswerSerializer,
    SessionFinishResponseSerializer,
    SessionProgressSerializer,
    SessionQuestionReviewSerializer,
    SessionQuestionSerializer,
    TestSessionCreateSerializer,
    TestSessionDetailSerializer,
    TestSessionSerializer,
    TestSessionUpdateSerializer,
)
from testengine.services import (
    answers_by_question,
    authorize_questions,
    create_session,
    finish_session,
    save_answer,
    session_progress,
    session_questions,
)

session_logger = logging.getLogger('testengine.session')


def detail_serializer(name):
    return inline_serializer(name=name, fields={'detail': serializers.CharField()})


class SessionAccessMixin:
    """Sessiyani egasi bo'yicha oladi va kontekstni tayyorlaydi."""

    throttle_classes = [BurstUserRateThrottle]
    permission_classes = [IsAuthenticated]

    def get_session(self, request, pk):
        queryset = TestSession.objects.select_related('user', 'subject')
        return get_object_or_404(queryset, pk=pk, user=request.user)

    def context(self, request, session=None, answers=None):
        data = {'request': request, 'language': resolve_language(request)}
        if answers is not None:
            data['answers'] = answers
        elif session is not None:
            data['answers'] = answers_by_question(session)
        return data

    def finished_response(self, message="Bu sessiya allaqachon yakunlangan."):
        return Response({"detail": message}, status=status.HTTP_400_BAD_REQUEST)


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
        serializer = TestSessionCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        session = create_session(
            user=request.user,
            subject=data['subject'],
            mode=data['mode'],
            question_count=data.get('question_count') or DEFAULT_QUESTION_COUNT,
            topic_ids=[topic.id for topic in data.get('topics', [])],
        )

        if session is None:
            return Response(
                {"detail": "Bu fan (yoki tanlangan mavzular) bo'yicha savollar topilmadi."},
                status=status.HTTP_400_BAD_REQUEST,
            )

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
        """Yakunlanmagan sessiyani tashlab yuborish. Yakunlangan sessiya
        natijasi tarix va reyting uchun kerak — u o'chirilmaydi."""
        session = self.get_session(request, pk)

        if session.is_finished:
            return self.finished_response("Yakunlangan sessiyani o'chirib bo'lmaydi.")

        session.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class SessionQuestionListAPIView(SessionAccessMixin, APIView):
    """GET /testengine/sessions/<pk>/questions/ — butun test varaqasi.

    Mijoz shu bitta so'rov bilan 15 ta savolni ham, o'z tanlovlarini ham
    oladi va offline holatda ham oldinga-orqaga yura oladi.
    """

    @extend_schema(
        responses=SessionQuestionSerializer(many=True),
        tags=['TestSession'],
        description="Sessiyaning barcha savollari tartib bo'yicha + mening "
                    "javoblarim. To'g'ri/noto'g'ri ma'lumoti YO'Q — u faqat "
                    "`finish` dan keyin `review` da ochiladi.",
    )
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
    """Tartib raqami bo'yicha bitta savol: `/questions/3/`.

    "10-savoldaman, 3-savolga qaytaman" — aynan shu endpoint.
    """

    def get_item(self, session, order):
        item = session_questions(session).filter(order=order).first()
        if item is None:
            from rest_framework.exceptions import NotFound
            raise NotFound(f"{order}-savol bu sessiyada mavjud emas.")
        return item

    @extend_schema(
        responses={200: SessionQuestionSerializer, 404: detail_serializer('SessionQuestionNotFound')},
        tags=['TestSession'],
    )
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
        tags=['TestSession'],
        description="Shu savolga javob berish YOKI oldingi javobni "
                    "o'zgartirish. Javob har safar qayta yoziladi, natija "
                    "ko'rsatilmaydi.",
    )
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
        tags=['TestSession'],
        description="Tanlovni bekor qilish — savol yana javobsiz bo'lib qoladi.",
    )
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
    """GET /testengine/sessions/<pk>/progress/

    "Yakunlash" tugmasidan oldin "2 ta savol javobsiz qoldi" ogohlantirishini
    ko'rsatish uchun.
    """

    @extend_schema(responses=SessionProgressSerializer, tags=['TestSession'])
    def get(self, request, pk):
        session = self.get_session(request, pk)
        return Response(SessionProgressSerializer(session_progress(session)).data)


class TestSessionNextQuestionAPIView(SessionAccessMixin, APIView):
    """GET /testengine/sessions/<pk>/next-question/ — keyingi JAVOBSIZ savol.

    Ilgari bu endpoint har safar yangi savol tanlar edi va sessiyaning
    savollar ro'yxati degan tushuncha yo'q edi. Endi u qotirilgan ro'yxat
    bo'ylab ishlaydi: javob berilmagan birinchi savolni qaytaradi.
    """

    @extend_schema(
        responses={
            200: SessionQuestionSerializer,
            400: detail_serializer('NextQuestionSessionFinished'),
            404: detail_serializer('NextQuestionNotFound'),
        },
        tags=['TestSession'],
    )
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
    """POST /testengine/sessions/<pk>/finish/

    Natija AYNAN shu yerda tug'iladi. Bundan keyin javoblar o'zgarmaydi.
    """

    @extend_schema(
        request=None,
        responses={
            200: SessionFinishResponseSerializer,
            400: detail_serializer('TestSessionFinishError'),
        },
        tags=['TestSession'],
        description="Testni yakunlash. Javobda natija va har bir savol "
                    "bo'yicha to'liq tahlil (to'g'ri javob bilan) qaytadi.",
    )
    def post(self, request, pk):
        session = self.get_session(request, pk)

        if session.is_finished:
            return self.finished_response("Bu sessiya allaqachon yakunlangan.")

        result = finish_session(session)
        if result is None:
            return self.finished_response("Bu sessiya allaqachon yakunlangan.")

        session.refresh_from_db()
        answers = answers_by_question(session)
        context = self.context(request, answers=answers)

        payload = {
            'session': session,
            'result': result,
            'review': list(session_questions(session)),
        }
        return Response(
            SessionFinishResponseSerializer(payload, context=context).data,
            status=status.HTTP_200_OK,
        )


class TestSessionReviewAPIView(SessionAccessMixin, APIView):
    """GET /testengine/sessions/<pk>/review/ — yakunlangandan keyingi tahlil."""

    @extend_schema(
        responses={
            200: SessionFinishResponseSerializer,
            400: detail_serializer('TestSessionReviewNotFinished'),
        },
        tags=['TestSession'],
        description="Har bir savol: sizning javobingiz, to'g'ri javob, "
                    "to'g'ri/noto'g'ri. Faqat sessiya yakunlangandan keyin.",
    )
    def get(self, request, pk):
        session = self.get_session(request, pk)

        if not session.is_finished:
            return Response(
                {"detail": "Sessiya hali yakunlanmagan. Natijani ko'rish uchun "
                           "avval testni yakunlang."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        result = TestResult.objects.filter(session=session).first()
        answers = answers_by_question(session)
        context = self.context(request, answers=answers)

        payload = {
            'session': session,
            'result': result,
            'review': list(session_questions(session)),
        }
        return Response(SessionFinishResponseSerializer(payload, context=context).data)


class TestSessionSyncAPIView(SessionAccessMixin, APIView):
    """POST /testengine/sessions/<pk>/sync/ — offline javoblarni yuklash.

    Internet uzilganda mijoz javoblarni o'zida saqlaydi va aloqa tiklanganda
    hammasini bir so'rovda yuboradi. Takroriy yuborish xavfsiz: javob
    yangilanadi, dublikat yaratilmaydi.
    """

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

        # Savollar aynan SHU SESSIYAGA tegishli bo'lishi shart — aks holda
        # mijoz sessiyaga kirmagan savolga javob yuborib, natijani shishirib
        # yuborishi mumkin.
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
