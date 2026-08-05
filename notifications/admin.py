from django.contrib import admin

from unfold.admin import ModelAdmin

from .models import NotificationLog, PushToken, ReminderSchedule


@admin.register(NotificationLog)
class NotificationLogAdmin(ModelAdmin):
    list_display = ("user", "channel", "status", "sent_at", "created_at")
    list_filter = ("channel", "status")
    search_fields = ("user__email", "message")
    autocomplete_fields = ("user",)
    ordering = ("-created_at",)


@admin.register(PushToken)
class PushTokenAdmin(ModelAdmin):
    list_display = ("user", "device_type", "is_active", "created_at")
    list_filter = ("device_type", "is_active")
    search_fields = ("user__email", "token")
    autocomplete_fields = ("user",)
    ordering = ("-created_at",)


@admin.register(ReminderSchedule)
class ReminderScheduleAdmin(ModelAdmin):
    list_display = ("user", "reminder_type", "scheduled_at", "is_sent")
    list_filter = ("reminder_type", "is_sent")
    search_fields = ("user__email",)
    autocomplete_fields = ("user",)
    ordering = ("scheduled_at",)
