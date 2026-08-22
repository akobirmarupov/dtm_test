from django.core.cache import cache
from rest_framework.test import APITestCase

from common.testutils import make_user
from rating.models import Rating
from rating.services import get_period_dates


class LeaderboardPrivacyTests(APITestCase):
    """Leaderboard begona foydalanuvchilarning emailini oshkor qilmasligi kerak.

    Ilgari `full_name or user.email` yozilgan edi — ismi kiritilmagan har bir
    foydalanuvchining emaili top-50 ro'yxatida hammaga ko'rinardi.
    """

    def setUp(self):
        cache.clear()
        self.viewer = make_user('viewer@example.com', full_name='Ko\'ruvchi')
        self.nameless = make_user('maxfiy@example.com')  # full_name bo'sh
        start, end = get_period_dates('daily')
        Rating.objects.create(
            user=self.nameless, period='daily', stars=10.0, rank=1,
            period_start_date=start, period_end_date=end,
        )
        self.client.force_authenticate(self.viewer)

    def test_email_is_not_exposed(self):
        response = self.client.get('/rating/leaderboard/daily/')
        self.assertEqual(response.status_code, 200)
        self.assertNotIn('maxfiy@example.com', str(response.data))

    def test_nameless_user_shown_as_anonim(self):
        response = self.client.get('/rating/leaderboard/daily/')
        self.assertEqual(response.data[0]['full_name'], 'Anonim')

    def test_invalid_period_returns_400(self):
        response = self.client.get('/rating/leaderboard/yillik/')
        self.assertEqual(response.status_code, 400)
