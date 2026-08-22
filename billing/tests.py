from datetime import timedelta
from unittest.mock import patch

from django.core.cache import cache
from django.utils import timezone
from rest_framework.test import APITestCase

from billing.models import Payment, Subscription
from billing.services import activate_subscription, expire_due_subscriptions
from common.models import Role
from common.testutils import make_plan, make_user


class PaymentThrottleRegressionTests(APITestCase):
    """`subscription_request` throttle scope regressiyasi uchun.

    Scope `DEFAULT_THROTTLE_RATES` da e'lon qilinmagani sababli bu endpoint
    `ImproperlyConfigured` bilan har safar 500 qaytarardi.
    """

    def setUp(self):
        cache.clear()
        self.user = make_user('payer@example.com')
        self.client.force_authenticate(self.user)

    def test_payments_list_does_not_500(self):
        response = self.client.get('/billing/payments/')
        self.assertEqual(response.status_code, 200)

    def test_payments_list_requires_auth(self):
        self.client.force_authenticate(None)
        response = self.client.get('/billing/payments/')
        self.assertEqual(response.status_code, 401)


class SubscriptionStatusChoiceTests(APITestCase):
    """`pending` holati model `choices` ida mavjud bo'lishi kerak —
    to'lov tasdiqlanishini kutayotgan obunalar shu holatda yoziladi."""

    def test_pending_is_a_valid_choice(self):
        self.assertIn('pending', Subscription.Status.values)


class PlanCatalogTests(APITestCase):
    """Uchta tarif: 0 so'm, 50 000 so'm, 70 000 so'm."""

    def setUp(self):
        cache.clear()
        self.user = make_user('plans@example.com')
        self.client.force_authenticate(self.user)
        self.free = make_plan('Bepul', 0)
        self.standard = make_plan('Standart', 50000)
        self.premium = make_plan('Premium', 70000)

    def test_plans_are_listed_cheapest_first(self):
        response = self.client.get('/billing/plan/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            [plan['name'] for plan in response.data],
            ['Bepul', 'Standart', 'Premium'],
        )

    def test_free_plan_is_flagged(self):
        response = self.client.get('/billing/plan/')
        self.assertTrue(response.data[0]['is_free'])
        self.assertFalse(response.data[1]['is_free'])

    def test_price_display_is_human_readable(self):
        response = self.client.get('/billing/plan/')
        self.assertEqual(response.data[1]['price_display'], "50 000 so'm")


