import logging

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.generics import get_object_or_404
from rest_framework.exceptions import NotFound
from drf_spectacular.utils import extend_schema

from common.permissions import IsMentorOrAdmin, IsAdmin
from common.models import Role

from dashboard.models import MentorStudent
from dashboard.routes.serializers import MentorStudentSerializer
from rating.models import Rating, TopicRating, SubjectRating
from rating.routes.serializers import RatingSerializer, TopicRatingSerializer, SubjectRatingSerializer

logger = logging.getLogger(__name__)


class MentorStudentListCreateAPIView(APIView):
    def get_permissions(self):
        if self.request.method == 'POST':
            return [IsAdmin()]
        return [IsMentorOrAdmin()]

    @extend_schema(responses=MentorStudentSerializer(many=True))
    def get(self, request):
        queryset = MentorStudent.objects.select_related('mentor', 'student')
        if request.user.role == Role.MENTOR:
            queryset = queryset.filter(mentor=request.user)
        queryset = queryset.order_by('-assigned_at')
        return Response(MentorStudentSerializer(queryset, many=True).data, status=status.HTTP_200_OK)

    @extend_schema(request=MentorStudentSerializer, responses={201: MentorStudentSerializer})
    def post(self, request):
        serializer = MentorStudentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        link = serializer.save()

        logger.info(
            'MentorStudent yaratildi: mentor_id=%s student_id=%s by=%s',
            link.mentor_id, link.student_id, request.user.id,
        )

        return Response(MentorStudentSerializer(link).data, status=status.HTTP_201_CREATED)


class MentorStudentDetailAPIView(APIView):
    permission_classes = [IsMentorOrAdmin]

    def get_object(self, pk, request):
        link = get_object_or_404(MentorStudent, pk=pk)
        if request.user.role == Role.MENTOR and link.mentor_id != request.user.id:
            raise NotFound("Bog'lanish topilmadi")
        return link

    @extend_schema(request=MentorStudentSerializer, responses=MentorStudentSerializer)
    def patch(self, request, pk):
        link = self.get_object(pk, request)
        serializer = MentorStudentSerializer(link, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        link = serializer.save()

        logger.info('MentorStudent yangilandi: id=%s by=%s', link.id, request.user.id)

        return Response(MentorStudentSerializer(link).data, status=status.HTTP_200_OK)


class MentorStudentStatsAPIView(APIView):
    """
    GET /dashboard/mentor/students/{student_id}/stats/

    Mentorning o'ziga biriktirilgan (yoki admin uchun istalgan) talabaning
    umumiy, fan va mavzu bo'yicha reytingini ko'rsatadi.
    """
    permission_classes = [IsMentorOrAdmin]

    @extend_schema(responses={200: dict})
    def get(self, request, student_id):
        links = MentorStudent.objects.filter(student_id=student_id, is_active=True)
        if request.user.role == Role.MENTOR:
            links = links.filter(mentor=request.user)

        if not links.exists():
            raise NotFound("Bu talaba sizga biriktirilmagan")

        overall = Rating.objects.filter(user_id=student_id, period='all_time').first()
        subjects = SubjectRating.objects.filter(user_id=student_id).select_related('subject').order_by('stars')
        weakest_topics = TopicRating.objects.filter(user_id=student_id).select_related('topic').order_by('stars')[:5]

        return Response({
            'overall_rating': RatingSerializer(overall).data if overall else None,
            'subjects': SubjectRatingSerializer(subjects, many=True).data,
            'weakest_topics': TopicRatingSerializer(weakest_topics, many=True).data,
        }, status=status.HTTP_200_OK)
