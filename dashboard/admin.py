from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models import MentorStudent, MentorAlert, AnalyticsSummary, DashboardAccess


@admin.register(MentorStudent)
class MentorStudentAdmin(admin.ModelAdmin):
    list_display = (
        'mentor_email',
        'student_email',
        'status_display',
        'assigned_at'
    )
    list_filter = ('is_active', 'assigned_at')
    search_fields = ('mentor__email', 'student__email', 'mentor__full_name', 'student__full_name')
    readonly_fields = ('created_at', 'updated_at', 'assigned_at')
    
    fieldsets = (
        ('Bog\'lanish', {
            'fields': ('mentor', 'student', 'is_active')
        }),
        ('Izohlar', {
            'fields': ('notes',)
        }),
        ('Vaqt', {
            'fields': ('assigned_at', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def mentor_email(self, obj):
        return obj.mentor.email
    mentor_email.short_description = 'Mentor'
    
    def student_email(self, obj):
        return obj.student.email
    student_email.short_description = 'Talaba'
    
    def status_display(self, obj):
        if obj.is_active:
            return mark_safe(
                '<span style="background-color: #27ae60; color: white; padding: 5px 10px; border-radius: 3px;">✓ Faol</span>'
            )
        else:
            return mark_safe(
                '<span style="background-color: #e74c3c; color: white; padding: 5px 10px; border-radius: 3px;">✗ Nofaol</span>'
            )
    status_display.short_description = 'Holati'
    
    ordering = ['-assigned_at']


@admin.register(MentorAlert)
class MentorAlertAdmin(admin.ModelAdmin):
    list_display = (
        'mentor_email',
        'student_email',
        'alert_type_display',
        'status_display',
        'created_at'
    )
    list_filter = ('alert_type', 'status', 'created_at')
    search_fields = ('mentor__email', 'student__email')
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        ('Bog\'lanishlar', {
            'fields': ('mentor', 'student', 'alert_type')
        }),
        ('Xabar', {
            'fields': ('message', 'status')
        }),
        ('Qayta ishlash', {
            'fields': ('action_taken', 'resolved_at'),
            'classes': ('collapse',)
        }),
        ('Vaqt', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def mentor_email(self, obj):
        return obj.mentor.email
    mentor_email.short_description = 'Mentor'
    
    def student_email(self, obj):
        return obj.student.email
    student_email.short_description = 'Talaba'
    
    def alert_type_display(self, obj):
        colors = {
            'low_performance': '#f39c12',
            'no_activity': '#e74c3c',
            'low_rating': '#e67e22',
            'streak_broken': '#9b59b6',
            'needs_review': '#3498db'
        }
        color = colors.get(obj.alert_type, '#95a5a6')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 5px 10px; border-radius: 3px;">{}</span>',
            color,
            obj.get_alert_type_display()
        )
    alert_type_display.short_description = 'Turi'
    
    def status_display(self, obj):
        colors = {
            'open': '#3498db',
            'resolved': '#27ae60',
            'ignored': '#95a5a6'
        }
        color = colors.get(obj.status, '#95a5a6')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 5px 10px; border-radius: 3px;">{}</span>',
            color,
            obj.get_status_display()
        )
    status_display.short_description = 'Holati'
    
    ordering = ['-created_at']


@admin.register(AnalyticsSummary)
class AnalyticsSummaryAdmin(admin.ModelAdmin):
    list_display = (
        'date',
        'timeframe_display',
        'total_users_display',
        'active_users_display',
        'tests_completed_display',
        'average_rating_display'
    )
    list_filter = ('timeframe', 'date')
    readonly_fields = ('created_at', 'updated_at', 'last_updated')
    
    fieldsets = (
        ('Davr', {
            'fields': ('date', 'timeframe')
        }),
        ('Foydalanuvchilar', {
            'fields': ('total_users', 'active_users', 'new_users')
        }),
        ('Testlar va Reyting', {
            'fields': ('total_tests_completed', 'average_accuracy', 'average_rating')
        }),
        ('Obunalar', {
            'fields': ('active_subscriptions', 'expired_subscriptions', 'total_revenue')
        }),
        ('Ishtirok va Qaytishi', {
            'fields': ('engagement_rate', 'retention_rate', 'top_subject_id')
        }),
        ('Vaqt', {
            'fields': ('last_updated', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def timeframe_display(self, obj):
        colors = {
            'daily': '#3498db',
            'weekly': '#2ecc71',
            'monthly': '#f39c12',
            'yearly': '#e74c3c'
        }
        color = colors.get(obj.timeframe, '#95a5a6')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 5px 10px; border-radius: 3px;">{}</span>',
            color,
            obj.get_timeframe_display()
        )
    timeframe_display.short_description = 'Davr'
    
    def total_users_display(self, obj):
        return format_html(
            '<span style="font-weight: bold; color: #2c3e50;">{}</span>',
            obj.total_users
        )
    total_users_display.short_description = 'Jami Foydalanuvchilar'
    
    def active_users_display(self, obj):
        if obj.total_users > 0:
            percentage = (obj.active_users / obj.total_users) * 100
            color = '#27ae60' if percentage >= 50 else '#f39c12' if percentage >= 30 else '#e74c3c'
            percentage_text = f'{percentage:.1f}%'
            return format_html(
                '<span style="color: {}; font-weight: bold;">{} ({})</span>',
                color,
                obj.active_users,
                percentage_text
            )
        return obj.active_users
    active_users_display.short_description = 'Faol Foydalanuvchilar'
    
    def tests_completed_display(self, obj):
        return format_html(
            '<span style="font-weight: bold; color: #2980b9;">{}</span>',
            obj.total_tests_completed
        )
    tests_completed_display.short_description = 'Tugagan Testlar'
    
    def average_rating_display(self, obj):
        stars = '⭐' * int(obj.average_rating)
        return f'{obj.average_rating:.1f} {stars}'
    average_rating_display.short_description = 'O\'rtacha Reyting'
    
    ordering = ['-date']


@admin.register(DashboardAccess)
class DashboardAccessAdmin(admin.ModelAdmin):
    list_display = (
        'user_email',
        'dashboard_type_display',
        'accessed_at',
        'duration_display',
        'ip_address'
    )
    list_filter = ('dashboard_type', 'accessed_at')
    search_fields = ('user__email', 'ip_address')
    readonly_fields = ('created_at', 'updated_at', 'accessed_at')
    
    fieldsets = (
        ('Foydalanuvchi', {
            'fields': ('user', 'dashboard_type')
        }),
        ('Kirish Ma\'lumotlari', {
            'fields': ('accessed_at', 'ip_address', 'duration_minutes')
        }),
        ('Vaqt', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def user_email(self, obj):
        return obj.user.email
    user_email.short_description = 'Foydalanuvchi'
    
    def dashboard_type_display(self, obj):
        colors = {
            'mentor': '#3498db',
            'admin': '#e74c3c',
            'analytics': '#f39c12'
        }
        color = colors.get(obj.dashboard_type, '#95a5a6')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 5px 10px; border-radius: 3px;">{}</span>',
            color,
            obj.get_dashboard_type_display()
        )
    dashboard_type_display.short_description = 'Dashboard Turi'
    
    def duration_display(self, obj):
        hours = obj.duration_minutes // 60
        minutes = obj.duration_minutes % 60
        if hours > 0:
            return f'{hours}h {minutes}min'
        return f'{minutes}min'
    duration_display.short_description = 'Vaqti'
    
    ordering = ['-accessed_at']
