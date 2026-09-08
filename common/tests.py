from django.test import TestCase, override_settings


class GoogleTestPageTests(TestCase):
    @override_settings(GOOGLE_CLIENT_ID='test-client.apps.googleusercontent.com')
    def test_page_opens_without_login(self):
        response = self.client.get('/google-test/')
        self.assertEqual(response.status_code, 200)

    @override_settings(GOOGLE_CLIENT_ID='test-client.apps.googleusercontent.com')
    def test_client_id_comes_from_settings_not_hardcoded(self):
        response = self.client.get('/google-test/')
        self.assertContains(response, 'test-client.apps.googleusercontent.com')

    @override_settings(GOOGLE_CLIENT_ID='test-client.apps.googleusercontent.com')
    def test_page_posts_to_the_real_auth_endpoint(self):
        response = self.client.get('/google-test/')
        self.assertContains(response, '/api/auth/google/')
