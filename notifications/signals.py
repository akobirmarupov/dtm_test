from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone

from account.models import User
from .models import Announcement, NotificationLog


@receiver(post_save, sender=Announcement)
def broadcast_announcement(sender, instance, created, **kwargs):
    if not created or instance.is_sent:
        return

    text = f'{instance.title}\n{instance.message}' if instance.title else instance.message
    user_ids = list(User.objects.filter(is_active=True).values_list('id', flat=True))

    NotificationLog.objects.bulk_create([
        NotificationLog(user_id=uid, type=NotificationLog.Type.ANNOUNCEMENT, message=text)
        for uid in user_ids
    ])

    instance.is_sent = True
    instance.sent_at = timezone.now()
    instance.recipients_count = len(user_ids)
    instance.save(update_fields=['is_sent', 'sent_at', 'recipients_count'])