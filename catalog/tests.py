import io

from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from PIL import Image
from rest_framework.test import APITestCase

from catalog.models import Question, Subject, Topic
from common.models import Role
from common.testutils import make_question, make_user


def png_bytes(size=(20, 20), color=(120, 200, 160)):
    """Haqiqiy PNG bayt-ketma-ketligi — `ImageField` Pillow bilan tekshiradi."""
    buffer = io.BytesIO()
    Image.new('RGB', size, color).save(buffer, format='PNG')
    return buffer.getvalue()


class SubjectListTests(APITestCase):
    """`CACHE_DURATION[...]` (Ellipsis) regressiyasi uchun.

    Ilgari har bir cache miss'da `KeyError: Ellipsis` -> 500 qaytardi.
    """

    def setUp(self):
        cache.clear()
        self.user = make_user('student@example.com')
        self.client.force_authenticate(self.user)
        make_question(subject_name='Matematika')
        make_question(subject_name='Fizika')

    def test_list_returns_200_on_cache_miss(self):
        response = self.client.get('/catalog/subjects/')
        self.assertEqual(response.status_code, 200)

    def test_list_is_paginated(self):
        response = self.client.get('/catalog/subjects/')
        # Ilgari paginatsiya qurilib, keyin tashlab yuborilardi.
        self.assertIn('results', response.data)
        self.assertIn('count', response.data)
        self.assertEqual(response.data['count'], 2)

    def test_second_call_hits_cache_and_matches(self):
        first = self.client.get('/catalog/subjects/')
        second = self.client.get('/catalog/subjects/')
        self.assertEqual(second.status_code, 200)
        self.assertEqual(first.data['results'], second.data['results'])


class TopicListPaginationTests(APITestCase):
    """`TopicList` paginatsiyani qurib, keyin uni tashlab yuborardi va
    butun ro'yxatni qaytarardi — Subject/Question bilan bir xil bo'lishi kerak."""

    def setUp(self):
        cache.clear()
        self.user = make_user('topics@example.com')
        self.client.force_authenticate(self.user)
        subject = Subject.objects.create(name='Matematika')
        for index in range(3):
            Topic.objects.create(subject=subject, name=f'Mavzu {index}')

    def test_topic_list_is_paginated(self):
        response = self.client.get('/catalog/topics/')

        self.assertEqual(response.status_code, 200)
        self.assertIn('results', response.data)
        self.assertEqual(response.data['count'], 3)


