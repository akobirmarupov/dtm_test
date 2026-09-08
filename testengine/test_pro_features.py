"""Obuna darajalari, yechim izohlari, imtihon taymeri va savol hayot sikli."""

from datetime import timedelta
from decimal import Decimal

from django.core.cache import cache
from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient

from billing.entitlements import entitlements_for, invalidate_free_plan_cache
from billing.models import Subscription
from catalog.models import Question
from common.testutils import make_plan, make_topic_questions, make_user
from testengine.models import ExplanationUsage, TestSession
from testengine.services import finish_expired_sessions, pick_questions


def activate_plan(user, plan, days=30):
    now = timezone.now()
    return Subscription.objects.create(
        user=user, plan=plan, status=Subscription.Status.ACTIVE,
        starts_at=now, expires_at=now + timedelta(days=days),
    )


class BaseFlow(TestCase):
    def setUp(self):
        cache.clear()
        invalidate_free_plan_cache()
        self.user = make_user('learner@example.com')
        self.client = APIClient()
        self.client.force_authenticate(self.user)
        self.topic, self.questions = make_topic_questions(25)

    def with_explanations(self):
        Question.objects.filter(topic=self.topic).update(
            explanation="Chunki kvadrat tenglama diskriminanti musbat."
        )

    def finish_a_test(self, count=20):
        started = self.client.post(
            f'/testengine/topics/{self.topic.id}/start-test/',
            {'count': count}, format='json',
        )
        session_id = started.data['id']
        return session_id, self.client.post(f'/testengine/sessions/{session_id}/finish/')


# ---------------------------------------------------------------------------
# Yechim izohlari
# ---------------------------------------------------------------------------
class ExplanationAccessTests(BaseFlow):
    def test_free_user_sees_the_correct_answer_but_no_explanation(self):
        self.with_explanations()
        _, response = self.finish_a_test()

        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.data['explanation_access']['available'])
        self.assertTrue(response.data['explanation_access']['upgrade_required'])
        for item in response.data['review']:
            # To'g'ri javob ochiq — bu Free uchun ham bor.
            self.assertIsNotNone(item['correct_option'])
            # Izoh esa yopiq.
            self.assertIsNone(item['explanation'])

    def test_pro_full_user_sees_the_explanation(self):
        self.with_explanations()
        plan = make_plan(
            'Pro-Full', Decimal('59000'), code='pro_full',
            is_pro=True, can_view_explanations=True, explanation_limit_per_day=None,
        )
        activate_plan(self.user, plan)

        _, response = self.finish_a_test()

        self.assertTrue(response.data['explanation_access']['available'])
        self.assertIsNone(response.data['explanation_access']['limit_per_day'])
        first = response.data['review'][0]
        self.assertIn('diskriminanti', first['explanation']['text'])
        self.assertEqual(first['explanation']['source'], 'static')

    def test_pro_basic_daily_explanation_limit_is_enforced(self):
        self.with_explanations()
        plan = make_plan(
            'Pro-Basic', Decimal('35000'), code='pro_basic',
            is_pro=True, can_view_explanations=True, explanation_limit_per_day=2,
        )
        activate_plan(self.user, plan)

        for _ in range(2):
            _, response = self.finish_a_test()
            self.assertTrue(response.data['explanation_access']['available'])

        _, third = self.finish_a_test()
        self.assertFalse(third.data['explanation_access']['available'])
        self.assertEqual(
            third.data['explanation_access']['code'], 'explanation_limit_reached'
        )
        self.assertIsNone(third.data['review'][0]['explanation'])

    def test_reopening_the_same_review_does_not_consume_the_quota(self):
        """Sahifani yangilash limitni yeb qo'ymasligi kerak."""
        self.with_explanations()
        plan = make_plan(
            'Pro-Basic', Decimal('35000'), code='pro_basic',
            is_pro=True, can_view_explanations=True, explanation_limit_per_day=1,
        )
        activate_plan(self.user, plan)

        session_id, _ = self.finish_a_test()
        for _ in range(3):
            response = self.client.get(f'/testengine/sessions/{session_id}/review/')
            self.assertTrue(response.data['explanation_access']['available'])

        self.assertEqual(ExplanationUsage.objects.filter(user=self.user).count(), 1)

    def test_question_without_explanation_returns_null(self):
        plan = make_plan(
            'Pro-Full', Decimal('59000'), code='pro_full',
            is_pro=True, can_view_explanations=True,
        )
        activate_plan(self.user, plan)

        _, response = self.finish_a_test()
        self.assertIsNone(response.data['review'][0]['explanation'])


