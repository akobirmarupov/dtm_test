"""Tarifdagi ptichkalar haqiqatan kuchga kiradimi.

Bu yerda tarif nomlari umuman muhim emas — har bir test kerakli cheklovi bor
tarif yaratadi va natijani tekshiradi. Admin nechta bosqich yaratsa ham
(Basic, Pro, Premium, Premium Max...), qoida bitta: bo'sh maydon — cheksiz,
0 — yopiq.
"""

from datetime import timedelta
from decimal import Decimal

from django.core.cache import cache
from django.utils import timezone
from rest_framework.test import APITestCase

from billing.entitlements import invalidate_free_plan_cache
from billing.models import Subscription
from common.models import DailyFeatureUsage, Role
from common.testutils import make_plan, make_topic_questions, make_user
from progress.models import ReviewCard
from testengine.models import Answer, MockExam, TestResult, TestSession


def activate(user, plan, days=30):
    now = timezone.now()
    return Subscription.objects.create(
        user=user, plan=plan, status=Subscription.Status.ACTIVE,
        starts_at=now, expires_at=now + timedelta(days=days),
    )


class PlanLimitBase(APITestCase):
    def setUp(self):
        cache.clear()
        invalidate_free_plan_cache()
        self.user = make_user('limits@example.com')
        self.topic, self.questions = make_topic_questions(25)
        self.client.force_authenticate(self.user)

    def on_plan(self, **limits):
        """Foydalanuvchini shu cheklovlari bor tarifga o'tkazadi."""
        plan = make_plan('Tarif', Decimal('35000'), is_pro=True, **limits)
        activate(self.user, plan)
        return plan

    def make_mistake(self):
        """Xatolar bankiga bitta savol tushiradi."""
        session = TestSession.objects.create(
            user=self.user, subject=self.topic.subject, question_count=1,
        )
        Answer.objects.create(
            session=session, question=self.questions[0],
            selected_option='B', is_correct=False,
        )


class MistakeTestLimitTests(PlanLimitBase):
    def test_zero_means_the_feature_is_closed(self):
        self.on_plan(mistake_test_daily_limit=0)
        self.make_mistake()

        response = self.client.post('/testengine/mistakes/start-test/', {}, format='json')

        self.assertEqual(response.status_code, 403)
        self.assertTrue(response.data['upgrade_required'])
        # Ro'yxatni ko'rish baribir ochiq qoladi.
        self.assertEqual(self.client.get('/testengine/mistakes/').status_code, 200)

    def test_daily_limit_is_counted(self):
        self.on_plan(mistake_test_daily_limit=2)
        self.make_mistake()

        for _ in range(2):
            allowed = self.client.post('/testengine/mistakes/start-test/', {}, format='json')
            self.assertEqual(allowed.status_code, 201, allowed.data)

        blocked = self.client.post('/testengine/mistakes/start-test/', {}, format='json')

        self.assertEqual(blocked.status_code, 403)
        self.assertEqual(blocked.data['code'], 'mistake_test_limit_reached')
        self.assertEqual(blocked.data['remaining_today'], 0)

    def test_empty_limit_means_unlimited(self):
        self.on_plan(mistake_test_daily_limit=None)
        self.make_mistake()

        for _ in range(4):
            response = self.client.post('/testengine/mistakes/start-test/', {}, format='json')
            self.assertEqual(response.status_code, 201)

        self.assertEqual(
            DailyFeatureUsage.objects.filter(
                user=self.user, feature=DailyFeatureUsage.Feature.MISTAKE_TEST
            ).count(),
            0,
            'Cheksiz tarifda hisoblagich yuritilmasligi kerak emas edi',
        )


class ReviewCardLimitTests(PlanLimitBase):
    def setUp(self):
        super().setUp()
        self.cards = [
            ReviewCard.objects.create(user=self.user, question=question)
            for question in self.questions[:5]
        ]

    def submit(self, card):
        return self.client.post(
            f'/progress/reviews/{card.id}/submit/',
            {'is_correct': True, 'response_time': 12}, format='json',
        )

    def test_zero_closes_the_feature(self):
        self.on_plan(review_cards_daily_limit=0)

        response = self.submit(self.cards[0])

        self.assertEqual(response.status_code, 403)
        self.assertTrue(response.data['upgrade_required'])

    def test_limit_stops_further_cards_today(self):
        self.on_plan(review_cards_daily_limit=2)

        self.assertEqual(self.submit(self.cards[0]).status_code, 200)
        self.assertEqual(self.submit(self.cards[1]).status_code, 200)

        blocked = self.submit(self.cards[2])
        self.assertEqual(blocked.status_code, 403)
        self.assertEqual(blocked.data['code'], 'review_card_limit_reached')

    def test_today_list_shows_only_what_is_left(self):
        self.on_plan(review_cards_daily_limit=2)

        first = self.client.get('/progress/reviews/today/')
        self.assertEqual(first.data['remaining_today'], 2)
        self.assertEqual(len(first.data['results']), 2)
        self.assertEqual(first.data['due_total'], 5)

        self.submit(self.cards[0])
        second = self.client.get('/progress/reviews/today/')

        self.assertEqual(second.data['remaining_today'], 1)
        self.assertEqual(len(second.data['results']), 1)


