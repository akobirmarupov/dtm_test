from django.contrib import admin
from django.utils.html import format_html

from unfold.admin import ModelAdmin

from .models import NotificationLog, Announcement


@admin.register(Announcement)
class AnnouncementAdmin(ModelAdmin):
    list_display = ("title", "sent_status", "recipients_count", "created_by", "created_at")
    list_filter = ("is_sent", "created_at")
    search_fields = ("title", "message")
    autocomplete_fields = ("created_by",)
    ordering = ("-created_at",)
    readonly_fields = ("is_sent", "sent_at", "recipients_count", "created_at")

    fieldsets = (
        ('Xabar yuborish', {
            'fields': ('title', 'message'),
            'description': "Saqlash tugmasini bosgan zahoti xabar BARCHA foydalanuvchilarga yuboriladi.",
        }),
        ('Natija', {
            'fields': ('is_sent', 'sent_at', 'recipients_count'),
            'classes': ('wide', 'extrapretty'),
        }),
    )

    def save_model(self, request, obj, form, change):
        if not change:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)

    def has_change_permission(self, request, obj=None):
        if obj and obj.is_sent:
            return False
        return super().has_change_permission(request, obj)

    def sent_status(self, obj):
        if obj.is_sent:
            return format_html('<span style="color:#22c55e;">✔ {}</span>', "Yuborildi")
        return format_html('<span style="color:#f59e0b;">⏳ {}</span>', "Kutilmoqda")
    sent_status.short_description = "Holati"


@admin.register(NotificationLog)
class NotificationLogAdmin(ModelAdmin):
    list_display = ("user", "type_badge", "short_message", "is_read", "created_at")
    list_filter = ("type", "is_read")
    search_fields = ("user__email", "message")
    autocomplete_fields = ("user",)
    ordering = ("-created_at",)
    readonly_fields = ("created_at", "read_at")

    def short_message(self, obj):
        return (obj.message[:60] + '…') if len(obj.message) > 60 else obj.message
    short_message.short_description = "Xabar"

    def type_badge(self, obj):
        colors = {'welcome': '#a855f7', 'rating_up': '#22c55e', 'announcement': '#3b82f6'}
        color = colors.get(obj.type, '#6b7280')
        return format_html(
            '<span style="background:{}; color:white; padding:2px 8px; border-radius:10px; font-size:12px;">{}</span>',
            color, obj.get_type_display(),
        )
    type_badge.short_description = "Turi"