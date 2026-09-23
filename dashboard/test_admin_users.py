"""Admin foydalanuvchilarni ko'radi va bloklaydi."""

from datetime import timedelta
from decimal import Decimal

from django.core.cache import cache
from django.utils import timezone
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

from account.models import User
from billing.models import Subscription
from common.models import Role
from common.testutils import make_plan, make_user


class AdminUserApiTests(APITestCase):
    def setUp(self):
        cache.clear()
        self.admin = make_user('boss@example.com', role=Role.ADMIN)
        self.student = make_user('talaba@example.com', full_name='Ali Valiyev')
        self.other = make_user('boshqa@example.com', full_name='Vali Aliyev')
        self.client.force_authenticate(self.admin)

    def give_pro(self, user):
        plan = make_plan('Pullik', Decimal('59000'), is_pro=True)
        now = timezone.now()
        return Subscription.objects.create(
            user=user, plan=plan, status=Subscription.Status.ACTIVE,
            starts_at=now, expires_at=now + timedelta(days=30),
        )

    # -- ro'yxat ----------------------------------------------------------
    def test_list_shows_users_with_summary_numbers(self):
        self.give_pro(self.student)

        response = self.client.get('/dashboard/admin/users/')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['stats']['total'], 3)
        self.assertEqual(response.data['stats']['pro'], 1)
        self.assertEqual(response.data['stats']['blocked'], 0)

    def test_search_finds_by_name_and_email(self):
        by_name = self.client.get('/dashboard/admin/users/?search=Ali Valiyev')
        by_email = self.client.get('/dashboard/admin/users/?search=boshqa@')

        self.assertEqual([row['id'] for row in by_name.data['results']], [self.student.id])
        self.assertEqual([row['id'] for row in by_email.data['results']], [self.other.id])

    def test_blocked_users_can_be_filtered(self):
        self.client.post(f'/dashboard/admin/users/{self.student.id}/block/',
                         {'reason': 'Spam'}, format='json')

        response = self.client.get('/dashboard/admin/users/?is_active=false')

        self.assertEqual([row['id'] for row in response.data['results']], [self.student.id])
        self.assertTrue(response.data['results'][0]['is_blocked'])

    def test_pro_filter(self):
        self.give_pro(self.other)

        response = self.client.get('/dashboard/admin/users/?tier=pro')

        self.assertEqual([row['id'] for row in response.data['results']], [self.other.id])

    def test_only_admin_can_see_the_list(self):
        self.client.force_authenticate(self.student)
        self.assertEqual(self.client.get('/dashboard/admin/users/').status_code, 403)

    # -- tafsilot ---------------------------------------------------------
    def test_detail_shows_plan_and_activity(self):
        self.give_pro(self.student)

        response = self.client.get(f'/dashboard/admin/users/{self.student.id}/')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['email'], 'talaba@example.com')
        self.assertEqual(response.data['subscription']['plan'], 'Pullik')
        self.assertTrue(response.data['entitlements']['is_pro'])
        self.assertEqual(response.data['sessions_total'], 0)

    # -- bloklash ---------------------------------------------------------
    def test_block_records_who_and_why(self):
        response = self.client.post(
            f'/dashboard/admin/users/{self.student.id}/block/',
            {'reason': 'Qoidabuzarlik'}, format='json',
        )

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.data['is_blocked'])

        self.student.refresh_from_db()
        self.assertFalse(self.student.is_active)
        self.assertEqual(self.student.block_reason, 'Qoidabuzarlik')
        self.assertEqual(self.student.blocked_by_id, self.admin.id)
        self.assertIsNotNone(self.student.blocked_at)

    def test_blocked_user_cannot_use_the_api(self):
        token = RefreshToken.for_user(self.student).access_token
        self.client.post(f'/dashboard/admin/users/{self.student.id}/block/',
                         {'reason': 'Test'}, format='json')

        blocked_client = self.client_class()
        blocked_client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        response = blocked_client.get('/api/auth/me/')

        self.assertEqual(response.status_code, 401)

    def test_unblock_clears_everything(self):
        self.client.post(f'/dashboard/admin/users/{self.student.id}/block/',
                         {'reason': 'Xato edi'}, format='json')

        response = self.client.post(f'/dashboard/admin/users/{self.student.id}/unblock/')

        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.data['is_blocked'])

        self.student.refresh_from_db()
        self.assertTrue(self.student.is_active)
        self.assertEqual(self.student.block_reason, '')
        self.assertIsNone(self.student.blocked_at)
        self.assertIsNone(self.student.blocked_by_id)

    def test_admin_cannot_block_himself(self):
        response = self.client.post(f'/dashboard/admin/users/{self.admin.id}/block/')

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data['code'], 'self_block')

    def test_another_admin_cannot_be_blocked(self):
        second_admin = make_user('ikkinchi@example.com', role=Role.ADMIN)

        response = self.client.post(f'/dashboard/admin/users/{second_admin.id}/block/')

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data['code'], 'admin_block')

    def test_student_cannot_block_anyone(self):
        self.client.force_authenticate(self.student)

        response = self.client.post(f'/dashboard/admin/users/{self.other.id}/block/')

        self.assertEqual(response.status_code, 403)
        self.other.refresh_from_db()
        self.assertTrue(self.other.is_active)

    def test_unknown_user_returns_404(self):
        self.assertEqual(
            self.client.post('/dashboard/admin/users/999999/block/').status_code, 404
        )