class ExamModeTests(PlanLimitBase):
    def test_exam_mode_can_be_switched_off_for_a_plan(self):
        self.on_plan(can_use_exam_mode=False)

        by_topic = self.client.post(
            f'/testengine/topics/{self.topic.id}/start-test/',
            {'count': 20, 'mode': 'exam'}, format='json',
        )
        by_subject = self.client.post('/testengine/sessions/', {
            'subject': self.topic.subject_id, 'mode': 'exam', 'question_count': 20,
        }, format='json')

        for response in (by_topic, by_subject):
            self.assertEqual(response.status_code, 403, response.data)
            self.assertEqual(response.data['code'], 'exam_mode_unavailable')

    def test_practice_mode_still_works(self):
        self.on_plan(can_use_exam_mode=False)

        response = self.client.post(
            f'/testengine/topics/{self.topic.id}/start-test/',
            {'count': 20, 'mode': 'practice'}, format='json',
        )
        self.assertEqual(response.status_code, 201)

    def test_exam_mode_is_open_when_the_checkbox_is_on(self):
        self.on_plan(can_use_exam_mode=True)

        response = self.client.post(
            f'/testengine/topics/{self.topic.id}/start-test/',
            {'count': 20, 'mode': 'exam'}, format='json',
        )
        self.assertEqual(response.status_code, 201)


class QuestionCountChoiceTests(PlanLimitBase):
    def test_plan_without_the_choice_always_gets_the_smallest_set(self):
        self.on_plan(can_choose_question_count=False, max_question_count=60)

        response = self.client.post('/testengine/sessions/', {
            'subject': self.topic.subject_id, 'question_count': 40,
        }, format='json')

        self.assertEqual(response.status_code, 201, response.data)
        self.assertEqual(response.data['question_count'], 20)

    def test_available_counts_offer_a_single_tier(self):
        self.on_plan(can_choose_question_count=False)

        response = self.client.get(
            f'/testengine/topics/{self.topic.id}/available-counts/'
        )
        self.assertEqual(response.data['tiers'], [20])


class AnalyticsAccessTests(PlanLimitBase):
    CLOSED = [
        '/rating/weak-topics/',
        '/rating/topics/',
        '/rating/subjects/',
        '/rating/history/',
    ]

    def test_analytics_is_hidden_when_the_checkbox_is_off(self):
        self.on_plan(can_view_analytics=False)

        for url in self.CLOSED:
            self.assertEqual(self.client.get(url).status_code, 403, url)

    def test_overall_rating_and_leaderboard_stay_open(self):
        self.on_plan(can_view_analytics=False)

        self.assertEqual(self.client.get('/rating/me/').status_code, 200)
        self.assertEqual(
            self.client.get('/rating/leaderboard/weekly/').status_code, 200
        )

    def test_analytics_opens_with_the_checkbox(self):
        self.on_plan(can_view_analytics=True)

        for url in self.CLOSED:
            self.assertEqual(self.client.get(url).status_code, 200, url)


class HistoryWindowTests(PlanLimitBase):
    def make_result(self, days_ago):
        session = TestSession.objects.create(
            user=self.user, subject=self.topic.subject, question_count=1,
        )
        result = TestResult.objects.create(session=session, total_score=10)
        moment = timezone.now() - timedelta(days=days_ago)
        TestResult.objects.filter(pk=result.pk).update(created_at=moment)
        return result

    def test_older_results_fall_outside_the_window(self):
        self.on_plan(history_days=7)
        fresh = self.make_result(days_ago=2)
        old = self.make_result(days_ago=30)

        listed = self.client.get('/testengine/results/my-results/')
        ids = [row['id'] for row in listed.data['results']]

        self.assertIn(fresh.id, ids)
        self.assertNotIn(old.id, ids)
        self.assertEqual(
            self.client.get(f'/testengine/results/{old.id}/').status_code, 404
        )

    def test_empty_window_means_the_whole_history(self):
        self.on_plan(history_days=None)
        old = self.make_result(days_ago=400)

        listed = self.client.get('/testengine/results/my-results/')

        self.assertIn(old.id, [row['id'] for row in listed.data['results']])


