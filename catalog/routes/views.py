from __future__ import annotations

from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status

from drf_spectacular.utils import extend_schema

from django.db import IntegrityError, transaction
from django.core.cache import cache
import logging

from rest_framework.exceptions import NotFound

from catalog.filters import SubjectFilter, QuestionFilter, TopicFilter
from catalog.models import Subject, Question, Topic
from common.permissions import IsMentorOrAdmin
from common.pagination import StandardResultsPagination
from common.throttles import BurstUserRateThrottle
from common.models import Role
from catalog.routes.serializers import SubjectSerializer, TopicSerializer, QuestionSerializer, QuestionWriteSerializer


subject_logger = logging.getLogger('subject')
topic_logger = logging.getLogger('topic')
question_logger = logging.getLogger('question')


CACHE_DURATION = {
    'subject_list': 60 * 5,
    'question_list': 60 * 2
}


class SubjectListCreateAPIView(APIView):
    throttle_classes = [BurstUserRateThrottle]

    def get_permissions(self):
        if self.request.method == "POST":
            return [IsAuthenticated(), IsMentorOrAdmin()]
        return [IsAuthenticated()]


    @extend_schema(responses=SubjectSerializer(many=True))
    def get(self, request):
        cache_key = f"subjects:list:{request.query_params.urlencode()}"
        cached = cache.get(cache_key)
        if cached:
            return cached
        
        queryset = Subject.objects.all().prefetch_related('topics').order_by("name")
        queryset = SubjectFilter(request.query_params, queryset=queryset).qs

        paginator = StandardResultsPagination()
        page = paginator.paginate_queryset(queryset, request, view=self)
        serializer = SubjectSerializer(page, many=True)
        response = paginator.get_paginated_response(serializer.data)
        
        cached_data = cache.get(cache_key)
        if cached_data is not None:
            return Response(cached_data)

        cache.set(cache_key, serializer.data, CACHE_DURATION[...])
        return Response(serializer.data)


    @extend_schema(request=SubjectSerializer, responses=SubjectSerializer)
    def post(self, request):
        serializer = SubjectSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            with transaction.atomic():
                subject = serializer.save()
                cache.delete_pattern('subjects:list:*')
        except IntegrityError as e:
            subject_logger.error(
                "Fan yaratishda IntegrityError: %s, ma'lumot: %s", 
                str(e), request.data, extra={"user_id": request.user.id}
            )
            return Response(
                {"detail": "Bu nomdagi fan allaqachon mavjud."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        subject_logger.info(
            "Fan yaratildi: id=%s nomi=%r foydalanuvchi_id=%s",
            subject.id, subject.name, request.user.id,
        )
        return Response(SubjectSerializer(subject).data, status=status.HTTP_201_CREATED)


class SubjectDetailAPIView(APIView):
    throttle_classes = [BurstUserRateThrottle]

    def get_permissions(self):
        if self.request.method in ("GET", "HEAD", "OPTIONS"):
            return [IsAuthenticated()]
        return [IsAuthenticated(), IsMentorOrAdmin()]

    def get_object(self, pk):
        try:
            return Subject.objects.get(pk=pk)
        except (Subject.DoesNotExist, ValueError, TypeError):
            raise NotFound({"detail": "Bunday fan mavjud emas."})


    @extend_schema(responses=SubjectSerializer)
    def get(self, request, pk):
        subject = self.get_object(pk)
        return Response(SubjectSerializer(subject).data)


    @extend_schema(request=SubjectSerializer, responses=SubjectSerializer)
    def put(self, request, pk):
        return self._update(request, pk, partial=False)


    @extend_schema(request=SubjectSerializer, responses=SubjectSerializer)
    def patch(self, request, pk):
        return self._update(request, pk, partial=True)

    def _update(self, request, pk, *, partial):
        subject = self.get_object(pk)
        serializer = SubjectSerializer(subject, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)

        try:
            with transaction.atomic():
                serializer.save()
                cache.delete_pattern('subjects:list:*')
        except IntegrityError:
            return Response(
                {"detail": "Bu nomdagi fan allaqachon mavjud."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        subject_logger.info(
            "Fan tahrirlandi: id=%s nomi=%r foydalanuvchi_id=%s",
            subject.id, subject.name, request.user.id,
        )
        return Response(serializer.data)


    @extend_schema(responses={204: None})
    def delete(self, request, pk):
        subject = self.get_object(pk)

        if subject.topics.exists():
            return Response(
                {
                    "detail": (
                        "Bu fanga bog'liq mavzular mavjud. Fanni o'chirishdan oldin "
                        "unga tegishli barcha mavzularni o'chiring yoki boshqa fanga ko'chiring."
                    )
                },
                status=status.HTTP_409_CONFLICT,
            )

        subject_id = subject.id
        with transaction.atomic():
            subject.delete()
            cache.delete_pattern('subjects:list:*')

        subject_logger.warning(
            "Fan o'chirildi: id=%s foydalanuvchi_id=%s", subject_id, request.user.id,
        )
        return Response(status=status.HTTP_204_NO_CONTENT)


class TopicListCreateAPIView(APIView):
    throttle_classes = [BurstUserRateThrottle]

    def get_permissions(self):
        if self.request.method == "POST":
            return [IsAuthenticated(), IsMentorOrAdmin()]
        return [IsAuthenticated()]


    @extend_schema(responses=TopicSerializer(many=True))
    def get(self, request):
        cache_key = f"topics:list:{request.query_params.urlencode()}"
        cached = cache.get(cache_key)
        if cached:
            return cached
        
        queryset = Topic.objects.select_related("subject").prefetch_related('questions').order_by("subject", "name")
        queryset = TopicFilter(request.query_params, queryset=queryset).qs

        paginator = StandardResultsPagination()
        page = paginator.paginate_queryset(queryset, request, view=self)
        serializer = TopicSerializer(page, many=True)
        response = paginator.get_paginated_response(serializer.data)
        
        cached_data = cache.get(cache_key)
        if cached_data is not None:
            return Response(cached_data)

        serializer = TopicSerializer(queryset, many=True)
        data = serializer.data
        cache.set(cache_key, data, CACHE_DURATION['subject_list'])
        return Response(data)


    @extend_schema(request=TopicSerializer, responses=TopicSerializer)
    def post(self, request):
        serializer = TopicSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            with transaction.atomic():
                topic = serializer.save()
                cache.delete_pattern('topics:list:*')
        except IntegrityError as e:
            topic_logger.error(
                "Mavzu yaratishda IntegrityError: %s, ma'lumot: %s",
                str(e), request.data, extra={"user_id": request.user.id}
            )
            return Response(
                {"detail": "Bu fan ichida shu nomli mavzu allaqachon mavjud."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        topic_logger.info(
            "Mavzu yaratildi: id=%s nomi=%r subject_id=%s foydalanuvchi_id=%s",
            topic.id, topic.name, topic.subject_id, request.user.id,
        )
        return Response(TopicSerializer(topic).data, status=status.HTTP_201_CREATED)


class TopicDetailAPIView(APIView):
    throttle_classes = [BurstUserRateThrottle]

    def get_permissions(self):
        if self.request.method in ("GET", "HEAD", "OPTIONS"):
            return [IsAuthenticated()]
        return [IsAuthenticated(), IsMentorOrAdmin()]

    def get_object(self, pk):
        try:
            return Topic.objects.select_related("subject").get(pk=pk)
        except (Topic.DoesNotExist, ValueError, TypeError):
            raise NotFound({"detail": "Bunday mavzu mavjud emas."})


    @extend_schema(responses=TopicSerializer)
    def get(self, request, pk):
        topic = self.get_object(pk)
        return Response(TopicSerializer(topic).data)


    @extend_schema(request=TopicSerializer, responses=TopicSerializer)
    def put(self, request, pk):
        return self._update(request, pk, partial=False)


    @extend_schema(request=TopicSerializer, responses=TopicSerializer)
    def patch(self, request, pk):
        return self._update(request, pk, partial=True)


    def _update(self, request, pk, *, partial):
        topic = self.get_object(pk)
        serializer = TopicSerializer(topic, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)

        try:
            with transaction.atomic():
                serializer.save()
                cache.delete_pattern('topics:list:*')
        except IntegrityError:
            return Response(
                {"detail": "Bu fan ichida shu nomli mavzu allaqachon mavjud."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        topic_logger.info(
            "Mavzu tahrirlandi: id=%s nomi=%r subject_id=%s foydalanuvchi_id=%s",
            topic.id, topic.name, topic.subject_id, request.user.id,
        )
        return Response(TopicSerializer(topic).data)


    @extend_schema(responses={204: None})
    def delete(self, request, pk):
        topic = self.get_object(pk)

        if topic.questions.exists():
            return Response(
                {
                    "detail": (
                        "Bu mavzuya bog'liq savollar mavjud. Mavzuni o'chirishdan oldin "
                        "unga tegishli barcha savollarni o'chiring yoki boshqa mavzuga ko'chiring."
                    )
                },
                status=status.HTTP_409_CONFLICT,
            )

        topic_id = topic.id
        with transaction.atomic():
            topic.delete()
            cache.delete_pattern('topics:list:*')

        topic_logger.warning(
            "Mavzu o'chirildi: id=%s foydalanuvchi_id=%s", topic_id, request.user.id,
        )
        return Response({"detail": "Mavzu muvaffaqiyatli o'chirildi"}, status=status.HTTP_204_NO_CONTENT)


class QuestionListCreateAPIView(APIView):
    throttle_classes = [BurstUserRateThrottle]

    def get_permissions(self):
        if self.request.method == "POST":
            return [IsAuthenticated(), IsMentorOrAdmin()]
        return [IsAuthenticated()]

    def select_serializer(self, user):
        if user.role in (Role.MENTOR, Role.ADMIN):
            return QuestionWriteSerializer
        return QuestionSerializer


    @extend_schema(responses=QuestionSerializer(many=True))
    def get(self, request):
        user_role = getattr(request.user, 'role', Role.STUDENT)
        cache_key = f"questions:list:{user_role}:{request.query_params.urlencode()}"
        cached = cache.get(cache_key)
        if cached:
            return cached
        
        queryset = Question.objects.select_related("topic__subject").prefetch_related().order_by("topic", "id")
        queryset = QuestionFilter(request.query_params, queryset=queryset).qs

        paginator = StandardResultsPagination()
        page = paginator.paginate_queryset(queryset, request, view=self)
        
        serializer_class = self.select_serializer(request.user)
        serializer = serializer_class(page, many=True)
        response = paginator.get_paginated_response(serializer.data)
        
        cache.set(cache_key, response.data, CACHE_DURATION['question_list'])
        return response


    @extend_schema(request=QuestionWriteSerializer, responses=QuestionWriteSerializer)
    def post(self, request):
        serializer = QuestionWriteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            with transaction.atomic():
                question = serializer.save()
                cache.delete_pattern('questions:list:*')
        except IntegrityError as e:
            question_logger.error(
                "Savol yaratishda xato: %s, ma'lumot: %s",
                str(e), request.data, extra={"user_id": request.user.id}
            )
            return Response(
                {"detail": "Savol ma'lumotlarida xato. Barcha maydonlarni tekshiring."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        question_logger.info(
            "Savol yaratildi: id=%s topic_id=%s qiyinlik=%s foydalanuvchi_id=%s",
            question.id, question.topic_id, question.difficulty, request.user.id,
        )
        return Response(QuestionWriteSerializer(question).data, status=status.HTTP_201_CREATED)


class QuestionDetailAPIView(APIView):
    throttle_classes = [BurstUserRateThrottle]

    def get_permissions(self):
        if self.request.method in ("GET", "HEAD", "OPTIONS"):
            return [IsAuthenticated()]
        return [IsAuthenticated(), IsMentorOrAdmin()]

    def select_serializer(self, user):
        from common.models import Role
        if user.role in (Role.MENTOR, Role.ADMIN):
            return QuestionWriteSerializer
        return QuestionSerializer

    def get_object(self, pk):
        try:
            return Question.objects.select_related("topic__subject").get(pk=pk)
        except (Question.DoesNotExist, ValueError, TypeError):
            raise NotFound({"detail": "Bunday savol mavjud emas."})


    @extend_schema(responses=QuestionSerializer)
    def get(self, request, pk):
        question = self.get_object(pk)
        serializer_class = self.select_serializer(request.user)
        return Response(serializer_class(question).data)


    @extend_schema(request=QuestionWriteSerializer, responses=QuestionWriteSerializer)
    def put(self, request, pk):
        return self._update(request, pk, partial=False)


    @extend_schema(request=QuestionWriteSerializer, responses=QuestionWriteSerializer)
    def patch(self, request, pk):
        return self._update(request, pk, partial=True)

    def _update(self, request, pk, *, partial):
        question = self.get_object(pk)
        serializer = QuestionWriteSerializer(question, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)

        try:
            with transaction.atomic():
                serializer.save()
                cache.delete_pattern('questions:list:*')
        except IntegrityError as e:
            question_logger.error(
                "Savol tahrirlashda xato: %s, question_id: %s",
                str(e), pk, extra={"user_id": request.user.id}
            )
            return Response(
                {"detail": "Savol ma'lumotlarida xato. Barcha maydonlarni tekshiring."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        question_logger.info(
            "Savol tahrirlandi: id=%s topic_id=%s qiyinlik=%s foydalanuvchi_id=%s",
            question.id, question.topic_id, question.difficulty, request.user.id,
        )
        return Response(QuestionWriteSerializer(question).data)


    @extend_schema(responses={204: None})
    def delete(self, request, pk):
        from testengine.models import Answer
        
        question = self.get_object(pk)

        if Answer.objects.filter(question=question).exists():
            return Response(
                {
                    "detail": (
                        "Bu savol test sessiyalarida foydalanilgan. Savol o'chirilishi mumkin emas. "
                        "Administrator bilan bog'laning."
                    )
                },
                status=status.HTTP_409_CONFLICT,
            )

        question_id = question.id
        with transaction.atomic():
            question.delete()
            cache.delete_pattern('questions:list:*')

        question_logger.warning(
            "Savol o'chirildi: id=%s foydalanuvchi_id=%s", question_id, request.user.id,
        )
        return Response({"detail": "Savol muvaffaqiyatli o'chirildi"}, status=status.HTTP_204_NO_CONTENT)