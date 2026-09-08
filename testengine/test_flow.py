"""Yangi test oqimi: sinf ierarxiyasi, savol soni bosqichlari, guest, limit.

Bu yerdagi testlar TZ dagi biznes-qoidalarni bevosita tekshiradi — kod
o'zgarganda qaysi QOIDA buzilgani darrov ko'rinishi uchun.
"""

from datetime import timedelta
from decimal import Decimal

from django.core.cache import cache
from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient

from billing.models import Subscription
from catalog.models import Grade, Question, Subject, Topic
from common.testutils import make_plan, make_topic_questions, make_user
from testengine.access import get_available_tiers
from testengine.models import (
    DailyTopicUsage,
    SessionQuestion,
    TestSession,
)


def activate_plan(user, plan, days=30):
    now = timezone.now()
    return Subscription.objects.create(
        user=user, plan=plan, status=Subscription.Status.ACTIVE,
        starts_at=now, expires_at=now + timedelta(days=days),
    )


# ---------------------------------------------------------------------------
# Savol soni bosqichlari
# ---------------------------------------------------------------------------
class AvailableTiersTests(TestCase):
    """`get_available_tiers()` — TZ 3.3 dagi algoritm.

    Chegara holatlari ataylab tekshiriladi: aynan shu yerda "43 ta savol
    bo'lsa 45 ni ko'rsatib qo'yish" xatosi tug'iladi.
    """

    def test_below_minimum_returns_nothing(self):
        for total in (0, 1, 19):
            self.assertEqual(get_available_tiers(total), [], f'total={total}')

    def test_exactly_twenty_opens_the_first_tier(self):
        self.assertEqual(get_available_tiers(20), [20])

    def test_forty_three_does_not_offer_forty_five(self):
        self.assertEqual(get_available_tiers(43), [20, 25, 30, 35, 40])

    def test_forty_five_adds_the_next_tier(self):
        self.assertEqual(get_available_tiers(45), [20, 25, 30, 35, 40, 45])

    def test_fifty_nine_stops_at_fifty_five(self):
        self.assertEqual(get_available_tiers(59), [20, 25, 30, 35, 40, 45, 50, 55])

    def test_sixty_opens_every_tier(self):
        self.assertEqual(get_available_tiers(60), [20, 25, 30, 35, 40, 45, 50, 55, 60])

    def test_above_sixty_is_still_capped_at_sixty(self):
        """Mavzuda 500 ta savol bo'lsa ham maksimal tanlov — 60."""
        self.assertEqual(get_available_tiers(500)[-1], 60)


# ---------------------------------------------------------------------------
# Fan -> Sinf -> Mavzu ierarxiyasi
# ---------------------------------------------------------------------------
class GradeHierarchyTests(TestCase):
    def setUp(self):
        cache.clear()
        self.admin = make_user('admin@example.com', role='admin')
        self.client = APIClient()
        self.client.force_authenticate(self.admin)
        self.subject = Subject.objects.create(name='Matematika')

    def test_grade_name_is_free_text(self):
        """Sinf raqam bilan cheklanmaydi — kitob nomi ham bo'lishi mumkin."""
        response = self.client.post('/catalog/grades/', {
            'subject': self.subject.id,
            'name': 'Milliy sertifikat uchun',
            'order': 10,
        }, format='json')

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data['name'], 'Milliy sertifikat uchun')

    def test_grades_are_ordered_by_order_not_alphabet(self):
        """Alifbo bo'yicha «10-sinf» «7-sinf» dan oldin chiqib qolardi."""
        Grade.objects.create(subject=self.subject, name='10-sinf', order=10)
        Grade.objects.create(subject=self.subject, name='7-sinf', order=7)

        response = self.client.get(f'/catalog/grades/?subject={self.subject.id}')
        names = [item['name'] for item in response.data['results']]
        self.assertEqual(names, ['7-sinf', '10-sinf'])

    def test_topic_derives_subject_from_grade(self):
        grade = Grade.objects.create(subject=self.subject, name='7-sinf')
        response = self.client.post('/catalog/topics/', {
            'grade': grade.id, 'name': 'Qisqa ko\'paytirish formulalari',
        }, format='json')

        self.assertEqual(response.status_code, 201)
        topic = Topic.objects.get(pk=response.data['id'])
        self.assertEqual(topic.subject_id, self.subject.id)

    def test_topic_requires_a_grade(self):
        response = self.client.post('/catalog/topics/', {'name': 'Mavzu'}, format='json')
        self.assertEqual(response.status_code, 400)
        self.assertIn('grade', response.data)

    def test_duplicate_topic_inside_one_grade_is_rejected(self):
        grade = Grade.objects.create(subject=self.subject, name='7-sinf')
        Topic.objects.create(grade=grade, name='Algebra')

        response = self.client.post('/catalog/topics/', {
            'grade': grade.id, 'name': 'algebra',
        }, format='json')
        self.assertEqual(response.status_code, 400)

    def test_same_topic_name_is_allowed_in_another_grade(self):
        """«Algebra» 7-sinfda ham, 8-sinfda ham bo'lishi mumkin."""
        seven = Grade.objects.create(subject=self.subject, name='7-sinf')
        eight = Grade.objects.create(subject=self.subject, name='8-sinf')
        Topic.objects.create(grade=seven, name='Algebra')

        response = self.client.post('/catalog/topics/', {
            'grade': eight.id, 'name': 'Algebra',
        }, format='json')
        self.assertEqual(response.status_code, 201)

    def test_grade_with_topics_cannot_be_deleted(self):
        grade = Grade.objects.create(subject=self.subject, name='7-sinf')
        Topic.objects.create(grade=grade, name='Algebra')

        response = self.client.delete(f'/catalog/grades/{grade.id}/')
        self.assertEqual(response.status_code, 409)


