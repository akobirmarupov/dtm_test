from django.core.cache import cache
from rest_framework.test import APITestCase

from common.testutils import make_question, make_questions, make_user
from progress.models import ReviewCard
from testengine.models import Answer, SessionQuestion, TestResult, TestSession


class SessionOwnershipTests(APITestCase):
    """`raise get_object_or_404(TestSession)` regressiyasi uchun.

    Bu ifoda exception ko'tarmasdan model obyektini qaytarardi, natijada
    begona sessiyaga murojaat 404 emas, 500 bilan tugardi.
    """

    def setUp(self):
        cache.clear()
        self.owner = make_user('owner@example.com')
        self.intruder = make_user('intruder@example.com')
        self.question = make_question()
        self.session = TestSession.objects.create(
            user=self.owner, subject=self.question.topic.subject
        )

    def test_other_users_session_returns_404_not_500(self):
        self.client.force_authenticate(self.intruder)
        response = self.client.get(f'/testengine/sessions/{self.session.id}/')
        self.assertEqual(response.status_code, 404)

    def test_owner_can_read_own_session(self):
        self.client.force_authenticate(self.owner)
        response = self.client.get(f'/testengine/sessions/{self.session.id}/')
        self.assertEqual(response.status_code, 200)


class SessionCreationTests(APITestCase):
    """Sessiya ochilganda savollar qotirilishi kerak."""

    def setUp(self):
        cache.clear()
        self.user = make_user('creator@example.com')
        self.client.force_authenticate(self.user)
        self.questions = make_questions(20)
        self.subject = self.questions[0].topic.subject

    def test_creates_session_with_requested_question_count(self):
        response = self.client.post('/testengine/sessions/', {
            'subject': self.subject.id, 'question_count': 15,
        }, format='json')

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data['question_count'], 15)
        self.assertEqual(
            SessionQuestion.objects.filter(session_id=response.data['id']).count(), 15
        )

    def test_default_question_count_is_15(self):
        response = self.client.post(
            '/testengine/sessions/', {'subject': self.subject.id}, format='json'
        )
        self.assertEqual(response.data['question_count'], 15)

    def test_question_count_shrinks_when_subject_has_fewer_questions(self):
        """"15 ta" deb yozilib, aslida 3 ta savol chiqib qolmasligi kerak."""
        small = make_questions(3, subject_name='Tarix', topic_name='O\'rta asrlar')
        response = self.client.post('/testengine/sessions/', {
            'subject': small[0].topic.subject_id, 'question_count': 15,
        }, format='json')

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data['question_count'], 3)
        self.assertEqual(response.data['total_questions'], 3)

    def test_subject_without_questions_is_rejected(self):
        from catalog.models import Subject
        empty = Subject.objects.create(name='Bo\'sh fan')
        response = self.client.post(
            '/testengine/sessions/', {'subject': empty.id}, format='json'
        )
        self.assertEqual(response.status_code, 400)

    def test_orders_are_stable_between_requests(self):
        response = self.client.post('/testengine/sessions/', {
            'subject': self.subject.id, 'question_count': 5,
        }, format='json')
        session_id = response.data['id']

        first = self.client.get(f'/testengine/sessions/{session_id}/questions/').data
        second = self.client.get(f'/testengine/sessions/{session_id}/questions/').data

        self.assertEqual(
            [item['question']['id'] for item in first],
            [item['question']['id'] for item in second],
        )