# ---------------------------------------------------------------------------
# Obuna darajalari
# ---------------------------------------------------------------------------
class EntitlementTests(TestCase):
    def setUp(self):
        cache.clear()
        invalidate_free_plan_cache()

    def test_anonymous_user_is_a_guest(self):
        entitlements = entitlements_for(None)
        self.assertEqual(entitlements.tier, 'guest')
        self.assertFalse(entitlements.can_view_results)
        self.assertFalse(entitlements.can_persist_progress)
        self.assertFalse(entitlements.can_choose_question_count)

    def test_user_without_subscription_falls_back_to_free(self):
        user = make_user('nobody@example.com')
        entitlements = entitlements_for(user)

        self.assertEqual(entitlements.tier, 'free')
        self.assertEqual(entitlements.daily_topic_limit, 4)
        self.assertTrue(entitlements.can_view_results)
        self.assertFalse(entitlements.can_view_explanations)

    def test_free_plan_row_overrides_the_hardcoded_defaults(self):
        """Cheklovlar kodda emas, admin panelda boshqariladi."""
        make_plan('Bepul', Decimal('0'), code='free', daily_topic_limit=7)
        user = make_user('configured@example.com')

        self.assertEqual(entitlements_for(user).daily_topic_limit, 7)

    def test_pro_plan_removes_the_topic_limit(self):
        plan = make_plan(
            'Pro', Decimal('35000'), code='pro_basic', is_pro=True, daily_topic_limit=4,
        )
        user = make_user('pro@example.com')
        activate_plan(user, plan)

        entitlements = entitlements_for(user)
        self.assertTrue(entitlements.is_pro)
        # `is_pro` limitni bekor qiladi — tarifda son turgan bo'lsa ham.
        self.assertIsNone(entitlements.daily_topic_limit)

    def test_expired_subscription_drops_back_to_free(self):
        plan = make_plan('Pro', Decimal('35000'), code='pro_full', is_pro=True)
        user = make_user('expired@example.com')
        now = timezone.now()
        Subscription.objects.create(
            user=user, plan=plan, status=Subscription.Status.ACTIVE,
            starts_at=now - timedelta(days=40), expires_at=now - timedelta(days=1),
        )

        self.assertEqual(entitlements_for(user).tier, 'free')

    def test_question_count_above_the_plan_ceiling_is_rejected(self):
        make_plan('Bepul', Decimal('0'), code='free', max_question_count=30)
        user = make_user('capped@example.com')
        topic, _ = make_topic_questions(60)

        client = APIClient()
        client.force_authenticate(user)
        response = client.post('/testengine/sessions/', {
            'subject': topic.subject_id, 'question_count': 50,
        }, format='json')

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data['code'], 'question_count_exceeded')


# ---------------------------------------------------------------------------
# Imtihon taymeri
# ---------------------------------------------------------------------------
class ExamTimerTests(BaseFlow):
    def start_exam(self, count=20):
        response = self.client.post(
            f'/testengine/topics/{self.topic.id}/start-test/',
            {'count': count, 'mode': 'exam'}, format='json',
        )
        return TestSession.objects.get(pk=response.data['id']), response

    def test_exam_session_gets_a_server_side_deadline(self):
        session, response = self.start_exam()

        self.assertIsNotNone(session.expires_at)
        self.assertEqual(session.time_limit_seconds, 20 * 90)
        self.assertIsNotNone(response.data['seconds_left'])

    def test_practice_session_has_no_deadline(self):
        response = self.client.post(
            f'/testengine/topics/{self.topic.id}/start-test/',
            {'count': 20, 'mode': 'practice'}, format='json',
        )
        session = TestSession.objects.get(pk=response.data['id'])

        self.assertIsNone(session.expires_at)
        self.assertIsNone(response.data['seconds_left'])

    def test_expired_exam_is_auto_finished_on_the_next_request(self):
        session, _ = self.start_exam()
        TestSession.objects.filter(pk=session.pk).update(
            expires_at=timezone.now() - timedelta(minutes=1)
        )

        response = self.client.get(f'/testengine/sessions/{session.pk}/')

        session.refresh_from_db()
        self.assertTrue(session.is_finished)
        self.assertTrue(session.auto_finished)
        self.assertTrue(response.data['is_finished'])

    def test_answers_are_refused_after_the_deadline(self):
        session, _ = self.start_exam()
        TestSession.objects.filter(pk=session.pk).update(
            expires_at=timezone.now() - timedelta(minutes=1)
        )

        response = self.client.post(
            f'/testengine/sessions/{session.pk}/questions/1/answer/',
            {'selected_option': 'A'}, format='json',
        )
        self.assertEqual(response.status_code, 400)

    def test_background_task_closes_abandoned_exams(self):
        """Foydalanuvchi umuman qaytmasa ham sessiya abadiy ochiq qolmaydi."""
        session, _ = self.start_exam()
        TestSession.objects.filter(pk=session.pk).update(
            expires_at=timezone.now() - timedelta(hours=2)
        )

        self.assertEqual(finish_expired_sessions(), 1)
        session.refresh_from_db()
        self.assertTrue(session.auto_finished)

    def test_duration_is_capped_for_a_session_left_open_for_days(self):
        """«3 kun test ishladi» degan statistika chiqmasligi kerak."""
        response = self.client.post(
            f'/testengine/topics/{self.topic.id}/start-test/',
            {'count': 20}, format='json',
        )
        session_id = response.data['id']
        TestSession.objects.filter(pk=session_id).update(
            started_at=timezone.now() - timedelta(days=3)
        )

        finish = self.client.post(f'/testengine/sessions/{session_id}/finish/')
        # 20 savol x 600 s = 12 000 s shift.
        self.assertLessEqual(finish.data['result']['duration_seconds'], 20 * 600)


