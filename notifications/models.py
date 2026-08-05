from django.db import models

from common.models import BaseModel


class NotificationLog(BaseModel):
    class Channel(models.TextChoices):
        SMS = 'sms', 'SMS'
        PUSH = 'push', 'Push'

    class Status(models.TextChoices):
        PENDING = 'pending', 'Kutilmoqda'
        SENT = 'sent', 'Yuborildi'
        FAILED = 'failed', 'Yuborilmadi'

    user = models.ForeignKey('account.User', on_delete=models.CASCADE, related_name='notification_logs')
    channel = models.CharField('Kanal', max_length=10, choices=Channel.choices)
    message = models.TextField('Xabar matni')
    status = models.CharField('Holati', max_length=10, choices=Status.choices, default=Status.PENDING)
    sent_at = models.DateTimeField('Yuborilgan vaqti', null=True, blank=True)

    def __str__(self):
        return f'{self.user} - {self.channel}'


class PushToken(BaseModel):
    class DeviceType(models.TextChoices):
        FCM = 'fcm', 'FCM'
        APNS = 'apns', 'APNs'

    user = models.ForeignKey('account.User', on_delete=models.CASCADE, related_name='push_tokens')
    token = models.CharField('Token', max_length=255, unique=True)
    device_type = models.CharField('Qurilma turi', max_length=10, choices=DeviceType.choices)
    is_active = models.BooleanField('Faolmi', default=True)

    def __str__(self):
        return f'{self.user} - {self.device_type}'


class ReminderSchedule(BaseModel):
    class ReminderType(models.TextChoices):
        REVIEW = 'review', 'Takrorlash bor'
        STREAK = 'streak', 'Streak uzilmasin'

    user = models.ForeignKey('account.User', on_delete=models.CASCADE, related_name='reminder_schedules')
    reminder_type = models.CharField('Turi', max_length=10, choices=ReminderType.choices)
    scheduled_at = models.DateTimeField('Rejalashtirilgan vaqti')
    is_sent = models.BooleanField('Yuborilganmi', default=False)

    def __str__(self):
        return f'{self.user} - {self.reminder_type}'
