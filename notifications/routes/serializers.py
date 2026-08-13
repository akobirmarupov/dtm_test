from rest_framework import serializers

from notifications.models import NotificationLog


class NotificationLogSerializer(serializers.ModelSerializer):
    type_display = serializers.CharField(source='get_type_display', read_only=True)

    class Meta:
        model = NotificationLog
        fields = ['id', 'type', 'type_display', 'message', 'is_read', 'read_at', 'created_at']
        read_only_fields = fields