from unittest.mock import patch

from django.core.cache import cache
from django.test import TestCase
from rest_framework.test import APITestCase

from account.apple_auth import AppleAuthError
from account.models import Device, User
from common.i18n import parse_accept_language, resolve_language
from common.testutils import make_user


class LanguageResolutionTests(TestCase):
    """`common.i18n` — til aniqlash mantiqining o'zi."""

    def test_accept_language_picks_highest_quality(self):
        self.assertEqual(parse_accept_language('en;q=0.5,ru;q=0.9'), 'ru')

    def test_accept_language_respects_order_on_equal_quality(self):
        self.assertEqual(parse_accept_language('ru,en'), 'ru')

    def test_accept_language_ignores_unsupported(self):
        self.assertEqual(parse_accept_language('fr,de'), None)

    def test_accept_language_normalises_region(self):
        self.assertEqual(parse_accept_language('ru-RU'), 'ru')

    def test_malformed_quality_does_not_crash(self):
        self.assertEqual(parse_accept_language('ru;q=abc,en'), 'en')

    def test_resolve_language_without_request_returns_default(self):
        self.assertEqual(resolve_language(None), 'uz')


class GoogleAuthTests(APITestCase):
    """Android va web mijozlar uchun kirish."""

    def setUp(self):
        cache.clear()
        self.payload = {
            'email': 'new@example.com',
            'google_id': 'google-123',
            'full_name': 'Yangi Foydalanuvchi',
            'avatar_url': 'https://example.com/a.png',
        }

    def test_new_user_is_created_and_gets_tokens(self):
        with patch('account.routes.auth.views.verify_google_token', return_value=self.payload):
            response = self.client.post(
                '/api/auth/google/', {'id_token': 'x'}, format='json'
            )

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.data['is_new_user'])
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)
        self.assertTrue(response.data['user']['has_google'])

    def test_invalid_token_returns_400(self):
        with patch('account.routes.auth.views.verify_google_token', side_effect=ValueError):
            response = self.client.post(
                '/api/auth/google/', {'id_token': 'bad'}, format='json'
            )
        self.assertEqual(response.status_code, 400)

    def test_returning_user_is_not_duplicated(self):
        with patch('account.routes.auth.views.verify_google_token', return_value=self.payload):
            self.client.post('/api/auth/google/', {'id_token': 'x'}, format='json')
            response = self.client.post('/api/auth/google/', {'id_token': 'x'}, format='json')

        self.assertFalse(response.data['is_new_user'])
        self.assertEqual(User.objects.filter(email='new@example.com').count(), 1)

    def test_device_can_be_registered_during_login(self):
        with patch('account.routes.auth.views.verify_google_token', return_value=self.payload):
            self.client.post('/api/auth/google/', {
                'id_token': 'x',
                'device': {
                    'device_id': 'samsung-a51',
                    'platform': 'android',
                    'push_token': 'fcm-token',
                    'model_name': 'Galaxy A51',
                },
            }, format='json')

        device = Device.objects.get(device_id='samsung-a51')
        self.assertEqual(device.platform, 'android')
        self.assertEqual(device.model_name, 'Galaxy A51')


class AppleAuthTests(APITestCase):
    """iPhone/iPad — "Sign in with Apple"."""

    def setUp(self):
        cache.clear()
        self.apple = {
            'apple_id': 'apple-sub-123',
            'email': 'iphone@example.com',
            'email_verified': True,
            'is_private_email': False,
        }

    def login(self, **extra):
        with patch('account.routes.auth.views.verify_apple_token', return_value=self.apple):
            return self.client.post(
                '/api/auth/apple/', {'identity_token': 'x', **extra}, format='json'
            )

    def test_new_apple_user_is_created(self):
        response = self.login(full_name='Ali Valiyev')

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.data['is_new_user'])
        self.assertTrue(response.data['user']['has_apple'])
        self.assertEqual(response.data['user']['full_name'], 'Ali Valiyev')

    def test_second_login_reuses_the_same_account(self):
        self.login()
        response = self.login()

        self.assertFalse(response.data['is_new_user'])
        self.assertEqual(User.objects.filter(apple_id='apple-sub-123').count(), 1)

    def test_apple_login_without_email_finds_user_by_apple_id(self):
        """Apple emailni faqat birinchi kirishda beradi."""
        self.login()

        self.apple = {**self.apple, 'email': ''}
        response = self.login()

        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.data['is_new_user'])

    def test_first_apple_login_without_email_is_rejected_clearly(self):
        self.apple = {**self.apple, 'email': ''}
        response = self.login()

        self.assertEqual(response.status_code, 400)
        self.assertIn('email', response.data['detail'].lower())

    def test_apple_and_google_with_same_email_share_one_account(self):
        google_payload = {
            'email': 'iphone@example.com',
            'google_id': 'google-999',
            'full_name': 'Ali',
            'avatar_url': '',
        }
        with patch('account.routes.auth.views.verify_google_token', return_value=google_payload):
            self.client.post('/api/auth/google/', {'id_token': 'x'}, format='json')

        response = self.login()

        self.assertFalse(response.data['is_new_user'])
        self.assertEqual(User.objects.filter(email='iphone@example.com').count(), 1)
        self.assertTrue(response.data['user']['has_google'])
        self.assertTrue(response.data['user']['has_apple'])

    def test_invalid_apple_token_returns_400(self):
        with patch(
            'account.routes.auth.views.verify_apple_token',
            side_effect=AppleAuthError("Apple tokeni noto'g'ri yoki eskirgan"),
        ):
            response = self.client.post(
                '/api/auth/apple/', {'identity_token': 'bad'}, format='json'
            )

        self.assertEqual(response.status_code, 400)
        self.assertIn('Apple', response.data['detail'])


