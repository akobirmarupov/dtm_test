from datetime import timedelta

from django.core.cache import cache
from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient

from common.testutils import make_topic_questions, make_user
from progress.achievements import check_and_award, progress_for
from progress.models import Achievement, ReviewCard, UserAchievement, XPTransaction
from progress.services import (
    DEFAULT_EASE_FACTOR,MIN_EASE_FACTOR,award_xp,create_or_update_review_card,
    submit_review_card_answer,update_streak_on_activity)


class SM2Tests(TestCase):
    def setUp(self):
        cache.clear()
        self.user = make_user('sm2@x.uz')
        _, questions = make_topic_questions(3)
        self.question = questions[0]

    def test_wrong_answer_creates_a_card_due_tomorrow(self):
        card = create_or_update_review_card(self.user, self.question, is_correct=False)

        self.assertIsNotNone(card)
        self.assertEqual(card.interval_days, 1)
        self.assertEqual(card.repetitions, 0)
        self.assertEqual(card.next_review_date, timezone.localdate() + timedelta(days=1))

    def test_correct_answer_does_not_create_a_new_card(self):
        card = create_or_update_review_card(self.user, self.question, is_correct=True)

        self.assertIsNone(card)
        self.assertFalse(ReviewCard.objects.filter(user=self.user).exists())


    def test_intervals_grow_on_repeated_success(self):
        card = create_or_update_review_card(self.user, self.question, is_correct=False)

        card = submit_review_card_answer(card, is_correct=True, response_time=20)
        self.assertEqual(card.interval_days, 1)

        card = submit_review_card_answer(card, is_correct=True, response_time=20)
        self.assertEqual(card.interval_days, 6)

        card = submit_review_card_answer(card, is_correct=True, response_time=20)
        self.assertGreater(card.interval_days, 6)


    def test_lapse_resets_the_interval_but_keeps_the_difficulty(self):
        card = create_or_update_review_card(self.user, self.question, is_correct=False)
        for _ in range(3):
            card = submit_review_card_answer(card, is_correct=True, response_time=20)

        long_interval = card.interval_days
        card = submit_review_card_answer(card, is_correct=False)

        self.assertEqual(card.interval_days, 1)
        self.assertEqual(card.repetitions, 0)
        self.assertEqual(card.lapses, 2)
        self.assertLess(card.interval_days, long_interval)
        self.assertGreaterEqual(card.ease_factor, MIN_EASE_FACTOR)


    def test_ease_factor_never_drops_below_the_floor(self):
        card = create_or_update_review_card(self.user, self.question, is_correct=False)
        for _ in range(20):
            card = submit_review_card_answer(card, is_correct=False)

        self.assertGreaterEqual(card.ease_factor, MIN_EASE_FACTOR)


    def test_slow_correct_answer_is_worth_less_than_a_fast_one(self):
        _, questions = make_topic_questions(2, topic_name='Boshqa mavzu')
        slow_card = create_or_update_review_card(self.user, questions[0], is_correct=False)
        fast_card = create_or_update_review_card(self.user, questions[1], is_correct=False)

        slow_card = submit_review_card_answer(slow_card, is_correct=True, response_time=120)
        fast_card = submit_review_card_answer(fast_card, is_correct=True, response_time=5)

        self.assertLess(slow_card.ease_factor, fast_card.ease_factor)


    def test_legacy_field_stays_in_sync(self):
        card = create_or_update_review_card(self.user, self.question, is_correct=False)
        card = submit_review_card_answer(card, is_correct=True, response_time=20)
        card = submit_review_card_answer(card, is_correct=True, response_time=20)

        self.assertEqual(card.stability_days, float(card.interval_days))


class XPSyncTests(TestCase):
    def setUp(self):
        cache.clear()
        self.user = make_user('xpsync@x.uz')


    def test_award_updates_both_the_log_and_the_total(self):
        award_xp(self.user, 40, 'test', 'Birinchi test')
        award_xp(self.user, 25, 'test', 'Ikkinchi test')

        self.user.refresh_from_db()
        self.assertEqual(self.user.xp_total, 65)
        self.assertEqual(XPTransaction.objects.filter(user=self.user).count(), 2)


    def test_zero_award_is_ignored(self):
        self.assertIsNone(award_xp(self.user, 0, 'test'))
        self.assertEqual(XPTransaction.objects.filter(user=self.user).count(), 0)