class NavigationAndAnswerChangeTests(APITestCase):
    """Asosiy talab: 15 ta savol, 10-savoldan 3-savolga qaytib javobni
    o'zgartirish, natijani faqat yakunda ko'rish."""

    def setUp(self):
        cache.clear()
        self.user = make_user('navigator@example.com')
        self.client.force_authenticate(self.user)
        self.questions = make_questions(15, correct='A')
        self.subject = self.questions[0].topic.subject

        response = self.client.post('/testengine/sessions/', {
            'subject': self.subject.id, 'question_count': 15,
        }, format='json')
        self.session_id = response.data['id']
        self.base = f'/testengine/sessions/{self.session_id}'

    def answer(self, order, option):
        return self.client.post(
            f'{self.base}/questions/{order}/answer/', {'selected_option': option},
            format='json',
        )

    def test_can_answer_any_order_not_only_sequential(self):
        """10-savolga darrov o'tib javob berish mumkin."""
        response = self.answer(10, 'B')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['my_answer']['selected_option'], 'B')

    def test_can_go_back_and_change_earlier_answer(self):
        self.answer(3, 'B')
        self.answer(10, 'C')

        # 3-savolga qaytib javobni to'g'rilaymiz.
        response = self.answer(3, 'A')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['my_answer']['selected_option'], 'A')
        self.assertEqual(Answer.objects.filter(session_id=self.session_id).count(), 2)

    def test_changing_answer_does_not_create_duplicate_rows(self):
        for option in ('A', 'B', 'C', 'D', 'A'):
            self.answer(3, option)

        answers = Answer.objects.filter(session_id=self.session_id)
        self.assertEqual(answers.count(), 1)
        self.assertEqual(answers.first().selected_option, 'A')

    def test_answer_response_hides_correctness_during_test(self):
        response = self.answer(1, 'A')
        self.assertNotIn('is_correct', response.data.get('my_answer', {}))
        self.assertNotIn('correct_option', str(response.data))

    def test_question_list_hides_correct_option(self):
        response = self.client.get(f'{self.base}/questions/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 15)
        for item in response.data:
            self.assertNotIn('correct_option', item)
            self.assertNotIn('is_correct', item)

    def test_answers_list_hides_correctness_during_test(self):
        self.answer(1, 'A')
        response = self.client.get(f'{self.base}/answers/')
        self.assertNotIn('is_correct', response.data['results'][0])

    def test_can_clear_an_answer(self):
        self.answer(4, 'B')
        response = self.client.delete(f'{self.base}/questions/4/answer/')

        self.assertEqual(response.status_code, 200)
        self.assertIsNone(response.data['my_answer'])
        self.assertFalse(Answer.objects.filter(session_id=self.session_id).exists())

    def test_progress_reports_unanswered_orders(self):
        self.answer(1, 'A')
        self.answer(2, 'A')

        response = self.client.get(f'{self.base}/progress/')
        self.assertEqual(response.data['total_questions'], 15)
        self.assertEqual(response.data['answered_count'], 2)
        self.assertEqual(response.data['unanswered_count'], 13)
        self.assertEqual(response.data['unanswered_orders'][0], 3)

    def test_next_question_returns_first_unanswered(self):
        self.answer(1, 'A')
        self.answer(2, 'A')

        response = self.client.get(f'{self.base}/next-question/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['order'], 3)

    def test_invalid_option_is_rejected(self):
        response = self.answer(1, 'Z')
        self.assertEqual(response.status_code, 400)

    def test_out_of_range_order_returns_404(self):
        response = self.answer(99, 'A')
        self.assertEqual(response.status_code, 404)


class FinishAndReviewTests(APITestCase):
    """Yakunlash: natija shu paytda tug'iladi va javoblar qotadi."""

    def setUp(self):
        cache.clear()
        self.user = make_user('finisher@example.com')
        self.client.force_authenticate(self.user)
        self.questions = make_questions(5, correct='A')
        self.subject = self.questions[0].topic.subject

        response = self.client.post('/testengine/sessions/', {
            'subject': self.subject.id, 'question_count': 5,
        }, format='json')
        self.session_id = response.data['id']
        self.base = f'/testengine/sessions/{self.session_id}'

    def answer(self, order, option):
        return self.client.post(
            f'{self.base}/questions/{order}/answer/', {'selected_option': option},
            format='json',
        )

    def test_finish_returns_result_and_review(self):
        self.answer(1, 'A')
        self.answer(2, 'B')

        response = self.client.post(f'{self.base}/finish/')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['result']['correct_count'], 1)
        self.assertEqual(response.data['result']['incorrect_count'], 1)
        self.assertEqual(response.data['result']['unanswered_count'], 3)
        self.assertEqual(response.data['result']['total_questions'], 5)
        self.assertEqual(len(response.data['review']), 5)

    def test_review_exposes_correct_option_after_finish(self):
        self.answer(1, 'B')
        self.client.post(f'{self.base}/finish/')

        response = self.client.get(f'{self.base}/review/')
        first = response.data['review'][0]

        self.assertEqual(first['correct_option'], 'A')
        self.assertIn('is_correct', first)

    def test_review_is_blocked_before_finish(self):
        response = self.client.get(f'{self.base}/review/')
        self.assertEqual(response.status_code, 400)

    def test_final_answer_decides_the_score(self):
        """Xato javobni yakunlashdan oldin to'g'rilagan bo'lsa — ball beriladi."""
        self.answer(1, 'B')
        self.answer(1, 'A')

        response = self.client.post(f'{self.base}/finish/')
        self.assertEqual(response.data['result']['correct_count'], 1)
        self.assertEqual(response.data['result']['incorrect_count'], 0)

    def test_answers_are_frozen_after_finish(self):
        self.answer(1, 'B')
        self.client.post(f'{self.base}/finish/')

        response = self.answer(1, 'A')
        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            Answer.objects.get(session_id=self.session_id).selected_option, 'B'
        )

    def test_cannot_clear_answer_after_finish(self):
        self.answer(1, 'A')
        self.client.post(f'{self.base}/finish/')

        response = self.client.delete(f'{self.base}/questions/1/answer/')
        self.assertEqual(response.status_code, 400)

    def test_double_finish_is_rejected_and_creates_one_result(self):
        self.answer(1, 'A')
        self.client.post(f'{self.base}/finish/')
        second = self.client.post(f'{self.base}/finish/')

        self.assertEqual(second.status_code, 400)
        self.assertEqual(TestResult.objects.filter(session_id=self.session_id).count(), 1)

    def test_review_card_uses_final_answer_not_intermediate(self):
        """Xato javob keyin to'g'rilangan bo'lsa, takrorlash kartasi ochilmaydi."""
        self.answer(1, 'B')   # xato
        self.answer(1, 'A')   # to'g'rilandi
        self.answer(2, 'B')   # xato bo'lib qoldi
        self.client.post(f'{self.base}/finish/')

        cards = ReviewCard.objects.filter(user=self.user).values_list(
            'question_id', flat=True
        )
        answered_wrong = Answer.objects.get(
            session_id=self.session_id, selected_option='B'
        ).question_id

        self.assertEqual(list(cards), [answered_wrong])


