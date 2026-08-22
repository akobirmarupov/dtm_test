import logging

from celery import shared_task
from django.utils import timezone

from account.models import User
from .models import Announcement, NotificationLog

logger = logging.getLogger(__name__)

# Bir martada nechta NotificationLog INSERT qilinadi.
BATCH_SIZE = 1000


@shared_task(ignore_result=True)
def broadcast_announcement_task(announcement_id):
    """E'lonni barcha aktiv foydalanuvchilarga tarqatadi.

    Bu ish so'rov ichida bajarilsa, foydalanuvchilar soni o'sgani sari admin
    saqlash sahifasi timeout bo'ladi — shuning uchun Celery'ga chiqarilgan.
    """
    try:
        announcement = Announcement.objects.get(pk=announcement_id)
    except Announcement.DoesNotExist:
        logger.warning('E\'lon topilmadi: id=%s', announcement_id)
        return

    if announcement.is_sent:
        return

    text = (
        f'{announcement.title}\n{announcement.message}'
        if announcement.title else announcement.message
    )

    user_ids = User.objects.filter(is_active=True).values_list('id', flat=True)

    total = 0
    batch = []
    for uid in user_ids.iterator(chunk_size=BATCH_SIZE):
        batch.append(NotificationLog(
            user_id=uid,
            type=NotificationLog.Type.ANNOUNCEMENT,
            message=text,
        ))
        if len(batch) >= BATCH_SIZE:
            NotificationLog.objects.bulk_create(batch)
            total += len(batch)
            batch = []

    if batch:
        NotificationLog.objects.bulk_create(batch)
        total += len(batch)

    announcement.is_sent = True
    announcement.sent_at = timezone.now()
    announcement.recipients_count = total
    announcement.save(update_fields=['is_sent', 'sent_at', 'recipients_count'])

    logger.info(
        'E\'lon tarqatildi: id=%s qabul_qiluvchilar=%s', announcement_id, total
    )