# ---------------------------------------------------------------------------
# `available-counts` va `start-test`
# ---------------------------------------------------------------------------
class TopicTestFlowTests(TestCase):
    def setUp(self):
        cache.clear()
        self.user = make_user('student@example.com')
        self.client = APIClient()
        self.client.force_authenticate(self.user)
        self.topic, _ = make_topic_questions(43)

    def test_available_counts_reflect_question_total(self):
        response = self.client.get(f'/testengine/topics/{self.topic.id}/available-counts/')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['tiers'], [20, 25, 30, 35, 40])
        self.assertTrue(response.data['is_available'])

    def test_available_counts_hide_the_question_total_from_students(self):
        """Foydalanuvchi bazada nechta savol borligini bilmasligi kerak."""
        response = self.client.get(f'/testengine/topics/{self.topic.id}/available-counts/')
        self.assertIsNone(response.data['question_count'])

    def test_mentor_sees_the_question_total(self):
        mentor = make_user('mentor@example.com', role='mentor')
        self.client.force_authenticate(mentor)

        response = self.client.get(f'/testengine/topics/{self.topic.id}/available-counts/')
        self.assertEqual(response.data['question_count'], 43)

    def test_topic_below_minimum_is_not_available(self):
        small, _ = make_topic_questions(19, topic_name='Kichik mavzu')

        response = self.client.get(f'/testengine/topics/{small.id}/available-counts/')
        self.assertEqual(response.data['tiers'], [])
        self.assertFalse(response.data['is_available'])
        self.assertIsNotNone(response.data['reason'])

    def test_start_test_creates_a_session_with_the_chosen_count(self):
        response = self.client.post(
            f'/testengine/topics/{self.topic.id}/start-test/', {'count': 30}, format='json'
        )

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data['question_count'], 30)
        self.assertEqual(
            SessionQuestion.objects.filter(session_id=response.data['id']).count(), 30
        )

    def test_start_test_rejects_a_count_the_topic_cannot_serve(self):
        """43 ta savolli mavzuda 45 ta so'ralsa — aniq xato, jim qisqartirish emas."""
        response = self.client.post(
            f'/testengine/topics/{self.topic.id}/start-test/', {'count': 45}, format='json'
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data['code'], 'invalid_count')

    def test_start_test_rejects_a_count_outside_the_tiers(self):
        response = self.client.post(
            f'/testengine/topics/{self.topic.id}/start-test/', {'count': 23}, format='json'
        )
        self.assertEqual(response.status_code, 400)

    def test_session_remembers_the_topic_and_grade(self):
        response = self.client.post(
            f'/testengine/topics/{self.topic.id}/start-test/', {'count': 20}, format='json'
        )
        session = TestSession.objects.get(pk=response.data['id'])

        self.assertEqual(session.topic_id, self.topic.id)
        self.assertEqual(session.grade_id, self.topic.grade_id)