class StreakFreezeQuotaTests(PlanLimitBase):
    def test_zero_means_no_freeze_at_all(self):
        self.on_plan(streak_freezes_per_month=0)

        response = self.client.post('/progress/streak/freeze/')

        self.assertEqual(response.status_code, 403)
        self.assertTrue(response.data['upgrade_required'])

    def test_monthly_quota_is_counted(self):
        self.on_plan(streak_freezes_per_month=2)

        first = self.client.post('/progress/streak/freeze/')
        second = self.client.post('/progress/streak/freeze/')
        third = self.client.post('/progress/streak/freeze/')

        self.assertEqual(first.status_code, 200)
        self.assertEqual(first.data['freezes_remaining'], 1)
        self.assertEqual(second.status_code, 200)
        self.assertEqual(second.data['freezes_remaining'], 0)
        self.assertEqual(third.status_code, 403)
        self.assertEqual(third.data['code'], 'streak_freeze_limit_reached')

    def test_unlimited_plan_never_runs_out(self):
        self.on_plan(streak_freezes_per_month=None)

        for _ in range(4):
            response = self.client.post('/progress/streak/freeze/')
            self.assertEqual(response.status_code, 200)
        self.assertIsNone(response.data['freezes_remaining'])

    def test_detail_endpoint_reports_the_quota(self):
        self.on_plan(streak_freezes_per_month=3)
        self.client.post('/progress/streak/freeze/')

        response = self.client.get('/progress/streak/')

        self.assertEqual(response.data['freezes_limit_per_month'], 3)
        self.assertEqual(response.data['freezes_used_this_month'], 1)
        self.assertEqual(response.data['freezes_remaining'], 2)


class MockExamTests(PlanLimitBase):
    """DTM blok imtihoni: bir nechta fan, bitta umumiy taymer."""

    def setUp(self):
        super().setUp()
        self.second_topic, _ = make_topic_questions(
            25, subject_name='Fizika', topic_name='Mexanika'
        )
        self.subject_ids = [self.topic.subject_id, self.second_topic.subject_id]

    def start(self, **overrides):
        payload = {'subjects': self.subject_ids, 'question_count': 20}
        payload.update(overrides)
        return self.client.post('/testengine/mock-exams/', payload, format='json')

    def test_plan_without_the_checkbox_cannot_start_one(self):
        self.on_plan(features={'mock_exam': False})

        response = self.start()

        self.assertEqual(response.status_code, 403)

    def test_exam_opens_one_session_per_subject_with_a_shared_deadline(self):
        self.on_plan(features={'mock_exam': True})

        response = self.start()

        self.assertEqual(response.status_code, 201, response.data)
        self.assertEqual(len(response.data['subjects']), 2)
        self.assertEqual(response.data['summary']['total_questions'], 40)

        exam = MockExam.objects.get(pk=response.data['id'])
        deadlines = {session.expires_at for session in exam.sessions.all()}
        self.assertEqual(deadlines, {exam.expires_at})
        self.assertEqual(
            {session.mode for session in exam.sessions.all()},
            {TestSession.Mode.EXAM},
        )

    def test_two_open_exams_are_not_allowed(self):
        self.on_plan(features={'mock_exam': True})
        self.start()

        second = self.start()

        self.assertEqual(second.status_code, 400)
        self.assertEqual(second.data['code'], 'exam_already_open')

    def test_finishing_closes_every_subject_and_sums_the_score(self):
        self.on_plan(features={'mock_exam': True})
        started = self.start()
        exam_id = started.data['id']
        first_session = started.data['subjects'][0]['session_id']

        # Bitta fanda bitta to'g'ri javob.
        questions = self.client.get(f'/testengine/sessions/{first_session}/questions/')
        first_question = questions.data[0]['question']['id']
        self.client.post(
            f'/testengine/sessions/{first_session}/answers/',
            {'question': first_question, 'selected_option': 'A'}, format='json',
        )

        finished = self.client.post(f'/testengine/mock-exams/{exam_id}/finish/')

        self.assertEqual(finished.status_code, 200, finished.data)
        self.assertTrue(finished.data['is_finished'])
        self.assertEqual(finished.data['summary']['correct_count'], 1)
        self.assertEqual(finished.data['summary']['unanswered_count'], 39)
        self.assertFalse(
            TestSession.objects.filter(mock_exam_id=exam_id, finished_at__isnull=True).exists()
        )

    def test_question_count_respects_the_plan_ceiling(self):
        self.on_plan(features={'mock_exam': True}, max_question_count=20)

        response = self.start(question_count=25)

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data['code'], 'question_count_exceeded')

    def test_expired_exam_is_closed_automatically(self):
        self.on_plan(features={'mock_exam': True})
        exam_id = self.start().data['id']

        MockExam.objects.filter(pk=exam_id).update(
            expires_at=timezone.now() - timedelta(minutes=1)
        )
        response = self.client.get(f'/testengine/mock-exams/{exam_id}/')

        self.assertTrue(response.data['is_finished'])
        self.assertTrue(response.data['auto_finished'])


