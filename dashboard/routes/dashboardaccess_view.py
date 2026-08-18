import logging

from django.db.models import Avg
from django.utils import timezone
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from drf_spectacular.utils import extend_schema

from common.permissions import IsMentorOrAdmin, IsAdmin
from common.pagination import StandardResultsPagination
from common.models import Role

from account.models import User
from billing.models import Subscription
from rating.models import Rating
from dashboard.models import MentorStudent, MentorAlert, DashboardAccess
from dashboard.routes.serializers import DashboardAccessSerializer

logger = logging.getLogger(__name__)


def _log_access(user, dashboard_type, request):
    DashboardAccess.objects.create(
        user=user,
        dashboard_type=dashboard_type,
        ip_address=request.META.get('REMOTE_ADDR'),
    )


class MentorDashboardSummaryAPIView(APIView):
    """GET /dashboard/mentor/summary/ — mentorning o'ziga biriktirilgan talabalari bo'yicha umumiy ko'rinish."""
    permission_classes = [IsMentorOrAdmin]

    @extend_schema(responses={200: dict})
    def get(self, request):
        students = MentorStudent.objects.filter(mentor=request.user, is_active=True)
        student_ids = students.values_list('student_id', flat=True)

        avg_rating = Rating.objects.filter(
            user_id__in=student_ids, period='all_time'
        ).aggregate(avg=Avg('stars'))['avg'] or 0.0

        open_alerts = MentorAlert.objects.filter(
            mentor=request.user, status=MentorAlert.Status.OPEN
        ).count()

        _log_access(request.user, DashboardAccess.DashboardType.MENTOR, request)

        return Response({
            'students_count': students.count(),
            'average_rating': round(avg_rating, 2),
            'open_alerts_count': open_alerts,
        }, status=status.HTTP_200_OK)


class AdminDashboardSummaryAPIView(APIView):
    """GET /dashboard/admin/summary/ — platforma bo'yicha jonli (real-time) statistikasi."""
    permission_classes = [IsAdmin]

    @extend_schema(responses={200: dict})
    def get(self, request):
        now = timezone.now()

        total_users = User.objects.count()
        students_count = User.objects.filter(role=Role.STUDENT).count()
        active_subscriptions = Subscription.objects.filter(
            status='active', expires_at__gt=now
        ).count()
        avg_rating = Rating.objects.filter(period='all_time').aggregate(avg=Avg('stars'))['avg'] or 0.0
        open_alerts = MentorAlert.objects.filter(status=MentorAlert.Status.OPEN).count()

        _log_access(request.user, DashboardAccess.DashboardType.ADMIN, request)

        return Response({
            'total_users': total_users,
            'students_count': students_count,
            'active_subscriptions': active_subscriptions,
            'average_rating': round(avg_rating, 2),
            'open_alerts_count': open_alerts,
        }, status=status.HTTP_200_OK)


class DashboardAccessListAPIView(APIView):
    permission_classes = [IsAdmin]
    pagination_class = StandardResultsPagination

    @extend_schema(responses=DashboardAccessSerializer(many=True))
    def get(self, request):
        queryset = DashboardAccess.objects.select_related('user').order_by('-accessed_at')
        paginator = self.pagination_class()
        page = paginator.paginate_queryset(queryset, request, view=self)
        serializer = DashboardAccessSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)
