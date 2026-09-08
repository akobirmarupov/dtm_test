"""Reyting tizimi: tuzatilgan buglar va yangi qoidalar.

Har bir test AYNI BIR regressiyani qo'riqlaydi — kod o'zgarganda qaysi
qoida buzilgani darrov ko'rinishi uchun.
"""

from datetime import date, timedelta

from django.core.cache import cache
from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient

from common.testutils import make_topic_questions, make_user
from rating.leagues import (
    DEMOTE_COUNT,
    LEAGUE_SIZE,
    PROMOTE_COUNT,
    add_xp,
    close_week,
    current_week,
    ensure_membership,
)
from rating.models import League, LeagueMembership, Leaderboard, Rating, TopicRating
from rating.services import (
    ALL_TIME_END,
    ALL_TIME_START,
    calculate_stars,
    get_period_dates,
    rebuild_all_leaderboards,
    weak_topics,
)
from testengine.scoring import score_session, stars_from_points


# Davrlar
class PeriodTests(TestCase):
    def test_all_time_period_is_fixed(self):
        yesterday = date(2026, 9, 7)
        today = date(2026, 9, 8)

        self.assertEqual(
            get_period_dates('all_time', yesterday),
            get_period_dates('all_time', today),
        )
        self.assertEqual(get_period_dates('all_time', today), (ALL_TIME_START, ALL_TIME_END))

    def test_daily_period_uses_local_date(self):
        start, end = get_period_dates('daily')
        self.assertEqual(start, timezone.localdate())
        self.assertEqual(end, timezone.localdate())

    def test_weekly_period_starts_on_monday(self):
        start, end = get_period_dates('weekly', date(2026, 9, 10))  # payshanba
        self.assertEqual(start, date(2026, 9, 7))   # dushanba
        self.assertEqual(end, date(2026, 9, 13))    # yakshanba


# ⭐ formulasi
class StarsFormulaTests(TestCase):
    def test_unanswered_questions_are_not_free(self):
        lazy = stars_from_points(earned=5, possible=20)      # 15 tasi bo'sh
        diligent = stars_from_points(earned=28, possible=30)

        self.assertLess(lazy, diligent)

    def test_volume_matters(self):
        tiny_perfect = stars_from_points(earned=5, possible=5)
        large_good = stars_from_points(earned=540, possible=600)

        self.assertLess(tiny_perfect, large_good)

    def test_stars_stay_in_range(self):
        self.assertEqual(stars_from_points(0, 0), 0.0)
        self.assertGreaterEqual(calculate_stars(0, 100), 0.0)
        self.assertLessEqual(calculate_stars(10_000, 10_000), 5.0)

    def test_wrong_and_unanswered_cost_the_same(self):
        wrong = stars_from_points(earned=15, possible=20)      # 5 tasi xato
        blank = stars_from_points(earned=15, possible=20)      # 5 tasi bo'sh
        self.assertEqual(wrong, blank)


class DifficultyWeightTests(TestCase):
    def setUp(self):
        cache.clear()
        self.user = make_user('scorer@example.com')

    def test_hard_questions_are_worth_more(self):
        from catalog.models import Question
        from testengine.models import Answer, SessionQuestion, TestSession

        topic, questions = make_topic_questions(2)
        easy, hard = questions
        Question.objects.filter(pk=easy.pk).update(difficulty=Question.Difficulty.VERY_EASY)
        Question.objects.filter(pk=hard.pk).update(difficulty=Question.Difficulty.VERY_HARD)

        session = TestSession.objects.create(user=self.user, subject=topic.subject)
        SessionQuestion.objects.create(session=session, question=easy, order=1)
        SessionQuestion.objects.create(session=session, question=hard, order=2)
        Answer.objects.create(
            session=session, question=hard, selected_option='A', is_correct=True
        )

        score = score_session(session)
        # Faqat qiyin savol yechildi -> olingan ball butun havzaning yarmidan ko'p.
        self.assertGreater(score.earned / score.possible, 0.5)


