import logging

from django.db.models.signals import post_save
from django.db import transaction
from django.dispatch import receiver

from .models import Announcement
from .tasks import broadcast_announcement_task

logger = logging.getLogger(__name__)


@receiver(post_save, sender=Announcement)
def broadcast_announcement(sender, instance, created, **kwargs):
    if not created or instance.is_sent:
        return

    def _dispatch():
        try:
            broadcast_announcement_task.delay(instance.pk)
        except Exception:
            # Broker ishlamayotgani uchun admin paneldagi saqlash 500 bermasin —
            # e'lon `is_sent=False` bo'lib qoladi va qayta yuborsa bo'ladi.
            logger.exception(
                "E'lonni navbatga qo'yib bo'lmadi (broker ishlamayaptimi?): id=%s",
                instance.pk,
            )

    # Tranzaksiya commit bo'lgandan keyin navbatga qo'yamiz — aks holda worker
    # hali yozilmagan yozuvni o'qishga urinishi mumkin.
    transaction.on_commit(_dispatch)
