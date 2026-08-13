from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import RatingHistory


@receiver(post_save, sender=RatingHistory)
def notify_rank_up(sender, instance, created, **kwargs):
    if not created or instance.period != 'weekly':
        return
    if not instance.previous_rank or not instance.new_rank:
        return

    if instance.new_rank < instance.previous_rank:
        from notifications.models import NotificationLog
        delta = instance.previous_rank - instance.new_rank
        NotificationLog.objects.create(
            user=instance.user,
            type=NotificationLog.Type.RATING_UP,
            message=f"Sizning reytingingiz {delta} ga ko'tarildi! Endi {instance.new_rank}-o'rindasiz 🚀",
        )