class TranslationTests(APITestCase):
    """Uch til: uz (asosiy), ru, en."""

    def setUp(self):
        cache.clear()
        self.user = make_user('lang@example.com')
        self.client.force_authenticate(self.user)

        self.subject = Subject.objects.create(
            name='Matematika', name_ru='Математика', name_en='Mathematics'
        )
        self.topic = Topic.objects.create(
            subject=self.subject, name='Algebra', name_ru='Алгебра', name_en='Algebra'
        )
        self.question = Question.objects.create(
            topic=self.topic,
            text='2 + 2 nechchi?',
            text_ru='Сколько будет 2 + 2?',
            text_en='What is 2 + 2?',
            options={'A': 'To\'rt', 'B': 'Besh'},
            options_ru={'A': 'Четыре', 'B': 'Пять'},
            options_en={'A': 'Four', 'B': 'Five'},
            correct_option='A',
        )

    def test_default_language_is_uzbek(self):
        response = self.client.get('/catalog/subjects/')
        self.assertEqual(response.data['results'][0]['name'], 'Matematika')

    def test_lang_query_parameter_switches_language(self):
        response = self.client.get('/catalog/subjects/?lang=ru')
        self.assertEqual(response.data['results'][0]['name'], 'Математика')

    def test_x_language_header_switches_language(self):
        response = self.client.get('/catalog/subjects/', HTTP_X_LANGUAGE='en')
        self.assertEqual(response.data['results'][0]['name'], 'Mathematics')

    def test_accept_language_header_is_honoured_when_profile_language_unset(self):
        self.user.language = ''
        self.user.save(update_fields=['language'])

        response = self.client.get(
            '/catalog/subjects/', HTTP_ACCEPT_LANGUAGE='ru-RU,ru;q=0.9,en;q=0.8'
        )
        self.assertEqual(response.data['results'][0]['name'], 'Математика')

    def test_user_profile_language_is_used_when_nothing_else_given(self):
        self.user.language = 'en'
        self.user.save(update_fields=['language'])

        response = self.client.get('/catalog/subjects/')
        self.assertEqual(response.data['results'][0]['name'], 'Mathematics')

    def test_profile_language_wins_over_accept_language(self):
        """Foydalanuvchi ilovada tilni tanlagan bo'lsa, telefon tili emas,
        uning tanlovi ustun bo'ladi."""
        self.user.language = 'uz'
        self.user.save(update_fields=['language'])

        response = self.client.get('/catalog/subjects/', HTTP_ACCEPT_LANGUAGE='ru')
        self.assertEqual(response.data['results'][0]['name'], 'Matematika')

    def test_lang_parameter_wins_over_profile_language(self):
        self.user.language = 'uz'
        self.user.save(update_fields=['language'])

        response = self.client.get('/catalog/subjects/?lang=en')
        self.assertEqual(response.data['results'][0]['name'], 'Mathematics')

    def test_question_text_and_options_are_translated_together(self):
        response = self.client.get(f'/catalog/questions/{self.question.id}/?lang=ru')

        self.assertEqual(response.data['text'], 'Сколько будет 2 + 2?')
        self.assertEqual(response.data['options']['A'], 'Четыре')

    def test_missing_translation_falls_back_to_uzbek(self):
        subject = Subject.objects.create(name='Tarix')
        response = self.client.get(f'/catalog/subjects/{subject.id}/?lang=ru')
        self.assertEqual(response.data['name'], 'Tarix')

    def test_cache_does_not_leak_between_languages(self):
        """Ruscha so'rovga o'zbekcha keshdan javob kelmasligi kerak."""
        self.client.get('/catalog/subjects/')
        response = self.client.get('/catalog/subjects/?lang=ru')
        self.assertEqual(response.data['results'][0]['name'], 'Математика')

    def test_translations_block_exposes_every_language(self):
        response = self.client.get('/catalog/subjects/')
        translations = response.data['results'][0]['translations']

        self.assertEqual(translations['uz'], 'Matematika')
        self.assertEqual(translations['ru'], 'Математика')
        self.assertEqual(translations['en'], 'Mathematics')

    def test_unknown_language_falls_back_to_default(self):
        response = self.client.get('/catalog/subjects/?lang=fr')
        self.assertEqual(response.data['results'][0]['name'], 'Matematika')


