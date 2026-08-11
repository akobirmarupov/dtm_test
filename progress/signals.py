from django.db.models.signals import post_save
from django.dispatch import receiver

from testengine.models import Answer, TestResult
from .services import create_or_update_review_card, update_streak_on_activity, award_xp
from rating.services import update_ratings_for_test_result


@receiver(post_save, sender=Answer)
def handle_answer_saved(sender, instance, created, **kwargs):
    """Foydalanuvchi javob berganda ishlaydi. Faqat noto'g'ri javob bo'lsa,
    ReviewCard yaratiladi/yangilanadi — chunki takrorlash faqat xato
    qilingan savollar uchun kerak."""
    if not created:
        return
    if not instance.is_correct:
        create_or_update_review_card(
            user=instance.session.user,
            question=instance.question,
        )


@receiver(post_save, sender=TestResult)
def handle_test_result_created(sender, instance, created, **kwargs):
    """Test yakunlanib, TestResult yaratilganda ishlaydi.
    Streak yangilanadi, XP beriladi, va reytinglar yangilanadi."""
    if not created:
        return
    user = instance.session.user

    update_streak_on_activity(user)
    award_xp(
        user=user,
        amount=10,
        source='test',
        description='Test yakunlandi',
    )
    
    # Rating yangilash (daily, weekly, all_time)
    update_ratings_for_test_result(instance)