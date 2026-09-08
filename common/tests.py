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


class AdminCompletenessTests(TestCase):
    """Har bir model adminda ro'yxatdan o'tgan va sidebarda ko'rinadimi.

    Unfold sidebar ro'yxati `settings.UNFOLD` da QO'LDA yoziladi. Shuning
    uchun yangi model qo'shilganda admin klassi yozilgani bilan u chap
    menyuda paydo bo'lmaydi va admin uni topolmaydi.
    """

    APPS = {
        'account', 'catalog', 'testengine', 'progress',
        'rating', 'billing', 'notifications', 'dashboard',
    }

    def sidebar_links(self):
        from django.conf import settings

        return {
            item['link']
            for group in settings.UNFOLD['SIDEBAR']['navigation']
            for item in group.get('items', [])
        }

    def my_models(self):
        from django.contrib import admin

        return [
            model for model in admin.site._registry
            if model._meta.app_label in self.APPS
        ]

    def test_every_model_has_an_admin(self):
        from django.apps import apps
        from django.contrib import admin

        registered = set(admin.site._registry)
        missing = [
            f'{m._meta.app_label}.{m.__name__}'
            for m in apps.get_models()
            if m._meta.app_label in self.APPS and m not in registered
        ]
        self.assertEqual(missing, [], f'Admin klassi yozilmagan modellar: {missing}')

    def test_every_admin_is_in_the_sidebar(self):
        links = self.sidebar_links()
        missing = [
            f'{m._meta.app_label}.{m.__name__}'
            for m in self.my_models()
            if f'/admin/{m._meta.app_label}/{m._meta.model_name}/' not in links
        ]
        self.assertEqual(missing, [], f'Sidebarda ko\'rinmaydigan modellar: {missing}')

    def test_sidebar_has_no_dead_links(self):
        valid = {
            f'/admin/{m._meta.app_label}/{m._meta.model_name}/'
            for m in self.my_models()
        }
        dead = [
            link for link in self.sidebar_links()
            if link.startswith('/admin/') and link != '/admin/' and link not in valid
        ]
        self.assertEqual(dead, [], f'Mavjud bo\'lmagan sahifaga havola: {dead}')

    def test_admin_pages_open(self):
        """Ro'yxat va "qo'shish" sahifalari xatosiz ochilishi kerak."""
        from django.contrib.auth import get_user_model
        from django.urls import reverse

        boss = get_user_model().objects.create_superuser(
            email='admin-smoke@example.com', password='parol'
        )
        self.client.force_login(boss)

        broken = []
        for model in self.my_models():
            app, name = model._meta.app_label, model._meta.model_name
            for kind in ('changelist', 'add'):
                response = self.client.get(reverse(f'admin:{app}_{name}_{kind}'))
                # 403 — `has_add_permission` ataylab yopilgan sahifalar.
                if response.status_code not in (200, 302, 403):
                    broken.append((f'{app}.{model.__name__}', kind, response.status_code))

        self.assertEqual(broken, [], f'Ochilmaydigan admin sahifalari: {broken}')