class SubscriptionRequestTests(APITestCase):
    """Ariza yuborish oqimi va admin tasdig'i."""

    def setUp(self):
        cache.clear()
        self.user = make_user('applicant@example.com', phone_number='+998901112233')
        self.admin = make_user('admin@example.com', role=Role.ADMIN)
        self.client.force_authenticate(self.user)

        self.free = make_plan('Bepul', 0)
        self.standard = make_plan('Standart', 50000)
        self.premium = make_plan('Premium', 70000)

    def request_plan(self, plan, **extra):
        with patch('billing.tasks.notify_admin_about_request_task.delay'):
            return self.client.post(
                '/billing/payments/', {'plan_id': plan.id, **extra}, format='json'
            )

    def approve(self, payment_id):
        self.client.force_authenticate(self.admin)
        response = self.client.patch(f'/billing/payments/{payment_id}/approve/')
        self.client.force_authenticate(self.user)
        return response

    # -- ariza yuborish ---------------------------------------------------
    def test_request_creates_pending_payment_and_returns_telegram_link(self):
        response = self.request_plan(self.standard)

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data['ariza']['status'], 'pending')
        self.assertFalse(response.data['auto_activated'])
        self.assertTrue(response.data['admin_telegram'])
        self.assertIn('t.me', response.data['contact']['url'])
        self.assertTrue(response.data['contact']['prefilled_message'])

    def test_request_carries_contact_details_for_admin(self):
        response = self.request_plan(
            self.standard, contact_telegram='@student', note='Kechqurun to\'layman'
        )
        payment = Payment.objects.get(pk=response.data['ariza']['id'])

        self.assertEqual(payment.contact_phone, '+998901112233')
        self.assertEqual(payment.contact_telegram, 'student')
        self.assertEqual(payment.note, "Kechqurun to'layman")

    def test_admin_is_notified_about_new_request(self):
        # Xabar `transaction.on_commit` da navbatga qo'yiladi — testda commit
        # bo'lmaydi, shuning uchun callback'lar qo'lda ishga tushiriladi.
        with patch('billing.tasks.notify_admin_about_request_task.delay') as notify:
            with self.captureOnCommitCallbacks(execute=True):
                self.client.post(
                    '/billing/payments/', {'plan_id': self.standard.id}, format='json'
                )
        notify.assert_called_once()

    def test_free_plan_activates_immediately_without_admin(self):
        response = self.request_plan(self.free)

        self.assertEqual(response.status_code, 201)
        self.assertTrue(response.data['auto_activated'])
        self.assertEqual(response.data['subscription']['status'], 'active')

    def test_unknown_plan_returns_404(self):
        response = self.client.post('/billing/payments/', {'plan_id': 999999}, format='json')
        self.assertEqual(response.status_code, 404)

    def test_plan_id_is_required(self):
        response = self.client.post('/billing/payments/', {}, format='json')
        self.assertEqual(response.status_code, 400)

    # -- takroriy ariza ---------------------------------------------------
    def test_second_request_while_pending_is_rejected(self):
        self.request_plan(self.standard)
        response = self.request_plan(self.premium)

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data['code'], 'pending_request')

    def test_user_can_cancel_own_pending_request(self):
        created = self.request_plan(self.standard)
        payment_id = created.data['ariza']['id']

        response = self.client.patch(f'/billing/payments/{payment_id}/cancel/')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['status'], 'cancelled')
        # Bekor qilgandan keyin yangi ariza yuborish mumkin.
        self.assertEqual(self.request_plan(self.premium).status_code, 201)

    # -- admin tasdig'i ---------------------------------------------------
    def test_approval_activates_subscription_for_plan_duration(self):
        created = self.request_plan(self.standard)
        response = self.approve(created.data['ariza']['id'])

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['status'], 'active')

        subscription = Subscription.objects.get(pk=response.data['id'])
        expected = timezone.now() + timedelta(days=self.standard.duration_days)
        self.assertAlmostEqual(
            subscription.expires_at.timestamp(), expected.timestamp(), delta=60
        )

    def test_approval_is_not_repeatable(self):
        created = self.request_plan(self.standard)
        payment_id = created.data['ariza']['id']
        self.approve(payment_id)

        second = self.approve(payment_id)
        self.assertEqual(second.status_code, 400)
        self.assertEqual(second.data['code'], 'already_reviewed')

    def test_non_admin_cannot_approve(self):
        created = self.request_plan(self.standard)
        response = self.client.patch(
            f'/billing/payments/{created.data["ariza"]["id"]}/approve/'
        )
        self.assertEqual(response.status_code, 403)

    def test_rejection_stores_reason_and_frees_the_user(self):
        created = self.request_plan(self.standard)
        payment_id = created.data['ariza']['id']

        self.client.force_authenticate(self.admin)
        response = self.client.patch(
            f'/billing/payments/{payment_id}/reject/',
            {'reason': "To'lov kelmadi"}, format='json',
        )
        self.client.force_authenticate(self.user)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['rejection_reason'], "To'lov kelmadi")
        self.assertEqual(self.request_plan(self.standard).status_code, 201)


