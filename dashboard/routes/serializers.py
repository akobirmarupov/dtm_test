from rest_framework import serializers

from common.models import Role
from dashboard.models import MentorStudent, MentorAlert, AnalyticsSummary, DashboardAccess


class MentorStudentSerializer(serializers.ModelSerializer):
    mentor_email = serializers.CharField(source='mentor.email', read_only=True)
    student_email = serializers.CharField(source='student.email', read_only=True)
    student_full_name = serializers.CharField(source='student.full_name', read_only=True)

    class Meta:
        model = MentorStudent
        fields = [
            'id', 'mentor', 'mentor_email', 'student', 'student_email',
            'student_full_name', 'assigned_at', 'is_active', 'notes',
        ]
        # `mentor` va `student` yozib bo'lmaydigan bo'lishi SHART: aks holda mentor
        # o'z bog'lanishini PATCH qilib istalgan talabaga biriktirilib oladi.
        read_only_fields = [
            'id', 'mentor', 'mentor_email', 'student', 'student_email',
            'student_full_name', 'assigned_at',
        ]

    def validate(self, attrs):
        mentor = attrs.get('mentor') or getattr(self.instance, 'mentor', None)
        student = attrs.get('student') or getattr(self.instance, 'student', None)

        if mentor and mentor.role != Role.MENTOR:
            raise serializers.ValidationError({'mentor': "Bu foydalanuvchi mentor emas."})
        if student and student.role != Role.STUDENT:
            raise serializers.ValidationError({'student': "Bu foydalanuvchi talaba emas."})

        return attrs


class MentorAlertSerializer(serializers.ModelSerializer):
    alert_type_display = serializers.CharField(source='get_alert_type_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    student_email = serializers.CharField(source='student.email', read_only=True)

    class Meta:
        model = MentorAlert
        fields = [
            'id', 'mentor', 'student', 'student_email', 'alert_type', 'alert_type_display',
            'status', 'status_display', 'message', 'created_at', 'resolved_at', 'action_taken',
        ]
        read_only_fields = [
            # `status` faqat MentorAlertResolveSerializer orqali o'zgaradi —
            # aks holda ogohlantirishni darrov 'resolved' qilib yaratish mumkin.
            'id', 'mentor', 'student_email', 'alert_type_display', 'status',
            'status_display', 'created_at', 'resolved_at',
        ]

    def validate_student(self, student):
        if student.role != Role.STUDENT:
            raise serializers.ValidationError("Bu foydalanuvchi talaba emas.")
        return student


class MentorAlertResolveSerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=[MentorAlert.Status.RESOLVED, MentorAlert.Status.IGNORED])
    action_taken = serializers.CharField(required=False, allow_blank=True)


class AnalyticsSummarySerializer(serializers.ModelSerializer):
    timeframe_display = serializers.CharField(source='get_timeframe_display', read_only=True)

    class Meta:
        model = AnalyticsSummary
        fields = [
            'id', 'date', 'timeframe', 'timeframe_display', 'total_users', 'active_users',
            'new_users', 'total_tests_completed', 'average_accuracy', 'average_rating',
            'active_subscriptions', 'expired_subscriptions', 'total_revenue',
            'engagement_rate', 'retention_rate', 'last_updated',
        ]
        read_only_fields = fields


class DashboardAccessSerializer(serializers.ModelSerializer):
    user_email = serializers.CharField(source='user.email', read_only=True)
    dashboard_type_display = serializers.CharField(source='get_dashboard_type_display', read_only=True)

    class Meta:
        model = DashboardAccess
        fields = [
            'id', 'user', 'user_email', 'dashboard_type',
            'dashboard_type_display', 'accessed_at', 'ip_address',
        ]
        read_only_fields = fields
