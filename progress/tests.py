from django.core.cache import cache
from django.test import TestCase

from common.testutils import make_user, make_question
from progress.models import XPTransaction
from testengine.models import TestSession, TestResult


class XPAwardTests(TestCase):
    """XP "farming" regressiyasi uchun.

    Ilgari TestResult yaratilishi bilan javob soniga qaramay 10 XP berilardi,
    ya'ni sessiya ochib darhol yakunlash orqali XP to'plash mumkin edi.
    """

    def setUp(self):
        cache.clear()
        self.user = make_user('xp@example.com')
        self.question = make_question()
        self.session = TestSession.objects.create(
            user=self.user, subject=self.question.topic.subject
        )

    def _xp_total(self):
        return sum(XPTransaction.objects.filter(user=self.user).values_list('amount', flat=True))

    def test_empty_test_awards_no_xp(self):
        TestResult.objects.create(session=self.session, correct_count=0, incorrect_count=0)
        self.assertEqual(self._xp_total(), 0)

    def test_answered_test_awards_xp(self):
        TestResult.objects.create(session=self.session, correct_count=3, incorrect_count=1)
        self.assertGreater(self._xp_total(), 0)

    def test_xp_scales_with_correct_answers(self):
        TestResult.objects.create(session=self.session, correct_count=1, incorrect_count=0)
        few = self._xp_total()

        other_session = TestSession.objects.create(
            user=self.user, subject=self.question.topic.subject
        )
        TestResult.objects.create(session=other_session, correct_count=10, incorrect_count=0)
        self.assertGreater(self._xp_total() - few, few)
