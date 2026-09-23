from rest_framework import serializers

from account.models import User
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


class MentorStudentCreateSerializer(MentorStudentSerializer):
    """Faqat YARATISH uchun: bu yerda mentor va talaba yoziladigan bo'ladi.

    Asosiy serializerda ular ataylab read-only — aks holda mentor PATCH
    orqali o'z bog'lanishini istalgan talabaga ko'chirib olardi. Lekin
    yaratishda ularni kiritish kerak, shuning uchun alohida serializer.
    """

    class Meta(MentorStudentSerializer.Meta):
        read_only_fields = [
            'id', 'mentor_email', 'student_email', 'student_full_name', 'assigned_at',
        ]

    def validate_mentor(self, value):
        if value is None:
            raise serializers.ValidationError("Mentor tanlanmagan.")
        return value

    def validate_student(self, value):
        if value is None:
            raise serializers.ValidationError("Talaba tanlanmagan.")
        return value


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


class AdminUserSerializer(serializers.ModelSerializer):
    """Admin paneldagi foydalanuvchi qatori."""

    is_blocked = serializers.SerializerMethodField()
    blocked_by_email = serializers.CharField(source='blocked_by.email', read_only=True, default=None)

    class Meta:
        model = User
        fields = [
            'id', 'email', 'full_name', 'role', 'avatar_url', 'xp_total',
            'is_active', 'is_blocked', 'blocked_at', 'blocked_by_email',
            'block_reason', 'last_login', 'created_at',
        ]
        read_only_fields = fields

    def get_is_blocked(self, obj) -> bool:
        return not obj.is_active


class AdminUserDetailSerializer(serializers.Serializer):
    """Bitta foydalanuvchi kartasi — ro'yxatdagi maydonlar + tafsilotlar."""

    id = serializers.IntegerField()
    email = serializers.EmailField()
    full_name = serializers.CharField(allow_blank=True)
    role = serializers.CharField()
    avatar_url = serializers.CharField(allow_blank=True)
    xp_total = serializers.IntegerField()
    is_active = serializers.BooleanField()
    is_blocked = serializers.BooleanField()
    blocked_at = serializers.DateTimeField(allow_null=True)
    blocked_by_email = serializers.CharField(allow_null=True)
    block_reason = serializers.CharField(allow_blank=True)
    last_login = serializers.DateTimeField(allow_null=True)
    created_at = serializers.DateTimeField()

    phone_number = serializers.CharField(allow_blank=True)
    telegram_username = serializers.CharField(allow_blank=True)
    region = serializers.CharField(allow_blank=True)
    target_major = serializers.CharField(allow_blank=True)
    language = serializers.CharField(allow_blank=True)

    subscription = serializers.DictField(allow_null=True)
    entitlements = serializers.DictField()
    sessions_total = serializers.IntegerField()
    sessions_finished = serializers.IntegerField()
    last_test_at = serializers.DateTimeField(allow_null=True)
    devices_count = serializers.IntegerField()
