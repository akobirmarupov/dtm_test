from __future__ import annotations

import logging

from django.core.cache import cache
from django.db import IntegrityError, transaction
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import serializers, status
from rest_framework.exceptions import NotFound
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from catalog.filters import GradeFilter, QuestionFilter, SubjectFilter, TopicFilter
from catalog.models import Grade, Question, Subject, Topic
from catalog.routes.serializers import (
    GradeSerializer,GradeWriteSerializer,QuestionAdminSerializer,QuestionSerializer,
    QuestionWriteSerializer,SubjectSerializer,SubjectWriteSerializer,TopicSerializer,TopicWriteSerializer,)
from common.i18n import SUPPORTED_LANGUAGES, resolve_language
from common.models import Role
from common.pagination import StandardResultsPagination
from common.permissions import IsMentorOrAdmin
from common.throttles import BurstUserRateThrottle


subject_logger = logging.getLogger('subject')
grade_logger = logging.getLogger('grade')
topic_logger = logging.getLogger('topic')
question_logger = logging.getLogger('question')


CACHE_DURATION = {
    'subject_list': 60 * 5,
    'question_list': 60 * 2,
}

LANGUAGE_PARAMETER = OpenApiParameter(
    'lang',
    str,
    description="Javob tili: uz (standart), ru, en. `X-Language` header yoki "
                "`Accept-Language` orqali ham berish mumkin.",
    enum=list(SUPPORTED_LANGUAGES),
)


def detail_response(name):
    from drf_spectacular.utils import inline_serializer
    return inline_serializer(name=name, fields={'detail': serializers.CharField()})


class LanguageAwareAPIView(APIView):
    def get_serializer_context(self, request):
        from billing.entitlements import entitlements_for_request
        return {
            'request': request,
            'language': resolve_language(request),
            'entitlements': entitlements_for_request(request),
        }

    def cache_scope(self, request) -> str:
        from billing.entitlements import entitlements_for_request
        entitlements = entitlements_for_request(request)
        return f'{entitlements.tier}:{entitlements.max_question_count}'
        


