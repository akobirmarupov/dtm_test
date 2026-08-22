import logging

from django.utils import timezone
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.generics import get_object_or_404
from rest_framework.exceptions import PermissionDenied
from drf_spectacular.utils import extend_schema

from common.permissions import IsMentorOrAdmin
from common.pagination import StandardResultsPagination
from common.models import Role

from dashboard.models import MentorAlert, MentorStudent
from dashboard.routes.serializers import MentorAlertSerializer, MentorAlertResolveSerializer

logger = logging.getLogger(__name__)


class MentorAlertListCreateAPIView(APIView):
    permission_classes = [IsMentorOrAdmin]
    pagination_class = StandardResultsPagination

    @extend_schema(responses=MentorAlertSerializer(many=True))
    def get(self, request):
        queryset = MentorAlert.objects.select_related('mentor', 'student')
        if request.user.role == Role.MENTOR:
            queryset = queryset.filter(mentor=request.user)

        status_param = request.query_params.get('status')
        if status_param:
            queryset = queryset.filter(status=status_param)

        queryset = queryset.order_by('-created_at')

        paginator = self.pagination_class()
        page = paginator.paginate_queryset(queryset, request, view=self)
        serializer = MentorAlertSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)

    @extend_schema(request=MentorAlertSerializer, responses={201: MentorAlertSerializer})
    def post(self, request):
        serializer = MentorAlertSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # Mentor faqat o'ziga biriktirilgan talaba uchun ogohlantirish ocha oladi.
        student = serializer.validated_data['student']
        if request.user.role == Role.MENTOR and not MentorStudent.objects.filter(
            mentor=request.user, student=student, is_active=True
        ).exists():
            raise PermissionDenied("Bu talaba sizga biriktirilmagan")

        alert = serializer.save(mentor=request.user)

        logger.info(
            'MentorAlert yaratildi: mentor_id=%s student_id=%s type=%s',
            request.user.id, alert.student_id, alert.alert_type,
        )

        return Response(MentorAlertSerializer(alert).data, status=status.HTTP_201_CREATED)


class MentorAlertResolveAPIView(APIView):
    permission_classes = [IsMentorOrAdmin]

    @extend_schema(request=MentorAlertResolveSerializer, responses=MentorAlertSerializer)
    def patch(self, request, pk):
        alert = get_object_or_404(MentorAlert, pk=pk)
        if request.user.role == Role.MENTOR and alert.mentor_id != request.user.id:
            raise PermissionDenied("Bu ogohlantirish sizga tegishli emas")

        serializer = MentorAlertResolveSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        alert.status = serializer.validated_data['status']
        alert.action_taken = serializer.validated_data.get('action_taken', alert.action_taken)
        alert.resolved_at = timezone.now()
        alert.save(update_fields=['status', 'action_taken', 'resolved_at'])

        logger.info(
            'MentorAlert hal qilindi: id=%s status=%s by=%s',
            alert.id, alert.status, request.user.id,
        )

        return Response(MentorAlertSerializer(alert).data, status=status.HTTP_200_OK)
