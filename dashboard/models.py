from django.db import models
from django.utils import timezone
from common.models import BaseModel, Role


class MentorStudent(BaseModel):
    """
    Mentor va talaba o'rtasidagi bog'lanish.
    Bir mentor ko'p talabalarni ko'rashishi mumkin.
    """
    
    mentor = models.ForeignKey('account.User',on_delete=models.CASCADE,
        related_name='mentored_students',limit_choices_to={'role': Role.MENTOR})
    student = models.ForeignKey('account.User',on_delete=models.CASCADE,
        related_name='mentors',limit_choices_to={'role': Role.STUDENT})
    assigned_at = models.DateTimeField('Tayinlangan vaqti', auto_now_add=True)
    is_active = models.BooleanField('Faolmi', default=True)
    notes = models.TextField('Izohlar', blank=True)

    class Meta:
        unique_together = ('mentor', 'student')
        ordering = ['-assigned_at']

    def __str__(self):
        return f'{self.mentor.email} → {self.student.email}'


class MentorAlert(BaseModel):
    """
    Mentor uchun ogohlantirish/notifikatsiyalar.
    Qaysi talaba muammoli ekanini ko'rish.
    """
    
    class AlertType(models.TextChoices):
        LOW_PERFORMANCE = 'low_performance', 'Past faollik'
        NO_ACTIVITY = 'no_activity', 'Faollik yo\'q'
        LOW_RATING = 'low_rating', 'Past reyting'
        STREAK_BROKEN = 'streak_broken', 'Streak uzildi'
        NEEDS_REVIEW = 'needs_review', 'Ko\'rikni keraki'

    class Status(models.TextChoices):
        OPEN = 'open', 'Ochiq'
        RESOLVED = 'resolved', 'Hal qilindi'
        IGNORED = 'ignored', 'Rad etildi'

    mentor = models.ForeignKey('account.User',on_delete=models.CASCADE,
        related_name='alerts',limit_choices_to={'role': Role.MENTOR})
    student = models.ForeignKey('account.User',on_delete=models.CASCADE,related_name='alert_logs')
    alert_type = models.CharField('Ogohlantirish turi', max_length=20, choices=AlertType.choices)
    status = models.CharField('Holati', max_length=20, choices=Status.choices, default=Status.OPEN)
    message = models.TextField('Xabar')
    created_at = models.DateTimeField('Yaratilgan vaqti', auto_now_add=True)
    resolved_at = models.DateTimeField('Hal qilingan vaqti', null=True, blank=True)
    action_taken = models.TextField('Qabul qilingan haraka', blank=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['mentor', 'status']),
            models.Index(fields=['student', '-created_at']),
        ]

    def __str__(self):
        return f'{self.mentor.email} - {self.student.email}: {self.get_alert_type_display()}'


class AnalyticsSummary(BaseModel):
    """
    Platform bo'yicha umumiy statistika va tahlil.
    Admin dashboard uchun.
    """
    
    class TimeFrame(models.TextChoices):
        DAILY = 'daily', 'Kunlik'
        WEEKLY = 'weekly', 'Haftalik'
        MONTHLY = 'monthly', 'Oylik'
        YEARLY = 'yearly', 'Yillik'

    date = models.DateField('Sana')
    timeframe = models.CharField('Davr', max_length=20, choices=TimeFrame.choices)
    total_users = models.PositiveIntegerField('Jami foydalanuvchilar', default=0)
    active_users = models.PositiveIntegerField('Faol foydalanuvchilar', default=0)
    new_users = models.PositiveIntegerField('Yangi foydalanuvchilar', default=0)
    total_tests_completed = models.PositiveIntegerField('Jami tugagan testlar', default=0)
    average_accuracy = models.FloatField('O\'rtacha to\'g\'rilik %', default=0.0)
    average_rating = models.FloatField('O\'rtacha reyting ⭐', default=0.0)
    active_subscriptions = models.PositiveIntegerField('Faol obunalar', default=0)
    expired_subscriptions = models.PositiveIntegerField("Muddati o'tgan obunalar", default=0)
    total_revenue = models.DecimalField('Jami daromad', max_digits=12, decimal_places=2, default=0.0)
    engagement_rate = models.FloatField('Ishtirok darajasi %', default=0.0)
    retention_rate = models.FloatField('Qaytishi darajasi %', default=0.0)
    top_subject_id = models.ForeignKey('catalog.Subject',on_delete=models.SET_NULL,
        null=True,blank=True,related_name='analytics')
    last_updated = models.DateTimeField('Oxirgi yangilangan vaqt', auto_now=True)

    class Meta:
        unique_together = ('date', 'timeframe')
        ordering = ['-date']

    def __str__(self):
        return f'{self.get_timeframe_display()} - {self.date}'


class DashboardAccess(BaseModel):
    """
    Dashboard kirish logi.
    Mentor va Admin'larning dashboard'ga kirish tarixi.
    """
    
    class DashboardType(models.TextChoices):
        MENTOR = 'mentor', 'Mentor Dashboard'
        ADMIN = 'admin', 'Admin Dashboard'
        ANALYTICS = 'analytics', 'Analytics'

    user = models.ForeignKey('account.User', on_delete=models.CASCADE, related_name='dashboard_access')
    dashboard_type = models.CharField('Dashboard turi', max_length=20, choices=DashboardType.choices)  
    accessed_at = models.DateTimeField('Kirgan vaqti', auto_now_add=True)
    ip_address = models.GenericIPAddressField('IP manzili', null=True, blank=True) 
    duration_minutes = models.PositiveIntegerField('Qo\'shilgan vaqt (minut)', default=0)

    class Meta:
        ordering = ['-accessed_at']
        indexes = [
            models.Index(fields=['user', 'dashboard_type']),
            models.Index(fields=['accessed_at']),
        ]

    def __str__(self):
        return f'{self.user.email} - {self.get_dashboard_type_display()} ({self.accessed_at})'
