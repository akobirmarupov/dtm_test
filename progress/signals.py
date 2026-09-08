import logging

from django.db import transaction
from django.db.models.signals import post_save
from django.dispatch import receiver

from testengine.models import TestResult
from testengine.scoring import score_from_result

from .achievements import check_and_award
from .services import award_xp, create_or_update_review_card, update_streak_on_activity

logger = logging.getLogger('progress.signals')


@receiver(post_save, sender=TestResult)
def handle_test_result_created(sender, instance, created, **kwargs):
    if not created:
        return
    score = score_from_result(instance)
    if score.correct_count + score.incorrect_count == 0:
        return

    user = instance.session.user

    for answer in instance.session.answers.select_related('question'):
        create_or_update_review_card(
            user=user,
            question=answer.question,
            is_correct=answer.is_correct,
            response_time_seconds=answer.time_spent_seconds,
        )

    update_streak_on_activity(user)

    award_xp(
        user=user,
        amount=score.xp,
        source='test',
        description=(
            f"Test yakunlandi: {score.correct_count}/{score.total_questions} to'g'ri"
        ),
    )

    from rating.services import update_ratings_for_test_result

    update_ratings_for_test_result(instance)

    from rating.leagues import add_xp as add_league_xp

    add_league_xp(user, score.xp)

    check_and_award(user)

    logger.info(
        'Test natijasi qayta ishlandi: session_id=%s xp=%s togri=%s user_id=%s',
        instance.session_id, score.xp, score.correct_count, user.id,
    )