# Subject
class SubjectListCreateAPIView(LanguageAwareAPIView):
    throttle_classes = [BurstUserRateThrottle]

    def get_permissions(self):
        if self.request.method == "POST":
            return [IsAuthenticated(), IsMentorOrAdmin()]
        return [AllowAny()]

    @extend_schema(parameters=[LANGUAGE_PARAMETER],responses=SubjectSerializer(many=True),tags=['Catalog'])
    def get(self, request):
        language = resolve_language(request)
        cache_key = f"subjects:list:{language}:{request.query_params.urlencode()}"
        cached = cache.get(cache_key)
        if cached is not None:
            return Response(cached)
        from django.db.models import Count, Q as _Q

        from testengine.models import MIN_TIER

        queryset = Subject.objects.annotate(
            active_grade_count=Count(
                'grades', filter=_Q(grades__is_active=True), distinct=True
            ),
            active_topic_count=Count(
                'topics', filter=_Q(topics__is_active=True), distinct=True
            ),
            testable_topic_count=Count(
                'topics',
                filter=_Q(
                    topics__is_active=True,
                    topics__available_question_count__gte=MIN_TIER,
                ),
                distinct=True,
            ),
        ).order_by("name")
        queryset = SubjectFilter(request.query_params, queryset=queryset).qs

        paginator = StandardResultsPagination()
        page = paginator.paginate_queryset(queryset, request, view=self)
        serializer = SubjectSerializer(page, many=True, context=self.get_serializer_context(request))
        response = paginator.get_paginated_response(serializer.data)

        cache.set(cache_key, response.data, CACHE_DURATION['subject_list'])
        return response


    @extend_schema(request=SubjectWriteSerializer,responses={201: SubjectSerializer, 400: detail_response('SubjectCreateError')},tags=['Catalog'],)
    def post(self, request):
        serializer = SubjectWriteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            with transaction.atomic():
                subject = serializer.save()
        except IntegrityError as e:
            subject_logger.error(
                "Fan yaratishda IntegrityError: %s, ma'lumot: %s",
                str(e), request.data, extra={"user_id": request.user.id}
            )
            return Response(
                {"detail": "Bu nomdagi fan allaqachon mavjud."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        cache.delete_pattern('subjects:list:*')

        subject_logger.info(
            "Fan yaratildi: id=%s nomi=%r foydalanuvchi_id=%s",
            subject.id, subject.name, request.user.id,
        )
        return Response(
            SubjectSerializer(subject, context=self.get_serializer_context(request)).data,
            status=status.HTTP_201_CREATED,
        )


class SubjectDetailAPIView(LanguageAwareAPIView):
    throttle_classes = [BurstUserRateThrottle]

    def get_permissions(self):
        if self.request.method in ("GET", "HEAD", "OPTIONS"):
            return [AllowAny()]
        return [IsAuthenticated(), IsMentorOrAdmin()]

    def get_object(self, pk):
        try:
            return Subject.objects.get(pk=pk)
        except (Subject.DoesNotExist, ValueError, TypeError):
            raise NotFound("Bunday fan mavjud emas.")


    @extend_schema(parameters=[LANGUAGE_PARAMETER], responses=SubjectSerializer, tags=['Catalog'])
    def get(self, request, pk):
        subject = self.get_object(pk)
        return Response(
            SubjectSerializer(subject, context=self.get_serializer_context(request)).data
        )

    @extend_schema(request=SubjectWriteSerializer, responses=SubjectSerializer, tags=['Catalog'])
    def put(self, request, pk):
        return self._update(request, pk, partial=False)

    @extend_schema(request=SubjectWriteSerializer, responses=SubjectSerializer, tags=['Catalog'])
    def patch(self, request, pk):
        return self._update(request, pk, partial=True)

    def _update(self, request, pk, *, partial):
        subject = self.get_object(pk)
        serializer = SubjectWriteSerializer(subject, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)

        try:
            with transaction.atomic():
                subject = serializer.save()
        except IntegrityError:
            return Response(
                {"detail": "Bu nomdagi fan allaqachon mavjud."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        cache.delete_pattern('subjects:list:*')

        subject_logger.info(
            "Fan tahrirlandi: id=%s nomi=%r foydalanuvchi_id=%s",
            subject.id, subject.name, request.user.id,
        )
        return Response(
            SubjectSerializer(subject, context=self.get_serializer_context(request)).data
        )


    @extend_schema(responses={204: None, 409: detail_response('SubjectDeleteConflict')}, tags=['Catalog'])
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


# Grade (Sinf / Kitob)
class GradeListCreateAPIView(LanguageAwareAPIView):
    throttle_classes = [BurstUserRateThrottle]

    def get_permissions(self):
        if self.request.method == "POST":
            return [IsAuthenticated(), IsMentorOrAdmin()]
        return [AllowAny()]

    @extend_schema(
        parameters=[LANGUAGE_PARAMETER],
        responses=GradeSerializer(many=True),
        tags=['Catalog'],
    )
    def get(self, request):
        from django.db.models import Count, Q as _Q

        from testengine.models import MIN_TIER

        language = resolve_language(request)
        cache_key = f"grades:list:{language}:{request.query_params.urlencode()}"
        cached = cache.get(cache_key)
        if cached is not None:
            return Response(cached)

        queryset = Grade.objects.select_related('subject').annotate(
            active_topic_count=Count(
                'topics', filter=_Q(topics__is_active=True), distinct=True
            ),
            testable_topic_count=Count(
                'topics',
                filter=_Q(
                    topics__is_active=True,
                    topics__available_question_count__gte=MIN_TIER,
                ),
                distinct=True,
            ),
        ).order_by('subject_id', 'order', 'id')
        queryset = GradeFilter(request.query_params, queryset=queryset).qs

        paginator = StandardResultsPagination()
        page = paginator.paginate_queryset(queryset, request, view=self)
        serializer = GradeSerializer(page, many=True, context=self.get_serializer_context(request))
        response = paginator.get_paginated_response(serializer.data)

        cache.set(cache_key, response.data, CACHE_DURATION['subject_list'])
        return response

    @extend_schema(request=GradeWriteSerializer,responses={201: GradeSerializer, 400: detail_response('GradeCreateError')},tags=['Catalog'],)
    def post(self, request):
        serializer = GradeWriteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            with transaction.atomic():
                grade = serializer.save()
        except IntegrityError as e:
            grade_logger.error(
                "Sinf yaratishda IntegrityError: %s, ma'lumot: %s",
                str(e), request.data, extra={"user_id": request.user.id}
            )
            return Response(
                {"detail": "Bu fan ichida shu nomli sinf/kitob allaqachon mavjud."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        cache.delete_pattern('grades:list:*')
        cache.delete_pattern('subjects:list:*')

        grade_logger.info(
            "Sinf yaratildi: id=%s nomi=%r subject_id=%s foydalanuvchi_id=%s",
            grade.id, grade.name, grade.subject_id, request.user.id,
        )
        return Response(
            GradeSerializer(grade, context=self.get_serializer_context(request)).data,
            status=status.HTTP_201_CREATED,
        )


class GradeDetailAPIView(LanguageAwareAPIView):
    throttle_classes = [BurstUserRateThrottle]

    def get_permissions(self):
        if self.request.method in ("GET", "HEAD", "OPTIONS"):
            return [AllowAny()]
        return [IsAuthenticated(), IsMentorOrAdmin()]

    def get_object(self, pk):
        try:
            return Grade.objects.select_related('subject').get(pk=pk)
        except (Grade.DoesNotExist, ValueError, TypeError):
            raise NotFound("Bunday sinf/kitob mavjud emas.")

    @extend_schema(parameters=[LANGUAGE_PARAMETER], responses=GradeSerializer, tags=['Catalog'])
    def get(self, request, pk):
        grade = self.get_object(pk)
        return Response(
            GradeSerializer(grade, context=self.get_serializer_context(request)).data
        )

    @extend_schema(request=GradeWriteSerializer, responses=GradeSerializer, tags=['Catalog'])
    def put(self, request, pk):
        return self._update(request, pk, partial=False)

    @extend_schema(request=GradeWriteSerializer, responses=GradeSerializer, tags=['Catalog'])
    def patch(self, request, pk):
        return self._update(request, pk, partial=True)

    def _update(self, request, pk, *, partial):
        grade = self.get_object(pk)
        serializer = GradeWriteSerializer(grade, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)

        try:
            with transaction.atomic():
                grade = serializer.save()
        except IntegrityError:
            return Response(
                {"detail": "Bu fan ichida shu nomli sinf/kitob allaqachon mavjud."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        cache.delete_pattern('grades:list:*')
        cache.delete_pattern('topics:list:*')

        grade_logger.info(
            "Sinf tahrirlandi: id=%s nomi=%r foydalanuvchi_id=%s",
            grade.id, grade.name, request.user.id,
        )
        return Response(
            GradeSerializer(grade, context=self.get_serializer_context(request)).data
        )

    @extend_schema(
        responses={204: None, 409: detail_response('GradeDeleteConflict')}, tags=['Catalog']
    )
    def delete(self, request, pk):
        grade = self.get_object(pk)

        if grade.topics.exists():
            return Response(
                {
                    "detail": (
                        "Bu sinf/kitobga bog'liq mavzular mavjud. O'chirishdan oldin "
                        "mavzularni boshqa sinfga ko'chiring yoki o'chiring."
                    )
                },
                status=status.HTTP_409_CONFLICT,
            )

        grade_id = grade.id
        with transaction.atomic():
            grade.delete()

        cache.delete_pattern('grades:list:*')
        cache.delete_pattern('subjects:list:*')

        grade_logger.warning(
            "Sinf o'chirildi: id=%s foydalanuvchi_id=%s", grade_id, request.user.id,
        )
        return Response(status=status.HTTP_204_NO_CONTENT)


# Topic
class TopicListCreateAPIView(LanguageAwareAPIView):
    throttle_classes = [BurstUserRateThrottle]

    def get_permissions(self):
        if self.request.method == "POST":
            return [IsAuthenticated(), IsMentorOrAdmin()]
        return [AllowAny()]


    @extend_schema(parameters=[LANGUAGE_PARAMETER],responses=TopicSerializer(many=True),tags=['Catalog'])
    def get(self, request):
        language = resolve_language(request)
        cache_key = (
            f"topics:list:{language}:{self.cache_scope(request)}:"
            f"{request.query_params.urlencode()}"
        )
        cached = cache.get(cache_key)
        if cached is not None:
            return Response(cached)

        queryset = (
            Topic.objects
            .select_related("subject", "grade")
            .order_by("subject_id", "grade__order", "order", "name")
        )
        queryset = TopicFilter(request.query_params, queryset=queryset).qs

        paginator = StandardResultsPagination()
        page = paginator.paginate_queryset(queryset, request, view=self)
        serializer = TopicSerializer(page, many=True, context=self.get_serializer_context(request))
        response = paginator.get_paginated_response(serializer.data)

        cache.set(cache_key, response.data, CACHE_DURATION['subject_list'])
        return response

    @extend_schema(request=TopicWriteSerializer,responses={201: TopicSerializer, 400: detail_response('TopicCreateError')},tags=['Catalog'],)
    def post(self, request):
        serializer = TopicWriteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            with transaction.atomic():
                topic = serializer.save()
        except IntegrityError as e:
            topic_logger.error(
                "Mavzu yaratishda IntegrityError: %s, ma'lumot: %s",
                str(e), request.data, extra={"user_id": request.user.id}
            )
            return Response(
                {"detail": "Bu sinf/kitob ichida shu nomli mavzu allaqachon mavjud."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        cache.delete_pattern('topics:list:*')

        topic_logger.info(
            "Mavzu yaratildi: id=%s nomi=%r grade_id=%s foydalanuvchi_id=%s",
            topic.id, topic.name, topic.grade_id, request.user.id,
        )
        return Response(
            TopicSerializer(topic, context=self.get_serializer_context(request)).data,
            status=status.HTTP_201_CREATED,
        )


class TopicDetailAPIView(LanguageAwareAPIView):
    throttle_classes = [BurstUserRateThrottle]

    def get_permissions(self):
        if self.request.method in ("GET", "HEAD", "OPTIONS"):
            return [AllowAny()]
        return [IsAuthenticated(), IsMentorOrAdmin()]

    def get_object(self, pk):
        try:
            return Topic.objects.select_related("subject", "grade").get(pk=pk)
        except (Topic.DoesNotExist, ValueError, TypeError):
            raise NotFound("Bunday mavzu mavjud emas.")

    @extend_schema(parameters=[LANGUAGE_PARAMETER], responses=TopicSerializer, tags=['Catalog'])
    def get(self, request, pk):
        topic = self.get_object(pk)
        return Response(
            TopicSerializer(topic, context=self.get_serializer_context(request)).data
        )

    @extend_schema(request=TopicWriteSerializer, responses=TopicSerializer, tags=['Catalog'])
    def put(self, request, pk):
        return self._update(request, pk, partial=False)

    @extend_schema(request=TopicWriteSerializer, responses=TopicSerializer, tags=['Catalog'])
    def patch(self, request, pk):
        return self._update(request, pk, partial=True)

    def _update(self, request, pk, *, partial):
        topic = self.get_object(pk)
        serializer = TopicWriteSerializer(topic, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)

        try:
            with transaction.atomic():
                topic = serializer.save()
        except IntegrityError:
            return Response(
                {"detail": "Bu sinf/kitob ichida shu nomli mavzu allaqachon mavjud."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        cache.delete_pattern('topics:list:*')

        topic_logger.info(
            "Mavzu tahrirlandi: id=%s nomi=%r grade_id=%s foydalanuvchi_id=%s",
            topic.id, topic.name, topic.grade_id, request.user.id,
        )
        return Response(
            TopicSerializer(topic, context=self.get_serializer_context(request)).data
        )

    @extend_schema(responses={204: None, 409: detail_response('TopicDeleteConflict')}, tags=['Catalog'])
    def delete(self, request, pk):
        topic = self.get_object(pk)

        if topic.questions.exists():
            return Response(
                {
                    "detail": (
                        "Bu mavzuga bog'liq savollar mavjud. Mavzuni o'chirishdan oldin "
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
        return Response(status=status.HTTP_204_NO_CONTENT)



# Question
class QuestionListCreateAPIView(LanguageAwareAPIView):
    throttle_classes = [BurstUserRateThrottle]
    parser_classes = [JSONParser, MultiPartParser, FormParser]

    def get_permissions(self):
        if self.request.method == "POST":
            return [IsAuthenticated(), IsMentorOrAdmin()]
        return [AllowAny()]

    def select_serializer(self, user):
        if getattr(user, 'role', None) in (Role.MENTOR, Role.ADMIN):
            return QuestionAdminSerializer
        return QuestionSerializer

    @extend_schema(
        parameters=[LANGUAGE_PARAMETER],
        responses=QuestionSerializer(many=True),
        tags=['Catalog'],
    )
    def get(self, request):
        user_role = getattr(request.user, 'role', Role.STUDENT)
        language = resolve_language(request)
        cache_key = (
            f"questions:list:{user_role}:{language}:{request.query_params.urlencode()}"
        )
        cached = cache.get(cache_key)
        if cached is not None:
            return Response(cached)

        queryset = Question.objects.select_related(
            "topic__subject", "topic__grade"
        ).order_by("topic", "id")
        if user_role not in (Role.MENTOR, Role.ADMIN):
            queryset = queryset.available()
        queryset = QuestionFilter(request.query_params, queryset=queryset).qs

        paginator = StandardResultsPagination()
        page = paginator.paginate_queryset(queryset, request, view=self)

        serializer_class = self.select_serializer(request.user)
        serializer = serializer_class(
            page, many=True, context=self.get_serializer_context(request)
        )
        response = paginator.get_paginated_response(serializer.data)

        cache.set(cache_key, response.data, CACHE_DURATION['question_list'])
        return response

    @extend_schema(
        request={
            'multipart/form-data': QuestionWriteSerializer,
            'application/json': QuestionWriteSerializer,
        },
        responses={201: QuestionAdminSerializer, 400: detail_response('QuestionCreateError')},tags=['Catalog'])
    def post(self, request):
        serializer = QuestionWriteSerializer(
            data=request.data, context=self.get_serializer_context(request)
        )
        serializer.is_valid(raise_exception=True)

        try:
            with transaction.atomic():
                question = serializer.save()
        except IntegrityError as e:
            question_logger.error(
                "Savol yaratishda xato: %s, ma'lumot: %s",
                str(e), request.data, extra={"user_id": request.user.id}
            )
            return Response(
                {"detail": "Savol ma'lumotlarida xato. Barcha maydonlarni tekshiring."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        cache.delete_pattern('questions:list:*')
        cache.delete_pattern('topics:list:*')
        cache.delete_pattern('subjects:list:*')

        question_logger.info(
            "Savol yaratildi: id=%s topic_id=%s qiyinlik=%s rasm=%s foydalanuvchi_id=%s",
            question.id, question.topic_id, question.difficulty,
            bool(question.image), request.user.id,
        )
        return Response(
            QuestionAdminSerializer(question, context=self.get_serializer_context(request)).data,
            status=status.HTTP_201_CREATED,
        )


class QuestionDetailAPIView(LanguageAwareAPIView):
    throttle_classes = [BurstUserRateThrottle]
    parser_classes = [JSONParser, MultiPartParser, FormParser]

    def get_permissions(self):
        if self.request.method in ("GET", "HEAD", "OPTIONS"):
            return [AllowAny()]
        return [IsAuthenticated(), IsMentorOrAdmin()]

    def select_serializer(self, user):
        if getattr(user, 'role', None) in (Role.MENTOR, Role.ADMIN):
            return QuestionAdminSerializer
        return QuestionSerializer

    def get_object(self, pk, user=None):
        queryset = Question.objects.select_related("topic__subject", "topic__grade")
        if user is not None and getattr(user, 'role', None) not in (Role.MENTOR, Role.ADMIN):
            queryset = queryset.available()
        try:
            return queryset.get(pk=pk)
        except (Question.DoesNotExist, ValueError, TypeError):
            raise NotFound("Bunday savol mavjud emas.")

    @extend_schema(parameters=[LANGUAGE_PARAMETER], responses=QuestionSerializer, tags=['Catalog'])
    def get(self, request, pk):
        question = self.get_object(pk, user=request.user)
        serializer_class = self.select_serializer(request.user)
        return Response(
            serializer_class(question, context=self.get_serializer_context(request)).data
        )

    @extend_schema(
        request={
            'multipart/form-data': QuestionWriteSerializer,
            'application/json': QuestionWriteSerializer,
        },
        responses=QuestionAdminSerializer,
        tags=['Catalog'],
    )
    def put(self, request, pk):
        return self._update(request, pk, partial=False)

    @extend_schema(
        request={
            'multipart/form-data': QuestionWriteSerializer,
            'application/json': QuestionWriteSerializer,
        },
        responses=QuestionAdminSerializer,
        tags=['Catalog'],
        description="Savolni qisman tahrirlash. Rasmni olib tashlash uchun "
                    "`image: null` yuboring.",
    )
    def patch(self, request, pk):
        return self._update(request, pk, partial=True)

    def _update(self, request, pk, *, partial):
        question = self.get_object(pk)
        old_image = question.image.name if question.image else None

        serializer = QuestionWriteSerializer(
            question, data=request.data, partial=partial,
            context=self.get_serializer_context(request),
        )
        serializer.is_valid(raise_exception=True)

        try:
            with transaction.atomic():
                question = serializer.save()
        except IntegrityError as e:
            question_logger.error(
                "Savol tahrirlashda xato: %s, question_id: %s",
                str(e), pk, extra={"user_id": request.user.id}
            )
            return Response(
                {"detail": "Savol ma'lumotlarida xato. Barcha maydonlarni tekshiring."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        cache.delete_pattern('questions:list:*')
        cache.delete_pattern('topics:list:*')

        new_image = question.image.name if question.image else None
        if old_image and old_image != new_image:
            question.image.storage.delete(old_image)

        question_logger.info(
            "Savol tahrirlandi: id=%s topic_id=%s qiyinlik=%s rasm=%s foydalanuvchi_id=%s",
            question.id, question.topic_id, question.difficulty,
            bool(question.image), request.user.id,
        )
        return Response(
            QuestionAdminSerializer(question, context=self.get_serializer_context(request)).data
        )

    @extend_schema(responses={204: None, 409: detail_response('QuestionDeleteConflict')}, tags=['Catalog'])
    def delete(self, request, pk):
        from testengine.models import Answer, SessionQuestion

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

        if SessionQuestion.objects.filter(
            question=question, session__finished_at__isnull=True
        ).exists():
            return Response(
                {
                    "detail": (
                        "Bu savol hozir davom etayotgan test sessiyalariga biriktirilgan. "
                        "Sessiyalar yakunlangandan keyin o'chirishingiz mumkin."
                    )
                },
                status=status.HTTP_409_CONFLICT,
            )

        question_id = question.id
        image_name = question.image.name if question.image else None
        storage = question.image.storage if question.image else None

        with transaction.atomic():
            question.delete()

        cache.delete_pattern('questions:list:*')

        if image_name and storage:
            storage.delete(image_name)

        question_logger.warning(
            "Savol o'chirildi: id=%s foydalanuvchi_id=%s", question_id, request.user.id,
        )
        return Response(status=status.HTTP_204_NO_CONTENT)
