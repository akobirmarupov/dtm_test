"""Kirish testi: tasodifiy 4 ta savol, faqat ro'yxatdan o'tmaganlar uchun."""

from django.core.cache import cache
from rest_framework.test import APITestCase

from common.models import Role
from common.testutils import make_user
from intro.models import IntroQuestion
from intro.tokens import issue_token


def make_question(text='Qatordagi keyingi son nechchi?', kind=IntroQuestion.Kind.LOGIC,
                  correct='A', **extra):
    return IntroQuestion.objects.create(
        text=text, kind=kind,
        options=extra.pop('options', {'A': '8', 'B': '9', 'C': '10', 'D': '11'}),
        correct_option=correct, **extra,
    )


class IntroFlowTests(APITestCase):
    def setUp(self):
        cache.clear()
        self.questions = [make_question(text=f'Savol {i}') for i in range(1, 11)]

    def test_guest_gets_exactly_four_questions_with_a_token(self):
        response = self.client.get('/intro/start/')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['question_count'], 4)
        self.assertEqual(len(response.data['questions']), 4)
        self.assertTrue(response.data['token'])

    def test_correct_answer_is_never_sent_to_the_client(self):
        response = self.client.get('/intro/start/')

        for question in response.data['questions']:
            self.assertNotIn('correct_option', question)

    def test_questions_are_random(self):
        """Ko'p marta so'ralganda to'plam o'zgarib turishi kerak."""
        seen = set()
        for _ in range(6):
            response = self.client.get('/intro/start/')
            self.assertEqual(response.status_code, 200, response.data)
            seen.add(tuple(q['id'] for q in response.data['questions']))

        self.assertGreater(len(seen), 1, 'Har safar bir xil savollar chiqyapti')

    def test_registered_user_does_not_see_the_intro_test(self):
        self.client.force_authenticate(make_user('registered@example.com'))

        response = self.client.get('/intro/start/')

        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.data['code'], 'already_registered')

    def test_not_enough_questions_returns_a_clear_error(self):
        IntroQuestion.objects.update(is_active=False)

        response = self.client.get('/intro/start/')

        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.data['code'], 'not_enough_questions')

    def test_submit_scores_the_logic_questions(self):
        started = self.client.get('/intro/start/')
        asked = started.data['questions']
        answers = [
            {'question': asked[0]['id'], 'selected_option': 'A'},   # to'g'ri
            {'question': asked[1]['id'], 'selected_option': 'B'},   # xato
        ]

        response = self.client.post('/intro/submit/', {
            'token': started.data['token'], 'answers': answers,
        }, format='json')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['question_count'], 4)
        self.assertEqual(response.data['answered_count'], 2)
        self.assertEqual(response.data['correct_count'], 1)
        self.assertEqual(response.data['scored_count'], 4)
        self.assertTrue(response.data['registration_required'])

    def test_psychological_question_has_no_right_answer(self):
        IntroQuestion.objects.all().delete()
        for index in range(4):
            make_question(
                text=f'Qaysi biri sizga yaqin? {index}',
                kind=IntroQuestion.Kind.PSYCHOLOGY, correct='',
            )

        started = self.client.get('/intro/start/')
        response = self.client.post('/intro/submit/', {
            'token': started.data['token'],
            'answers': [{
                'question': started.data['questions'][0]['id'],
                'selected_option': 'C',
            }],
        }, format='json')

        self.assertEqual(response.data['scored_count'], 0)
        self.assertEqual(response.data['correct_count'], 0)
        self.assertIsNone(response.data['results'][0]['is_correct'])

    def test_answers_outside_the_token_are_ignored(self):
        other = make_question(text='Boshqa savol')
        token = issue_token([self.questions[0].id])

        response = self.client.post('/intro/submit/', {
            'token': token,
            'answers': [{'question': other.id, 'selected_option': 'A'}],
        }, format='json')

        self.assertEqual(response.data['answered_count'], 0)

    def test_broken_token_is_rejected(self):
        response = self.client.post('/intro/submit/', {
            'token': 'aldamchi-token', 'answers': [],
        }, format='json')

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data['code'], 'invalid_token')


class IntroAdminTests(APITestCase):
    def setUp(self):
        cache.clear()
        self.admin = make_user('intro-admin@example.com', role=Role.ADMIN)
        self.client.force_authenticate(self.admin)

    def payload(self, **overrides):
        data = {
            'kind': 'logic',
            'text': "Ikkita olma va uchta olma — jami nechta?",
            'options': {'A': '4', 'B': '5', 'C': '6'},
            'correct_option': 'B',
            'video_url': 'https://youtu.be/example',
        }
        data.update(overrides)
        return data

    def test_admin_creates_a_question(self):
        response = self.client.post('/intro/admin/questions/', self.payload(), format='json')

        self.assertEqual(response.status_code, 201, response.data)
        self.assertEqual(response.data['correct_option'], 'B')

    def test_logic_question_requires_a_correct_answer(self):
        response = self.client.post(
            '/intro/admin/questions/', self.payload(correct_option=''), format='json'
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn('correct_option', response.data)

    def test_correct_answer_must_be_one_of_the_options(self):
        response = self.client.post(
            '/intro/admin/questions/', self.payload(correct_option='Z'), format='json'
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn('correct_option', response.data)

    def test_psychological_question_must_not_have_one(self):
        response = self.client.post(
            '/intro/admin/questions/',
            self.payload(kind='psychology', correct_option='A'), format='json',
        )

        self.assertEqual(response.status_code, 400)

    def test_at_least_two_options(self):
        response = self.client.post(
            '/intro/admin/questions/',
            self.payload(options={'A': 'Yagona'}, correct_option='A'), format='json',
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn('options', response.data)

    def test_question_can_be_edited_and_deleted(self):
        created = self.client.post('/intro/admin/questions/', self.payload(), format='json')
        question_id = created.data['id']

        edited = self.client.patch(
            f'/intro/admin/questions/{question_id}/', {'is_active': False}, format='json'
        )
        self.assertEqual(edited.status_code, 200)
        self.assertFalse(edited.data['is_active'])

        deleted = self.client.delete(f'/intro/admin/questions/{question_id}/')
        self.assertEqual(deleted.status_code, 204)
        self.assertFalse(IntroQuestion.objects.filter(pk=question_id).exists())

    def test_student_cannot_manage_questions(self):
        self.client.force_authenticate(make_user('student@example.com'))

        self.assertEqual(self.client.get('/intro/admin/questions/').status_code, 403)
        self.assertEqual(
            self.client.post('/intro/admin/questions/', self.payload(), format='json').status_code,
            403,
        )