class StreakTests(TestCase):
    def setUp(self):
        cache.clear()
        self.user = make_user('streak@x.uz')

    def test_same_day_activity_does_not_double_count(self):
        update_streak_on_activity(self.user)
        streak = update_streak_on_activity(self.user)
        self.assertEqual(streak.current_streak, 1)


    def test_consecutive_days_extend_the_streak(self):
        streak = update_streak_on_activity(self.user)
        streak.last_activity_date = timezone.localdate() - timedelta(days=1)
        streak.save(update_fields=['last_activity_date'])

        streak = update_streak_on_activity(self.user)
        self.assertEqual(streak.current_streak, 2)


    def test_gap_resets_the_streak(self):
        streak = update_streak_on_activity(self.user)
        streak.current_streak = 9
        streak.longest_streak = 9
        streak.last_activity_date = timezone.localdate() - timedelta(days=3)
        streak.save(update_fields=['current_streak', 'longest_streak', 'last_activity_date'])

        streak = update_streak_on_activity(self.user)
        self.assertEqual(streak.current_streak, 1)
        self.assertEqual(streak.longest_streak, 9)


class AchievementTests(TestCase):
    def setUp(self):
        cache.clear()
        self.user = make_user('hunter@x.uz')
        self.achievement = Achievement.objects.create(
            code='first-steps', name='Birinchi qadam', icon='🎯',
            metric=Achievement.Metric.TOTAL_XP, threshold=50, xp_reward=10,
        )

    def test_achievement_is_awarded_when_threshold_is_reached(self):
        award_xp(self.user, 60, 'test')
        self.user.refresh_from_db()

        unlocked = check_and_award(self.user)
        self.assertEqual([a.code for a in unlocked], ['first-steps'])


    def test_achievement_is_not_awarded_twice(self):
        award_xp(self.user, 60, 'test')
        self.user.refresh_from_db()

        check_and_award(self.user)
        self.user.refresh_from_db()
        self.assertEqual(check_and_award(self.user), [])
        self.assertEqual(UserAchievement.objects.filter(user=self.user).count(), 1)


    def test_reward_xp_is_paid_out(self):
        award_xp(self.user, 60, 'test')
        self.user.refresh_from_db()
        check_and_award(self.user)

        self.user.refresh_from_db()
        self.assertEqual(self.user.xp_total, 70)  # 60 + 10 mukofot


    def test_locked_achievement_reports_progress(self):
        award_xp(self.user, 25, 'test')
        self.user.refresh_from_db()

        row = progress_for(self.user)[0]
        self.assertFalse(row['is_unlocked'])
        self.assertEqual(row['progress_percent'], 50.0)


    def test_endpoint_lists_unlocked_and_locked(self):
        client = APIClient()
        client.force_authenticate(self.user)
        response = client.get('/progress/achievements/')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['total_count'], 1)
        self.assertEqual(response.data['unlocked_count'], 0)


class MistakeBankTests(TestCase):
    def setUp(self):
        cache.clear()
        self.user = make_user('mistaker@x.uz')
        self.client = APIClient()
        self.client.force_authenticate(self.user)
        self.topic, _ = make_topic_questions(25)


    def _finish(self, wrong_letter='B', answered=20):
        started = self.client.post(
            f'/testengine/topics/{self.topic.id}/start-test/', {'count': 20}, format='json'
        )
        session_id = started.data['id']
        for order in range(1, answered + 1):
            self.client.post(
                f'/testengine/sessions/{session_id}/questions/{order}/answer/',
                {'selected_option': wrong_letter}, format='json',
            )
        self.client.post(f'/testengine/sessions/{session_id}/finish/')
        return session_id


    def test_wrong_answers_land_in_the_bank(self):
        self._finish(wrong_letter='B')
        response = self.client.get('/testengine/mistakes/')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['count'], 20)


    def test_corrected_question_leaves_the_bank(self):
        self._finish(wrong_letter='B')
        before = self.client.get('/testengine/mistakes/').data['count']

        self._finish(wrong_letter='A')  # hammasi to'g'ri
        after = self.client.get('/testengine/mistakes/').data['count']

        self.assertEqual(before, 20)
        self.assertLess(after, before)


    def test_practice_session_is_built_from_mistakes(self):
        self._finish(wrong_letter='B')
        response = self.client.post(
            '/testengine/mistakes/start-test/', {'count': 10}, format='json'
        )

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data['question_count'], 10)


    def test_empty_bank_returns_a_clear_message(self):
        response = self.client.post('/testengine/mistakes/start-test/', {}, format='json')

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data['code'], 'no_mistakes')


    def test_mistake_practice_ignores_the_daily_topic_limit(self):
        self._finish(wrong_letter='B')
        for index in range(2, 6):
            topic, _ = make_topic_questions(20, topic_name=f'Mavzu {index}')
            self.client.post(
                f'/testengine/topics/{topic.id}/start-test/', {'count': 20}, format='json'
            )

        response = self.client.post(
            '/testengine/mistakes/start-test/', {'count': 5}, format='json'
        )
        self.assertEqual(response.status_code, 201)