# ---------------------------------------------------------------------------
# Savol hayot sikli va statistikasi
# ---------------------------------------------------------------------------
class QuestionLifecycleTests(TestCase):
    def setUp(self):
        cache.clear()
        self.topic, self.questions = make_topic_questions(25)
        self.user = make_user('reader@example.com')
        self.client = APIClient()
        self.client.force_authenticate(self.user)

    def test_draft_questions_never_reach_a_test(self):
        Question.objects.filter(topic=self.topic).update(status=Question.Status.DRAFT)
        self.topic.recount_questions()

        picked = pick_questions(subject=self.topic.subject, count=10, topic_ids=[self.topic.id])
        self.assertEqual(picked, [])

    def test_deactivating_a_question_removes_it_from_the_pool(self):
        """Xato savolni o'chirmasdan muomaladan chiqarish."""
        broken = self.questions[0]
        broken.is_active = False
        broken.save()

        from testengine.services import invalidate_question_pool
        invalidate_question_pool()

        picked = pick_questions(
            subject=self.topic.subject, count=25, topic_ids=[self.topic.id]
        )
        self.assertNotIn(broken.id, [question.id for question in picked])

    def test_topic_counter_follows_question_status(self):
        self.topic.refresh_from_db()
        self.assertEqual(self.topic.available_question_count, 25)

        question = self.questions[0]
        question.status = Question.Status.ARCHIVED
        question.save()

        self.topic.refresh_from_db()
        self.assertEqual(self.topic.available_question_count, 24)

    def test_students_cannot_read_a_draft_question(self):
        question = self.questions[0]
        question.status = Question.Status.DRAFT
        question.save()

        self.assertEqual(
            self.client.get(f'/catalog/questions/{question.id}/').status_code, 404
        )

    def test_mentor_can_read_a_draft_question(self):
        question = self.questions[0]
        question.status = Question.Status.DRAFT
        question.save()

        self.client.force_authenticate(make_user('m@example.com', role='mentor'))
        self.assertEqual(
            self.client.get(f'/catalog/questions/{question.id}/').status_code, 200
        )

    def test_answer_statistics_are_collected_on_finish(self):
        started = self.client.post(
            f'/testengine/topics/{self.topic.id}/start-test/', {'count': 20}, format='json'
        )
        session_id = started.data['id']

        sheet = self.client.get(f'/testengine/sessions/{session_id}/questions/')
        first = sheet.data[0]
        self.client.post(
            f'/testengine/sessions/{session_id}/questions/1/answer/',
            {'selected_option': 'A', 'time_spent_seconds': 42}, format='json',
        )
        self.client.post(f'/testengine/sessions/{session_id}/finish/')

        question = Question.objects.get(pk=first['question']['id'])
        self.assertEqual(question.times_answered, 1)
        self.assertEqual(question.times_correct, 1)
        self.assertEqual(question.total_time_seconds, 42)

    def test_p_value_needs_enough_data(self):
        question = self.questions[0]
        question.times_answered, question.times_correct = 10, 9
        self.assertIsNone(question.p_value)

        question.times_answered, question.times_correct = 100, 90
        self.assertEqual(question.p_value, 0.9)
        self.assertEqual(question.observed_difficulty, 1)
