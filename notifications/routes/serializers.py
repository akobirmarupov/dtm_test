from rest_framework import serializers

from notifications.models import NotificationLog, Announcement


class NotificationLogSerializer(serializers.ModelSerializer):
    type_display = serializers.CharField(source='get_type_display', read_only=True)

    class Meta:
        model = NotificationLog
        fields = ['id', 'type', 'type_display', 'message', 'is_read', 'read_at', 'created_at']
        read_only_fields = fields


class AnnouncementSerializer(serializers.ModelSerializer):
    """
    POST /notifications/announcements/ — admin oddiy matnli xabar yozadi,
    u barcha faol talabalarga NotificationLog sifatida yuboriladi.
    """
    created_by_email = serializers.CharField(source='created_by.email', read_only=True)

    class Meta:
        model = Announcement
        fields = [
            'id', 'title', 'message', 'created_by', 'created_by_email',
            'is_sent', 'sent_at', 'recipients_count', 'created_at',
        ]
        read_only_fields = ['id', 'created_by', 'created_by_email', 'is_sent', 'sent_at', 'recipients_count', 'created_at']