# ---------------------------------------------------------------------------
# Kunlik mavzu limiti (Free)
# ---------------------------------------------------------------------------
class DailyTopicLimitTests(TestCase):
    def setUp(self):
        cache.clear()
        self.user = make_user('free@example.com')
        self.client = APIClient()
        self.client.force_authenticate(self.user)
        self.topics = [
            make_topic_questions(20, topic_name=f'Mavzu {index}')[0]
            for index in range(1, 7)
        ]

    def start(self, topic, count=20):
        return self.client.post(
            f'/testengine/topics/{topic.id}/start-test/', {'count': count}, format='json'
        )

    def test_four_topics_are_allowed_per_day(self):
        for topic in self.topics[:4]:
            self.assertEqual(self.start(topic).status_code, 201, topic.name)

    def test_fifth_topic_is_blocked_with_an_upgrade_prompt(self):
        for topic in self.topics[:4]:
            self.start(topic)

        response = self.start(self.topics[4])

        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.data['code'], 'daily_topic_limit_reached')
        self.assertTrue(response.data['upgrade_required'])
        self.assertEqual(response.data['daily_topic_limit'], 4)
        self.assertIn('reset_at', response.data)

    def test_the_limit_counts_topics_not_tests(self):
        """Bitta mavzuda 5 marta test ishlash ham «1 ta mavzu» hisoblanadi."""
        for _ in range(5):
            self.assertEqual(self.start(self.topics[0]).status_code, 201)

        self.assertEqual(
            DailyTopicUsage.objects.filter(user=self.user).count(), 1
        )
        # Limitdan faqat bitta joy ketgan — qolgan uchtasi hali ochiq.
        for topic in self.topics[1:4]:
            self.assertEqual(self.start(topic).status_code, 201)

    def test_yesterdays_usage_does_not_count_today(self):
        yesterday = timezone.localdate() - timedelta(days=1)
        for topic in self.topics[:4]:
            DailyTopicUsage.objects.create(user=self.user, topic=topic, date=yesterday)

        self.assertEqual(self.start(self.topics[4]).status_code, 201)

    def test_pro_user_has_no_topic_limit(self):
        plan = make_plan('Pro-Full', Decimal('59000'), is_pro=True, code='pro_full')
        activate_plan(self.user, plan)

        for topic in self.topics:
            self.assertEqual(self.start(topic).status_code, 201, topic.name)

    def test_my_limits_reports_the_remaining_topics(self):
        self.start(self.topics[0])

        response = self.client.get('/testengine/my-limits/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['daily_topic_limit'], 4)
        self.assertEqual(response.data['topics_used_today'], 1)
        self.assertEqual(response.data['topics_remaining_today'], 3)

    def test_usage_is_not_recorded_when_the_session_cannot_start(self):
        """Savol yetmay sessiya ochilmasa, limitdan joy yemasligi kerak."""
        empty, _ = make_topic_questions(0, topic_name='Bo\'sh mavzu')

        self.start(empty)
        self.assertFalse(
            DailyTopicUsage.objects.filter(user=self.user, topic=empty).exists()
        )


# ---------------------------------------------------------------------------
# Guest oqimi
# ---------------------------------------------------------------------------
class GuestFlowTests(TestCase):
    def setUp(self):
        cache.clear()
        self.client = APIClient()
        self.topic, _ = make_topic_questions(43)

    def start(self):
        return self.client.post(
            '/testengine/guest/start/', {'topic': self.topic.id}, format='json'
        )

    def test_guest_gets_exactly_twenty_questions(self):
        response = self.start()

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data['question_count'], 20)
        self.assertEqual(len(response.data['questions']), 20)

    def test_guest_questions_never_include_the_answer(self):
        response = self.start()
        for question in response.data['questions']:
            self.assertNotIn('correct_option', question)

    def test_guest_session_is_not_stored(self):
        self.start()
        self.assertEqual(TestSession.objects.count(), 0)
        self.assertEqual(SessionQuestion.objects.count(), 0)

    def test_guest_submit_returns_a_registration_prompt_instead_of_results(self):
        started = self.start()
        question_ids = [item['id'] for item in started.data['questions']]

        response = self.client.post('/testengine/guest/submit/', {
            'token': started.data['token'],
            'answers': [{'question': qid, 'selected_option': 'A'} for qid in question_ids],
        }, format='json')

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.data['requires_registration'])
        self.assertTrue(response.data['results_hidden'])
        # Natijaning HECH BIR ko'rinishi qaytmasligi kerak.
        for leaked in ('correct_count', 'total_score', 'accuracy_percent', 'score'):
            self.assertNotIn(leaked, response.data)

    def test_guest_submit_offers_both_actions(self):
        started = self.start()
        response = self.client.post(
            '/testengine/guest/submit/', {'token': started.data['token']}, format='json'
        )
        codes = [action['code'] for action in response.data['actions']]
        self.assertEqual(codes, ['register', 'later'])

    def test_guest_submit_rejects_a_forged_token(self):
        response = self.client.post(
            '/testengine/guest/submit/', {'token': 'soxta-token'}, format='json'
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data['code'], 'invalid_token')

    def test_guest_answers_are_not_saved(self):
        from testengine.models import Answer

        started = self.start()
        self.client.post('/testengine/guest/submit/', {
            'token': started.data['token'],
            'answers': [
                {'question': started.data['questions'][0]['id'], 'selected_option': 'A'}
            ],
        }, format='json')

        self.assertEqual(Answer.objects.count(), 0)

    def test_topic_without_twenty_questions_is_refused(self):
        small, _ = make_topic_questions(19, topic_name='Kichik')
        response = self.client.post(
            '/testengine/guest/start/', {'topic': small.id}, format='json'
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data['code'], 'not_enough_questions')

    def test_guest_topics_only_lists_playable_topics(self):
        make_topic_questions(19, topic_name='Kichik')

        response = self.client.get('/testengine/guest/topics/')
        names = [item['name'] for item in response.data['results']]
        self.assertIn(self.topic.name, names)
        self.assertNotIn('Kichik', names)