# To'liq oqim
class RatingFlowTests(TestCase):
    def setUp(self):
        cache.clear()
        self.user = make_user('flow@example.com')
        self.client = APIClient()
        self.client.force_authenticate(self.user)
        self.topic, _ = make_topic_questions(25)

    def finish_test(self, answered=20, correct_letter='A'):
        started = self.client.post(
            f'/testengine/topics/{self.topic.id}/start-test/', {'count': 20}, format='json'
        )
        session_id = started.data['id']
        for order in range(1, answered + 1):
            self.client.post(
                f'/testengine/sessions/{session_id}/questions/{order}/answer/',
                {'selected_option': correct_letter}, format='json',
            )
        return self.client.post(f'/testengine/sessions/{session_id}/finish/')

    def test_all_three_periods_are_updated(self):
        self.finish_test()
        periods = set(Rating.objects.filter(user=self.user).values_list('period', flat=True))
        self.assertEqual(periods, {'daily', 'weekly', 'all_time'})

    def test_all_time_row_is_reused_not_duplicated(self):
        self.finish_test()
        self.finish_test()

        rows = Rating.objects.filter(user=self.user, period='all_time')
        self.assertEqual(rows.count(), 1)
        self.assertEqual(rows.first().tests_completed, 2)

    def test_unanswered_questions_are_recorded(self):
        self.finish_test(answered=12)
        rating = Rating.objects.get(user=self.user, period='daily')
        self.assertEqual(rating.unanswered_answers, 8)

    def test_xp_is_awarded_and_user_total_stays_in_sync(self):
        """REGRESSIYA: `User.xp_total` hech qachon yangilanmasdi va admin
        panelda har bir foydalanuvchi 0 XP bo'lib turardi."""
        self.finish_test()
        self.user.refresh_from_db()

        rating = Rating.objects.get(user=self.user, period='daily')
        self.assertGreater(rating.xp, 0)
        self.assertEqual(self.user.xp_total, rating.xp)

    def test_topic_rating_is_updated(self):
        self.finish_test()
        self.assertTrue(TopicRating.objects.filter(user=self.user, topic=self.topic).exists())


# Leaderboard
class LeaderboardTests(TestCase):
    def setUp(self):
        cache.clear()
        self.start, self.end = get_period_dates('daily')

    def _rating(self, email, xp, stars=3.0):
        user = make_user(email)
        Rating.objects.create(
            user=user, period='daily', xp=xp, stars=stars, tests_completed=1,
            period_start_date=self.start, period_end_date=self.end,
        )
        return user

    def test_ranks_are_computed_for_everyone(self):
        self._rating('a@x.uz', xp=300)
        self._rating('b@x.uz', xp=200)
        self._rating('c@x.uz', xp=100)

        rebuild_all_leaderboards()

        ranks = list(
            Rating.objects.filter(period='daily').order_by('rank')
            .values_list('xp', 'rank')
        )
        self.assertEqual(ranks, [(300, 1), (200, 2), (100, 3)])

    def test_snapshot_table_is_populated(self):
        self._rating('a@x.uz', xp=300)
        rebuild_all_leaderboards()

        self.assertTrue(
            Leaderboard.objects.filter(period='daily', rank=1).exists()
        )

    def test_leaderboard_is_ordered_by_xp(self):
        top = self._rating('worker@x.uz', xp=500, stars=2.0)
        self._rating('accurate@x.uz', xp=50, stars=5.0)
        rebuild_all_leaderboards()

        client = APIClient()
        client.force_authenticate(top)
        response = client.get('/rating/leaderboard/daily/')

        self.assertEqual(response.data['results'][0]['user_id'], top.id)
        self.assertEqual(response.data['results'][0]['rank'], 1)

    def test_user_outside_top_still_sees_own_rank(self):
        for index in range(3):
            self._rating(f'top{index}@x.uz', xp=1000 - index)
        me = self._rating('me@x.uz', xp=1)
        rebuild_all_leaderboards()

        client = APIClient()
        client.force_authenticate(me)
        response = client.get('/rating/leaderboard/daily/')

        self.assertEqual(response.data['my_position']['rank'], 4)
        self.assertEqual(response.data['my_position']['total_participants'], 4)

    def test_both_weekly_leaderboards_agree(self):
        start, end = get_period_dates('weekly')
        first = make_user('first@x.uz', full_name='Birinchi')
        second = make_user('second@x.uz', full_name='Ikkinchi')
        Rating.objects.create(
            user=first, period='weekly', xp=900, stars=1.0, tests_completed=9,
            period_start_date=start, period_end_date=end,
        )
        Rating.objects.create(
            user=second, period='weekly', xp=100, stars=5.0, tests_completed=1,
            period_start_date=start, period_end_date=end,
        )
        rebuild_all_leaderboards()

        client = APIClient()
        client.force_authenticate(first)
        rating_top = client.get('/rating/leaderboard/weekly/').data['results'][0]['user_id']
        progress_top = client.get('/progress/leaderboard/weekly/').data[0]['user_id']

        self.assertEqual(rating_top, progress_top)