class SessionLocalisationTests(APITestCase):
    """Test topshirayotgan foydalanuvchi savolni O'Z TILIDA ko'rishi kerak."""

    def setUp(self):
        cache.clear()
        self.user = make_user('lang-session@example.com')
        self.client.force_authenticate(self.user)

        from catalog.models import Question, Subject, Topic
        subject = Subject.objects.create(name='Matematika', name_ru='Математика')
        topic = Topic.objects.create(subject=subject, name='Algebra', name_ru='Алгебра')
        Question.objects.create(
            topic=topic,
            text='2 + 2 nechchi?', text_ru='Сколько будет 2 + 2?',
            options={'A': "To'rt", 'B': 'Besh'},
            options_ru={'A': 'Четыре', 'B': 'Пять'},
            correct_option='A',
        )

        response = self.client.post('/testengine/sessions/', {
            'subject': subject.id, 'question_count': 1,
        }, format='json')
        self.base = f'/testengine/sessions/{response.data["id"]}'

    def test_questions_are_served_in_requested_language(self):
        response = self.client.get(f'{self.base}/questions/?lang=ru')
        question = response.data[0]['question']

        self.assertEqual(question['text'], 'Сколько будет 2 + 2?')
        self.assertEqual(question['options']['A'], 'Четыре')

    def test_questions_default_to_uzbek(self):
        response = self.client.get(f'{self.base}/questions/')
        self.assertEqual(response.data[0]['question']['text'], '2 + 2 nechchi?')

    def test_option_keys_stay_identical_across_languages(self):
        """Javob kaliti (A/B) tildan qat'i nazar bir xil bo'lishi shart."""
        uz = self.client.get(f'{self.base}/questions/').data[0]['question']
        ru = self.client.get(f'{self.base}/questions/?lang=ru').data[0]['question']

        self.assertEqual(sorted(uz['options']), sorted(ru['options']))

    def test_answer_given_in_russian_is_graded_correctly(self):
        self.client.post(
            f'{self.base}/questions/1/answer/?lang=ru',
            {'selected_option': 'A'}, format='json',
        )
        response = self.client.post(f'{self.base}/finish/')
        self.assertEqual(response.data['result']['correct_count'], 1)

    def test_question_image_is_exposed_to_the_test_taker(self):
        from django.core.files.uploadedfile import SimpleUploadedFile
        from catalog.tests import png_bytes
        from catalog.models import Question

        question = Question.objects.first()
        question.image = SimpleUploadedFile(
            'grafik.png', png_bytes(), content_type='image/png'
        )
        question.image_caption = 'Grafik'
        question.save(update_fields=['image', 'image_caption'])

        response = self.client.get(f'{self.base}/questions/')
        payload = response.data[0]['question']

        self.assertTrue(payload['has_image'])
        self.assertIn('.png', payload['image'])
        self.assertEqual(payload['image_caption'], 'Grafik')