class ResultExportTests(PlanLimitBase):
    def make_result(self, days_ago=0):
        session = TestSession.objects.create(
            user=self.user, subject=self.topic.subject, question_count=10,
        )
        result = TestResult.objects.create(
            session=session, total_score=7, correct_count=7,
            incorrect_count=2, unanswered_count=1, duration_seconds=600,
        )
        if days_ago:
            TestResult.objects.filter(pk=result.pk).update(
                created_at=timezone.now() - timedelta(days=days_ago)
            )
        return result

    def test_plan_without_the_checkbox_cannot_export(self):
        self.on_plan(features={'export_results': False})
        self.make_result()

        self.assertEqual(
            self.client.get('/testengine/results/export/').status_code, 403
        )

    def test_export_returns_an_xlsx_file(self):
        self.on_plan(features={'export_results': True})
        self.make_result()

        response = self.client.get('/testengine/results/export/')

        self.assertEqual(response.status_code, 200)
        self.assertIn('spreadsheetml', response['Content-Type'])
        self.assertIn('attachment;', response['Content-Disposition'])
        # .xlsx — bu ZIP arxiv, shuning uchun 'PK' bilan boshlanadi.
        self.assertTrue(response.content.startswith(b'PK'))

    def test_export_can_be_a_pdf(self):
        self.on_plan(features={'export_results': True})
        self.make_result()

        response = self.client.get('/testengine/results/export/?type=pdf')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/pdf')
        self.assertIn('.pdf', response['Content-Disposition'])
        self.assertTrue(response.content.startswith(b'%PDF'))

    def test_unknown_format_is_rejected(self):
        self.on_plan(features={'export_results': True})

        response = self.client.get('/testengine/results/export/?type=doc')

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data['code'], 'unsupported_format')

    def test_export_respects_the_history_window(self):
        self.on_plan(features={'export_results': True}, history_days=7)
        self.make_result()
        self.make_result(days_ago=30)

        response = self.client.get('/testengine/results/export/')

        from io import BytesIO

        from openpyxl import load_workbook

        sheet = load_workbook(BytesIO(response.content)).active
        # Sarlavha + bitta qator.
        self.assertEqual(sheet.max_row, 2)


class MentorSupportTests(PlanLimitBase):
    def setUp(self):
        super().setUp()
        self.admin = make_user('mentor-admin@example.com', role=Role.ADMIN)
        self.mentor = make_user('mentor@example.com', role=Role.MENTOR)
        self.client.force_authenticate(self.admin)

    def attach(self):
        return self.client.post('/dashboard/mentor/students/', {
            'mentor': self.mentor.id, 'student': self.user.id,
        }, format='json')

    def test_student_without_the_checkbox_cannot_be_attached(self):
        self.on_plan(features={'mentor_support': False})

        response = self.attach()

        self.assertEqual(response.status_code, 403)
        self.assertTrue(response.data['upgrade_required'])

    def test_student_with_the_checkbox_is_attached(self):
        self.on_plan(features={'mentor_support': True})

        response = self.attach()

        self.assertEqual(response.status_code, 201, response.data)


class PrioritySupportTests(PlanLimitBase):
    def test_priority_is_shown_on_the_request_page(self):
        self.on_plan(features={'priority_support': True})

        response = self.client.get('/billing/payments/info/')

        self.assertTrue(response.data['priority_support'])
        self.assertIn('navbatsiz', response.data['message'])

    def test_plan_without_priority_sees_the_plain_message(self):
        self.on_plan(features={'priority_support': False})

        response = self.client.get('/billing/payments/info/')

        self.assertFalse(response.data['priority_support'])
        self.assertNotIn('navbatsiz', response.data['message'])


class AITutorSeamTests(PlanLimitBase):
    """AI tutor hali yozilmagan — ptichka belgilansa ham izoh o'ylab
    topilmasligi kerak."""

    def test_ai_service_stays_silent_without_a_static_explanation(self):
        from testengine.explanations import AIExplanationService

        self.on_plan(features={'ai_tutor': True}, can_view_explanations=True)
        question = self.questions[0]

        explanation = AIExplanationService().for_question(question, request=None)

        self.assertIsNone(explanation)

    def test_catalog_marks_ai_tutor_as_not_enforced(self):
        from billing.features import feature_catalog

        by_key = {item['key']: item for item in feature_catalog()['features']}

        self.assertFalse(by_key['ai_tutor']['enforced'])
        self.assertTrue(by_key['mock_exam']['enforced'])
        self.assertTrue(by_key['export_results']['enforced'])
        self.assertTrue(by_key['mentor_support']['enforced'])