class PlanTierRulesTests(APITestCase):
    """Talab: 50 minglikni olgan bo'lsa, oy tugagunicha 50 minglikni qayta
    ololmaydi, lekin 70 minglikni olishi mumkin."""

    def setUp(self):
        cache.clear()
        self.user = make_user('tier@example.com')
        self.admin = make_user('tieradmin@example.com', role=Role.ADMIN)
        self.client.force_authenticate(self.user)

        self.free = make_plan('Bepul', 0)
        self.standard = make_plan('Standart', 50000)
        self.premium = make_plan('Premium', 70000)

        self.activate(self.standard)

    def activate(self, plan):
        """Foydalanuvchiga shu tarifni faol qilib beradi."""
        now = timezone.now()
        subscription = Subscription.objects.create(
            user=self.user, plan=plan,
            status=Subscription.Status.PENDING, starts_at=now, expires_at=now,
        )
        return activate_subscription(subscription, now=now)

    def request_plan(self, plan):
        with patch('billing.tasks.notify_admin_about_request_task.delay'):
            return self.client.post(
                '/billing/payments/', {'plan_id': plan.id}, format='json'
            )

    def test_same_plan_is_blocked_until_expiry(self):
        response = self.request_plan(self.standard)

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data['code'], 'already_active')
        self.assertIn('available_at', response.data)

    def test_cheaper_plan_is_blocked(self):
        response = self.request_plan(self.free)

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data['code'], 'downgrade_blocked')

    def test_more_expensive_plan_is_allowed(self):
        response = self.request_plan(self.premium)
        self.assertEqual(response.status_code, 201)

    def test_same_plan_allowed_again_after_expiry(self):
        Subscription.objects.filter(user=self.user).update(
            expires_at=timezone.now() - timedelta(days=1)
        )
        response = self.request_plan(self.standard)
        self.assertEqual(response.status_code, 201)

    def test_upgrade_carries_over_remaining_days(self):
        """50 minglikda 20 kun qolgan bo'lsa, 70 minglik 30+20 kun bo'ladi."""
        current = Subscription.objects.get(user=self.user)
        current.expires_at = timezone.now() + timedelta(days=20)
        current.save(update_fields=['expires_at'])

        created = self.request_plan(self.premium)
        self.client.force_authenticate(self.admin)
        self.client.patch(f'/billing/payments/{created.data["ariza"]["id"]}/approve/')
        self.client.force_authenticate(self.user)

        upgraded = Subscription.objects.get(plan=self.premium, user=self.user)
        expected = timezone.now() + timedelta(days=self.premium.duration_days + 20)
        self.assertAlmostEqual(
            upgraded.expires_at.timestamp(), expected.timestamp(), delta=120
        )

        current.refresh_from_db()
        self.assertEqual(current.status, Subscription.Status.CANCELLED)

    def test_eligibility_endpoint_explains_every_plan(self):
        response = self.client.get('/billing/subscriptions/eligibility/')

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.data['has_active_subscription'])

        by_name = {row['plan']['name']: row for row in response.data['plans']}
        self.assertFalse(by_name['Standart']['can_request'])
        self.assertFalse(by_name['Bepul']['can_request'])
        self.assertTrue(by_name['Premium']['can_request'])
        self.assertTrue(by_name['Premium']['is_upgrade'])
        self.assertIsNotNone(by_name['Standart']['available_at'])


class CurrentSubscriptionShapeTests(APITestCase):
    """`current` endpointi obuna bor-yo'qligidan qat'i nazar bir xil
    shaklda javob berishi kerak."""

    def setUp(self):
        cache.clear()
        self.user = make_user('shape@example.com')
        self.client.force_authenticate(self.user)
        self.plan = make_plan('Standart', 50000)

    def test_shape_is_stable_without_subscription(self):
        response = self.client.get('/billing/subscriptions/current/')

        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.data['has_active_subscription'])
        self.assertIsNone(response.data['subscription'])
        self.assertIsNone(response.data['pending_request'])

    def test_shape_is_stable_with_subscription(self):
        now = timezone.now()
        Subscription.objects.create(
            user=self.user, plan=self.plan, status=Subscription.Status.ACTIVE,
            starts_at=now, expires_at=now + timedelta(days=30),
        )

        response = self.client.get('/billing/subscriptions/current/')

        self.assertTrue(response.data['has_active_subscription'])
        self.assertEqual(response.data['subscription']['plan']['name'], 'Standart')
        self.assertGreater(response.data['subscription']['days_left'], 28)


class SubscriptionExpiryTests(APITestCase):
    def setUp(self):
        cache.clear()
        self.user = make_user('expiry@example.com')
        self.plan = make_plan('Standart', 50000)

    def test_expired_subscriptions_are_closed(self):
        now = timezone.now()
        Subscription.objects.create(
            user=self.user, plan=self.plan, status=Subscription.Status.ACTIVE,
            starts_at=now - timedelta(days=40), expires_at=now - timedelta(days=1),
        )

        self.assertEqual(expire_due_subscriptions(), 1)
        self.assertEqual(
            Subscription.objects.get(user=self.user).status,
            Subscription.Status.EXPIRED,
        )

    def test_active_subscriptions_are_left_alone(self):
        now = timezone.now()
        Subscription.objects.create(
            user=self.user, plan=self.plan, status=Subscription.Status.ACTIVE,
            starts_at=now, expires_at=now + timedelta(days=10),
        )

        self.assertEqual(expire_due_subscriptions(), 0)