class SyncTests(APITestCase):
    """Offline sync `answer_data['is_correct']` regressiyasi uchun.

    `BulkAnswerItemSerializer` da bunday maydon yo'q edi -> KeyError -> 500.
    Endi `is_correct` serverda `correct_option` bilan solishtirib hisoblanadi.
    """

    def setUp(self):
        cache.clear()
        self.user = make_user('sync@example.com')
        self.client.force_authenticate(self.user)
        self.question = make_question(correct='A')
        self.session = TestSession.objects.create(
            user=self.user, subject=self.question.topic.subject
        )
        self.url = f'/testengine/sessions/{self.session.id}/sync/'

    def test_sync_succeeds_without_client_supplied_is_correct(self):
        response = self.client.post(self.url, {
            'answers': [{'question': self.question.id, 'selected_option': 'A'}]
        }, format='json')
        self.assertIn(response.status_code, (200, 201))

    def test_is_correct_is_computed_server_side(self):
        self.client.post(self.url, {
            'answers': [{'question': self.question.id, 'selected_option': 'A'}]
        }, format='json')
        self.assertTrue(Answer.objects.get(session=self.session).is_correct)

    def test_wrong_option_is_marked_incorrect(self):
        self.client.post(self.url, {
            'answers': [{'question': self.question.id, 'selected_option': 'B'}]
        }, format='json')
        self.assertFalse(Answer.objects.get(session=self.session).is_correct)

    def test_sync_is_idempotent(self):
        payload = {'answers': [{'question': self.question.id, 'selected_option': 'A'}]}
        self.client.post(self.url, payload, format='json')
        self.client.post(self.url, payload, format='json')
        # Offline mijoz qayta yuborsa dublikat yaratilmasligi kerak.
        self.assertEqual(Answer.objects.filter(session=self.session).count(), 1)

    def test_question_from_another_subject_is_rejected(self):
        foreign = make_question(subject_name='Tarix', topic_name='O\'rta asrlar')
        response = self.client.post(self.url, {
            'answers': [{'question': foreign.id, 'selected_option': 'A'}]
        }, format='json')
        self.assertEqual(response.status_code, 400)
        self.assertEqual(Answer.objects.filter(session=self.session).count(), 0)

    def test_duplicate_question_in_payload_is_rejected(self):
        response = self.client.post(self.url, {
            'answers': [
                {'question': self.question.id, 'selected_option': 'A'},
                {'question': self.question.id, 'selected_option': 'B'},
            ]
        }, format='json')
        self.assertEqual(response.status_code, 400)


class AnswerSubjectScopingTests(APITestCase):
    """Javob yuborishda savol sessiyaga tegishli bo'lishi shart."""

    def setUp(self):
        cache.clear()
        self.user = make_user('answer@example.com')
        self.client.force_authenticate(self.user)
        self.question = make_question(correct='A')
        self.foreign = make_question(subject_name='Tarix', topic_name='O\'rta asrlar')
        self.session = TestSession.objects.create(
            user=self.user, subject=self.question.topic.subject
        )
        self.url = f'/testengine/sessions/{self.session.id}/answers/'

    def test_own_subject_question_accepted(self):
        response = self.client.post(self.url, {
            'question': self.question.id, 'selected_option': 'A'
        }, format='json')
        self.assertIn(response.status_code, (200, 201))

    def test_foreign_subject_question_rejected(self):
        response = self.client.post(self.url, {
            'question': self.foreign.id, 'selected_option': 'A'
        }, format='json')
        self.assertEqual(response.status_code, 400)

    def test_bulk_foreign_subject_question_rejected(self):
        response = self.client.post(f'{self.url}bulk/', {
            'answers': [{'question': self.foreign.id, 'selected_option': 'A'}]
        }, format='json')
        self.assertEqual(response.status_code, 400)
        self.assertEqual(Answer.objects.filter(session=self.session).count(), 0)

    def test_question_outside_pinned_list_is_rejected(self):
        """Sessiyaga biriktirilmagan savolga javob berib bo'lmaydi."""
        questions = make_questions(3, subject_name='Kimyo', topic_name='Organik')
        create = self.client.post('/testengine/sessions/', {
            'subject': questions[0].topic.subject_id, 'question_count': 2,
        }, format='json')
        session_id = create.data['id']

        pinned = set(
            SessionQuestion.objects.filter(session_id=session_id)
            .values_list('question_id', flat=True)
        )
        outsider = next(q for q in questions if q.id not in pinned)

        response = self.client.post(
            f'/testengine/sessions/{session_id}/answers/',
            {'question': outsider.id, 'selected_option': 'A'}, format='json',
        )
        self.assertEqual(response.status_code, 400)
