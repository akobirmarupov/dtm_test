from django.db import models

from common.models import BaseModel


class NotificationLog(BaseModel):
    class Type(models.TextChoices):
        WELCOME = 'welcome', 'Ro\'yxatdan o\'tish tabrigi'
        RATING_UP = 'rating_up', 'Reyting ko\'tarilishi'
        ANNOUNCEMENT = 'announcement', 'Umumiy e\'lon'

    user = models.ForeignKey('account.User', on_delete=models.CASCADE, related_name='notification_logs')
    type = models.CharField('Turi', max_length=20, choices=Type.choices)
    message = models.TextField('Xabar matni')
    is_read = models.BooleanField('O\'qilganmi', default=False)
    read_at = models.DateTimeField('O\'qilgan vaqti', null=True, blank=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'is_read']),
            models.Index(fields=['user', '-created_at']),
        ]

    def __str__(self):
        return f'{self.user} - {self.get_type_display()}'


class Announcement(BaseModel):
    title = models.CharField('Sarlavha', max_length=200, blank=True)
    message = models.TextField('Xabar matni')
    created_by = models.ForeignKey(
        'account.User', on_delete=models.SET_NULL, null=True, blank=True,related_name='announcements',)
    is_sent = models.BooleanField('Yuborildimi', default=False)
    sent_at = models.DateTimeField('Yuborilgan vaqti', null=True, blank=True)
    recipients_count = models.PositiveIntegerField('Nechta userga yetdi', default=0)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.title or self.message[:40]