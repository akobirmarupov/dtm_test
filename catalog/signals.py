from django.db import transaction
from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from catalog.models import Question, Topic


def _refresh(topic_id):
    if not topic_id:
        return
    topic = Topic.objects.filter(pk=topic_id).only('id', 'available_question_count').first()
    if topic is not None:
        topic.recount_questions()


def _invalidate_pool():
    from testengine.services import invalidate_question_pool
    invalidate_question_pool()


@receiver(post_save, sender=Question)
def question_saved(sender, instance, **kwargs):
    topic_ids = {instance.topic_id, getattr(instance, '_previous_topic_id', None)}

    for topic_id in topic_ids:
        _refresh(topic_id)

    transaction.on_commit(_invalidate_pool)


@receiver(post_delete, sender=Question)
def question_deleted(sender, instance, **kwargs):
    _refresh(instance.topic_id)
    transaction.on_commit(_invalidate_pool)