class ProfileTests(APITestCase):
    def setUp(self):
        cache.clear()
        self.user = make_user('profile@example.com')
        self.client.force_authenticate(self.user)

    def test_me_returns_profile(self):
        response = self.client.get('/api/auth/me/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['email'], 'profile@example.com')

    def test_language_can_be_changed(self):
        response = self.client.patch(
            '/api/auth/me/', {'language': 'ru'}, format='json'
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['language'], 'ru')

    def test_unsupported_language_is_rejected(self):
        response = self.client.patch(
            '/api/auth/me/', {'language': 'fr'}, format='json'
        )
        self.assertEqual(response.status_code, 400)

    def test_role_cannot_be_escalated_through_profile(self):
        self.client.patch('/api/auth/me/', {'role': 'admin'}, format='json')

        self.user.refresh_from_db()
        self.assertEqual(self.user.role, 'student')

    def test_xp_cannot_be_inflated_through_profile(self):
        self.client.patch('/api/auth/me/', {'xp_total': 999999}, format='json')

        self.user.refresh_from_db()
        self.assertEqual(self.user.xp_total, 0)

    def test_phone_and_telegram_are_normalised(self):
        response = self.client.patch('/api/auth/me/', {
            'phone_number': '+998901112233', 'telegram_username': '@student',
        }, format='json')

        self.assertEqual(response.data['telegram_username'], 'student')
        self.assertEqual(response.data['phone_number'], '+998901112233')

    def test_invalid_phone_is_rejected(self):
        response = self.client.patch(
            '/api/auth/me/', {'phone_number': 'telefon-raqamim'}, format='json'
        )
        self.assertEqual(response.status_code, 400)


class DeviceTests(APITestCase):
    """iPhone, Samsung va boshqa qurilmalar push uchun ro'yxatdan o'tadi."""

    def setUp(self):
        cache.clear()
        self.user = make_user('device@example.com')
        self.client.force_authenticate(self.user)

    def register(self, **extra):
        payload = {'device_id': 'iphone-15', 'platform': 'ios'}
        payload.update(extra)
        return self.client.post('/api/auth/devices/', payload, format='json')

    def test_device_registration_returns_201(self):
        response = self.register(model_name='iPhone 15 Pro', os_version='17.2')

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data['platform'], 'ios')
        self.assertEqual(response.data['model_name'], 'iPhone 15 Pro')

    def test_re_registering_updates_instead_of_duplicating(self):
        self.register(push_token='old')
        response = self.register(push_token='new')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(Device.objects.filter(user=self.user).count(), 1)
        self.assertEqual(Device.objects.get(user=self.user).push_token, 'new')

    def test_devices_are_scoped_to_their_owner(self):
        self.register()
        other = make_user('other-device@example.com')
        self.client.force_authenticate(other)

        response = self.client.get('/api/auth/devices/')
        self.assertEqual(len(response.data), 0)

    def test_android_platform_is_supported(self):
        response = self.register(device_id='samsung-s24', platform='android')
        self.assertEqual(response.data['platform'], 'android')

    def test_unknown_platform_is_rejected(self):
        response = self.register(platform='nokia-3310')
        self.assertEqual(response.status_code, 400)

    def test_device_can_be_removed(self):
        self.register()
        response = self.client.delete('/api/auth/devices/iphone-15/')

        self.assertEqual(response.status_code, 204)
        self.assertFalse(Device.objects.filter(user=self.user).exists())

    def test_removing_unknown_device_returns_404(self):
        response = self.client.delete('/api/auth/devices/does-not-exist/')
        self.assertEqual(response.status_code, 404)

    def test_requires_authentication(self):
        self.client.force_authenticate(None)
        response = self.client.get('/api/auth/devices/')
        self.assertEqual(response.status_code, 401)


class LogoutTests(APITestCase):
    def setUp(self):
        cache.clear()
        self.user = make_user('logout@example.com')
        self.client.force_authenticate(self.user)

    def test_logout_clears_push_token_of_named_device(self):
        from rest_framework_simplejwt.tokens import RefreshToken

        Device.objects.create(
            user=self.user, device_id='iphone-15', platform='ios', push_token='fcm'
        )
        refresh = RefreshToken.for_user(self.user)

        response = self.client.post('/api/auth/logout/', {
            'refresh': str(refresh), 'device_id': 'iphone-15',
        }, format='json')

        self.assertEqual(response.status_code, 200)
        device = Device.objects.get(device_id='iphone-15')
        self.assertEqual(device.push_token, '')
        self.assertFalse(device.is_active)

    def test_invalid_refresh_token_returns_400(self):
        response = self.client.post(
            '/api/auth/logout/', {'refresh': 'nonsense'}, format='json'
        )
        self.assertEqual(response.status_code, 400)
