from __future__ import annotations

from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status

from drf_spectacular.utils import extend_schema

from django.db import transaction
from django.utils import timezone
from django.shortcuts import get_object_or_404
import logging

from testengine.filters import TestSessionFilter
from testengine.models import TestSession, Answer, TestResult
from catalog.models import Question
from testengine.routes.serializers import (
    TestSessionSerializer, TestSessionCreateSerializer, TestSessionDetailSerializer,
    QuestionForTestSerializer
)
from common.pagination import StandardResultsPagination
from common.throttles import BurstUserRateThrottle


session_logger = logging.getLogger('testengine.session')


class TestSessionListCreateAPIView(APIView):
    throttle_classes = [BurstUserRateThrottle]
    permission_classes = [IsAuthenticated]

    @extend_schema(responses=TestSessionSerializer(many=True))
    def get(self, request):
        queryset = TestSession.objects.filter(
            user=request.user
        ).select_related('user', 'subject').order_by('-created_at')
        
        queryset = TestSessionFilter(request.query_params, queryset=queryset).qs
        
        paginator = StandardResultsPagination()
        page = paginator.paginate_queryset(queryset, request, view=self)
        serializer = TestSessionSerializer(page, many=True)
        
        return paginator.get_paginated_response(serializer.data)

    @extend_schema(request=TestSessionCreateSerializer, responses=TestSessionSerializer)
    def post(self, request):
        serializer = TestSessionCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        try:
            with transaction.atomic():
                session = TestSession.objects.create(
                    user=request.user,
                    **serializer.validated_data
                )
                
                session_logger.info(
                    "Yangi test sessiyasi yaratildi: id=%s subject=%s mode=%s user_id=%s",
                    session.id, session.subject.name, session.mode, request.user.id
                )
        except Exception as e:
            session_logger.error(
                "Sessiya yaratishda xatolik: xatolik=%s user_id=%s",
                str(e), request.user.id
            )
            return Response(
                {"detail": "Sessiya yaratishda xatolik yuz berdi."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
        return Response(TestSessionSerializer(session).data, status=status.HTTP_201_CREATED)


class TestSessionDetailAPIView(APIView):
    throttle_classes = [BurstUserRateThrottle]
    permission_classes = [IsAuthenticated]

    def get_object(self, pk, user):
        try:
            return TestSession.objects.select_related('user', 'subject').get(
                id=pk,
                user=user
            )
        except TestSession.DoesNotExist:
            raise get_object_or_404(TestSession)

    @extend_schema(responses=TestSessionDetailSerializer)
    def get(self, request, pk):
        session = self.get_object(pk, request.user)
        return Response(TestSessionDetailSerializer(session).data)

    @extend_schema(request=TestSessionCreateSerializer, responses=TestSessionSerializer)
    def patch(self, request, pk):
        session = self.get_object(pk, request.user)
        
        if session.finished_at:
            return Response(
                {"detail": "Tugagan sessiyani o'zgartirish mumkin emas."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        serializer = TestSessionCreateSerializer(session, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        
        try:
            with transaction.atomic():
                serializer.save()
                
                session_logger.info(
                    "Sessiya yangilandi: id=%s user_id=%s",
                    session.id, request.user.id
                )
        except Exception as e:
            session_logger.error(
                "Sessiya yangilashda xatolik: id=%s xatolik=%s user_id=%s",
                session.id, str(e), request.user.id
            )
            return Response(
                {"detail": "Sessiya yangilashda xatolik yuz berdi."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
        return Response(TestSessionSerializer(session).data)


class TestSessionNextQuestionAPIView(APIView):
    throttle_classes = [BurstUserRateThrottle]
    permission_classes = [IsAuthenticated]

    def get_object(self, pk, user):
        try:
            return TestSession.objects.select_related('subject').get(id=pk, user=user)
        except TestSession.DoesNotExist:
            raise get_object_or_404(TestSession)

    @extend_schema(responses=QuestionForTestSerializer)
    def get(self, request, pk):
        session = self.get_object(pk, request.user)
        
        if session.finished_at:
            return Response(
                {"detail": "Bu sessiya tugalgan."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        recent_answers = session.answers.all().order_by('-created_at')[:3]
        
        correct_count = sum(1 for answer in recent_answers if answer.is_correct)
        
        if correct_count >= 3:
            min_difficulty = 8
        elif correct_count == 2:
            min_difficulty = 5
        else:
            min_difficulty = 1
        
        answered_ids = session.answers.values_list('question_id', flat=True)
        question = Question.objects.filter(
            topic__subject=session.subject,
            difficulty__gte=min_difficulty
        ).exclude(id__in=answered_ids).first()
        
        if not question:
            question = Question.objects.filter(
                topic__subject=session.subject,
            ).exclude(id__in=answered_ids).order_by('-difficulty').first()
        
        if not question:
            return Response(
                {"detail": "Boshqa savollar yo'q. Sessiyani yakunlang."},
                status=status.HTTP_404_NOT_FOUND
            )
        
        return Response(QuestionForTestSerializer(question).data)


class TestSessionFinishAPIView(APIView):
    throttle_classes = [BurstUserRateThrottle]
    permission_classes = [IsAuthenticated]

    def get_object(self, pk, user):
        try:
            return TestSession.objects.select_related('subject').get(id=pk, user=user)
        except TestSession.DoesNotExist:
            raise get_object_or_404(TestSession)

    @extend_schema(responses=TestSessionDetailSerializer)
    def post(self, request, pk):
        session = self.get_object(pk, request.user)
        
        if session.finished_at:
            return Response(
                {"detail": "Bu sessiya allaqachon tugalgan."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            with transaction.atomic():
                session.finished_at = timezone.now()
                session.save()
                
                answers = session.answers.all()
                correct_count = answers.filter(is_correct=True).count()
                incorrect_count = answers.filter(is_correct=False).count()
                
                total_score = correct_count
                
                if session.started_at:
                    duration = (session.finished_at - session.started_at).total_seconds()
                else:
                    duration = 0
                
                TestResult.objects.create(
                    session=session,
                    total_score=total_score,
                    correct_count=correct_count,
                    incorrect_count=incorrect_count,
                    duration_seconds=int(duration)
                )
                
                session_logger.info(
                    "Test sessiyasi yakunlandi: id=%s score=%s correct=%s incorrect=%s user_id=%s",
                    session.id, total_score, correct_count, incorrect_count, request.user.id
                )
        except Exception as e:
            session_logger.error(
                "Sessiya yakunlanishda xatolik: id=%s xatolik=%s user_id=%s",
                pk, str(e), request.user.id
            )
            return Response(
                {"detail": "Sessiya yakunlanishda xatolik yuz berdi."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
        return Response(TestSessionDetailSerializer(session).data)


class TestSessionSyncAPIView(APIView):
    throttle_classes = [BurstUserRateThrottle]
    permission_classes = [IsAuthenticated]

    def get_object(self, pk, user):
        try:
            return TestSession.objects.select_related('subject').get(id=pk, user=user)
        except TestSession.DoesNotExist:
            raise get_object_or_404(TestSession)

    @extend_schema(responses=TestSessionDetailSerializer)
    def post(self, request, pk):
        session = self.get_object(pk, request.user)
        
        if session.finished_at:
            return Response(
                {"detail": "Tugagan sessiyada sync qilish mumkin emas."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        from testengine.routes.serializers import BulkAnswerSerializer
        serializer = BulkAnswerSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        try:
            with transaction.atomic():
                answers_data = serializer.validated_data.get('answers', [])
                created_count = 0
                
                for answer_data in answers_data:
                    Answer.objects.create(
                        session=session,
                        question_id=answer_data['question'],
                        selected_option=answer_data['selected_option'],
                        is_correct=answer_data['is_correct'],
                        confidence=answer_data.get('confidence', ''),
                        time_spent_seconds=answer_data.get('time_spent_seconds', 0)
                    )
                    created_count += 1
                
                session_logger.info(
                    "Offline javoblar sinxronlandi: session_id=%s javoblar_soni=%s user_id=%s",
                    session.id, created_count, request.user.id
                )
        except Exception as e:
            session_logger.error(
                "Sync paytida xatolik: session_id=%s xatolik=%s user_id=%s",
                session.id, str(e), request.user.id
            )
            return Response(
                {"detail": "Javoblar sinxronlanishda xatolik yuz berdi."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
        return Response(
            {"detail": f"{created_count} ta javob sinxronlandi."},
            status=status.HTTP_201_CREATED
        )