class QuestionAuthoringTests(APITestCase):
    """Savol yaratish: rasm IXTIYORIY, tarjimalar ixtiyoriy."""

    def setUp(self):
        cache.clear()
        self.mentor = make_user('mentor@example.com', role=Role.MENTOR)
        self.student = make_user('pupil@example.com')
        self.client.force_authenticate(self.mentor)

        self.subject = Subject.objects.create(name='Fizika')
        self.topic = Topic.objects.create(subject=self.subject, name='Mexanika')

    def payload(self, **extra):
        data = {
            'topic': self.topic.id,
            'text': 'Tezlik formulasi qanday?',
            'options': {'A': 'v = s/t', 'B': 'v = t/s'},
            'correct_option': 'A',
        }
        data.update(extra)
        return data

    def test_question_without_image_is_accepted(self):
        response = self.client.post(
            '/catalog/questions/', self.payload(), format='json'
        )

        self.assertEqual(response.status_code, 201)
        self.assertIsNone(response.data['image'])
        self.assertFalse(response.data['has_image'])

    def test_question_with_image_is_accepted(self):
        image = SimpleUploadedFile('grafik.png', png_bytes(), content_type='image/png')
        response = self.client.post('/catalog/questions/', {
            'topic': self.topic.id,
            'text': 'Grafikda nima tasvirlangan?',
            'options': '{"A": "Chiziq", "B": "Parabola"}',
            'correct_option': 'A',
            'image': image,
            'image_caption': 'Harakat grafigi',
        }, format='multipart')

        self.assertEqual(response.status_code, 201)
        self.assertTrue(response.data['has_image'])
        self.assertIn('.png', response.data['image_url'])
        self.assertEqual(response.data['image_caption'], 'Harakat grafigi')

    def test_students_see_the_image_but_not_the_answer(self):
        image = SimpleUploadedFile('grafik.png', png_bytes(), content_type='image/png')
        created = self.client.post('/catalog/questions/', {
            'topic': self.topic.id,
            'text': 'Grafikda nima tasvirlangan?',
            'options': '{"A": "Chiziq", "B": "Parabola"}',
            'correct_option': 'A',
            'image': image,
        }, format='multipart')

        self.client.force_authenticate(self.student)
        response = self.client.get(f'/catalog/questions/{created.data["id"]}/')

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.data['image'].endswith('.png'))
        self.assertNotIn('correct_option', response.data)

    def test_translated_options_must_use_the_same_keys(self):
        """Ruscha variantlarda 'C' bo'lib qolsa, javob kaliti mos kelmay qoladi."""
        response = self.client.post('/catalog/questions/', self.payload(
            options_ru={'A': 'v = s/t', 'C': 'v = t/s'},
        ), format='json')

        self.assertEqual(response.status_code, 400)
        self.assertIn('options_ru', response.data)

    def test_translated_options_with_matching_keys_are_accepted(self):
        response = self.client.post('/catalog/questions/', self.payload(
            text_ru='Какова формула скорости?',
            options_ru={'A': 'v = s/t', 'B': 'v = t/s'},
        ), format='json')

        self.assertEqual(response.status_code, 201)

    def test_correct_option_must_exist_in_options(self):
        response = self.client.post(
            '/catalog/questions/', self.payload(correct_option='D'), format='json'
        )
        self.assertEqual(response.status_code, 400)

    def test_student_cannot_create_questions(self):
        self.client.force_authenticate(self.student)
        response = self.client.post(
            '/catalog/questions/', self.payload(), format='json'
        )
        self.assertEqual(response.status_code, 403)

    def test_has_image_filter(self):
        self.client.post('/catalog/questions/', self.payload(), format='json')
        image = SimpleUploadedFile('x.png', png_bytes(), content_type='image/png')
        self.client.post('/catalog/questions/', {
            'topic': self.topic.id,
            'text': 'Rasmli savol matni',
            'options': '{"A": "1", "B": "2"}',
            'correct_option': 'A',
            'image': image,
        }, format='multipart')

        with_image = self.client.get('/catalog/questions/?has_image=true')
        without_image = self.client.get('/catalog/questions/?has_image=false')

        self.assertEqual(with_image.data['count'], 1)
        self.assertEqual(without_image.data['count'], 1)


class QuestionDeletionGuardTests(APITestCase):
    """Davom etayotgan sessiyadagi savol jimgina yo'qolib qolmasligi kerak."""

    def setUp(self):
        cache.clear()
        self.mentor = make_user('deleter@example.com', role=Role.MENTOR)
        self.student = make_user('taker@example.com')

        from common.testutils import make_questions
        self.questions = make_questions(3, subject_name='Biologiya', topic_name='Hujayra')
        self.subject = self.questions[0].topic.subject

    def start_session(self):
        self.client.force_authenticate(self.student)
        response = self.client.post('/testengine/sessions/', {
            'subject': self.subject.id, 'question_count': 3,
        }, format='json')
        self.client.force_authenticate(self.mentor)
        return response.data['id']

    def test_question_in_active_session_cannot_be_deleted(self):
        self.start_session()
        response = self.client.delete(f'/catalog/questions/{self.questions[0].id}/')
        self.assertEqual(response.status_code, 409)

    def test_unused_question_can_be_deleted(self):
        self.client.force_authenticate(self.mentor)
        response = self.client.delete(f'/catalog/questions/{self.questions[0].id}/')
        self.assertEqual(response.status_code, 204)

    def test_question_can_be_deleted_after_session_is_finished(self):
        session_id = self.start_session()

        self.client.force_authenticate(self.student)
        self.client.post(f'/testengine/sessions/{session_id}/finish/')
        self.client.force_authenticate(self.mentor)

        response = self.client.delete(f'/catalog/questions/{self.questions[0].id}/')
        self.assertEqual(response.status_code, 204)


class MultilingualSearchTests(APITestCase):
    def setUp(self):
        cache.clear()
        self.user = make_user('search@example.com')
        self.client.force_authenticate(self.user)
        Subject.objects.create(name='Matematika', name_ru='Математика')

    def test_search_matches_russian_name(self):
        response = self.client.get('/catalog/subjects/?name=Матем')
        self.assertEqual(response.data['count'], 1)

    def test_search_matches_uzbek_name(self):
        response = self.client.get('/catalog/subjects/?name=Matem')
        self.assertEqual(response.data['count'], 1)
