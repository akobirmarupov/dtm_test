from django.core.cache import cache
from django.test import TestCase, override_settings

from common.testutils import make_user
from notifications.models import Announcement, NotificationLog


@override_settings(CELERY_TASK_ALWAYS_EAGER=True, CELERY_TASK_EAGER_PROPAGATES=True)
class AnnouncementBroadcastTests(TestCase):
    """E'lon tarqatish Celery'ga ko'chirildi (ilgari admin so'rovi ichida
    sinxron bajarilib, foydalanuvchilar soni o'sgani sari timeout berardi).

    Vazifa `transaction.on_commit` orqali navbatga qo'yilgani uchun testda
    `captureOnCommitCallbacks` bilan ishga tushiriladi.
    """

    def setUp(self):
        cache.clear()
        self.active_one = make_user('a@example.com')
        self.active_two = make_user('b@example.com')
        self.inactive = make_user('c@example.com')
        self.inactive.is_active = False
        self.inactive.save(update_fields=['is_active'])

    def _create_announcement(self):
        with self.captureOnCommitCallbacks(execute=True):
            return Announcement.objects.create(title='Salom', message='Matn')

    def test_log_created_for_each_active_user(self):
        self._create_announcement()
        self.assertEqual(NotificationLog.objects.count(), 2)

    def test_inactive_user_gets_nothing(self):
        self._create_announcement()
        self.assertFalse(NotificationLog.objects.filter(user=self.inactive).exists())

    def test_announcement_marked_sent(self):
        announcement = self._create_announcement()
        announcement.refresh_from_db()
        self.assertTrue(announcement.is_sent)
        self.assertEqual(announcement.recipients_count, 2)

    def test_resave_does_not_duplicate(self):
        announcement = self._create_announcement()
        with self.captureOnCommitCallbacks(execute=True):
            announcement.save()
        self.assertEqual(NotificationLog.objects.count(), 2)
