from django.contrib import admin
from common.models import DailyFeatureUsage, Feedback


@admin.register(DailyFeatureUsage)
class DailyFeatureUsageAdmin(admin.ModelAdmin):
    list_display = ('user', 'feature', 'date', 'count')
    list_filter = ('feature', 'date')
    search_fields = ('user__email', 'user__full_name')


@admin.register(Feedback)
class FeedbackAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'type', 'rating', 'title', 'created_at')
    list_filter = ('type', 'rating', 'created_at')
    search_fields = ('title', 'message', 'user__email', 'user__full_name')
    readonly_fields = ('created_at', 'updated_at')
