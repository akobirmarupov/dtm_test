from django.db.models.signals import post_save
from django.dispatch import receiver

from rating.services import update_ratings_for_test_result
from testengine.models import TestResult

from .services import award_xp, create_or_update_review_card, update_streak_on_activity


@receiver(post_save, sender=TestResult)
def handle_test_result_created(sender, instance, created, **kwargs):
    """Test YAKUNLANGANDA ishlaydi.

    Takrorlash kartalari ham shu yerda yaratiladi (ilgari har bir javob
    saqlanganda yaratilardi). Sabab: endi foydalanuvchi 3-savolga qaytib
    javobini to'g'rilashi mumkin — javob berilgan paytdagi holat bo'yicha
    karta ochilsa, keyinchalik to'g'rilangan savol ham "xato" bo'lib
    qolaverardi. Yakuniy holat esa faqat testni tugatganda ma'lum bo'ladi.
    """
    if not created:
        return

    # Bo'sh test uchun XP ham, reyting ham berilmaydi: aks holda sessiya ochib
    # darrov yakunlash orqali XP va leaderboard "farming" qilish mumkin bo'ladi.
    total_answered = instance.correct_count + instance.incorrect_count
    if total_answered == 0:
        return

    user = instance.session.user

    for answer in instance.session.answers.filter(is_correct=False).select_related('question'):
        create_or_update_review_card(user=user, question=answer.question)

    update_streak_on_activity(user)
    award_xp(
        user=user,
        amount=5 + instance.correct_count * 2,
        source='test',
        description='Test yakunlandi',
    )

    # Rating yangilash (daily, weekly, all_time)
    update_ratings_for_test_result(instance)