# Ligalar
class LeagueTests(TestCase):
    def setUp(self):
        cache.clear()
        self.start, self.end = current_week()

    def test_new_user_starts_in_bronze(self):
        user = make_user('rookie@x.uz')
        membership = ensure_membership(user)
        self.assertEqual(membership.league.tier, League.Tier.BRONZE)

    def test_group_holds_thirty_people_then_opens_a_new_one(self):
        for index in range(LEAGUE_SIZE + 1):
            ensure_membership(make_user(f'u{index}@x.uz'))

        groups = League.objects.filter(period_start_date=self.start, tier=League.Tier.BRONZE)
        self.assertEqual(groups.count(), 2)

    def test_xp_accumulates_inside_the_league(self):
        user = make_user('grinder@x.uz')
        add_xp(user, 50)
        add_xp(user, 30)

        membership = LeagueMembership.objects.get(user=user)
        self.assertEqual(membership.xp, 80)

    def test_top_seven_are_promoted_and_bottom_five_demoted(self):
        users = [make_user(f'p{index}@x.uz') for index in range(LEAGUE_SIZE)]
        for position, user in enumerate(users):
            add_xp(user, (LEAGUE_SIZE - position) * 10)

        League.objects.filter(period_start_date=self.start).update(tier=League.Tier.SILVER)
        close_week(self.start)

        rows = LeagueMembership.objects.order_by('rank')
        promoted = [row for row in rows if row.outcome == 'promoted']
        demoted = [row for row in rows if row.outcome == 'demoted']

        self.assertEqual(len(promoted), PROMOTE_COUNT)
        self.assertEqual(len(demoted), DEMOTE_COUNT)
        self.assertEqual(promoted[0].user_id, users[0].id)

    def test_bronze_users_are_never_demoted(self):
        users = [make_user(f'b{index}@x.uz') for index in range(10)]
        for position, user in enumerate(users):
            add_xp(user, (10 - position) * 10)

        close_week(self.start)
        self.assertFalse(LeagueMembership.objects.filter(outcome='demoted').exists())

    def test_promoted_user_moves_up_next_week(self):
        user = make_user('climber@x.uz')
        membership = ensure_membership(user)
        League.objects.filter(pk=membership.league_id).update(tier=League.Tier.BRONZE)
        add_xp(user, 500)
        close_week(self.start)

        from rating.leagues import previous_tier
        next_week = self.start + timedelta(days=7)
        self.assertEqual(previous_tier(user, next_week), League.Tier.SILVER)

    def test_my_league_endpoint_marks_the_zones(self):
        me = make_user('me@x.uz')
        add_xp(me, 100)
        for index in range(9):
            add_xp(make_user(f"other{index}@x.uz"), index + 1)

        client = APIClient()
        client.force_authenticate(me)
        response = client.get('/rating/league/')

        self.assertTrue(response.data['has_league'])
        self.assertEqual(response.data['my_rank'], 1)
        self.assertEqual(response.data['my_zone'], 'promotion')
        self.assertEqual(len(response.data['standings']), 10)

    def test_user_without_activity_has_no_league(self):
        client = APIClient()
        client.force_authenticate(make_user('idle@x.uz'))
        response = client.get('/rating/league/')

        self.assertFalse(response.data['has_league'])
        self.assertEqual(response.data['standings'], [])

    def test_league_does_not_expose_emails(self):
        me = make_user('viewer@x.uz', full_name='Ko\'ruvchi')
        add_xp(me, 10)
        add_xp(make_user('secret@x.uz'), 5)

        client = APIClient()
        client.force_authenticate(me)
        response = client.get('/rating/league/')

        self.assertNotIn('secret@x.uz', str(response.data))


# Zaif mavzular
class WeakTopicTests(TestCase):
    def setUp(self):
        cache.clear()
        self.user = make_user('struggler@x.uz')
        self.topic, _ = make_topic_questions(20)

    def test_topic_with_little_data_is_not_called_weak(self):
        """Bitta testdagi omadsizlik «zaif mavzu» degani emas."""
        TopicRating.objects.create(
            user=self.user, topic=self.topic, stars=1.0,
            correct_answers=1, incorrect_answers=2,
        )
        self.assertEqual(weak_topics(self.user), [])

    def test_weak_topic_is_reported(self):
        TopicRating.objects.create(
            user=self.user, topic=self.topic, stars=1.5,
            correct_answers=4, incorrect_answers=16,
        )
        rows = weak_topics(self.user)
        self.assertEqual([row.topic_id for row in rows], [self.topic.id])

    def test_endpoint_flags_whether_practice_can_start(self):
        TopicRating.objects.create(
            user=self.user, topic=self.topic, stars=1.5,
            correct_answers=4, incorrect_answers=16,
        )
        client = APIClient()
        client.force_authenticate(self.user)
        response = client.get('/rating/weak-topics/')

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.data[0]['can_start_test'])
