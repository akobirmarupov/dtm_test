from django.urls import path

from dashboard.routes.mentorstudent_view import (
    MentorStudentListCreateAPIView,
    MentorStudentDetailAPIView,
    MentorStudentStatsAPIView,
)
from dashboard.routes.mentoralert_view import MentorAlertListCreateAPIView, MentorAlertResolveAPIView
from dashboard.routes.analyticssummary_view import AnalyticsSummaryListAPIView, AnalyticsSummaryDetailAPIView
from dashboard.routes.dashboardaccess_view import (
    MentorDashboardSummaryAPIView,
    AdminDashboardSummaryAPIView,
    DashboardAccessListAPIView,
)

urlpatterns = [
    # MentorStudent
    path('mentor/students/', MentorStudentListCreateAPIView.as_view(), name='mentor-student-list'),
    path('mentor/students/<int:pk>/', MentorStudentDetailAPIView.as_view(), name='mentor-student-detail'),
    path('mentor/students/<int:student_id>/stats/', MentorStudentStatsAPIView.as_view(), name='mentor-student-stats'),

    # MentorAlert
    path('mentor/alerts/', MentorAlertListCreateAPIView.as_view(), name='mentor-alert-list'),
    path('mentor/alerts/<int:pk>/resolve/', MentorAlertResolveAPIView.as_view(), name='mentor-alert-resolve'),

    # Dashboard summary (jonli statistikasi + DashboardAccess logi)
    path('mentor/summary/', MentorDashboardSummaryAPIView.as_view(), name='mentor-dashboard-summary'),
    path('admin/summary/', AdminDashboardSummaryAPIView.as_view(), name='admin-dashboard-summary'),

    # AnalyticsSummary
    path('admin/analytics/', AnalyticsSummaryListAPIView.as_view(), name='analytics-summary-list'),
    path('admin/analytics/<int:pk>/', AnalyticsSummaryDetailAPIView.as_view(), name='analytics-summary-detail'),

    # DashboardAccess
    path('admin/access-log/', DashboardAccessListAPIView.as_view(), name='dashboard-access-log'),
]
