from django.core.cache import cache
from rest_framework.test import APITestCase

from common.models import Role
from common.testutils import make_user
from dashboard.models import MentorStudent, MentorAlert


class MentorStudentReassignTests(APITestCase):
    """Mentor huquq oshirish (IDOR) regressiyasi uchun.

    `mentor`/`student` serializer'da yoziladigan bo'lgani sababli mentor
    o'z bog'lanishini PATCH qilib istalgan talabaga biriktirilib olardi.
    """

    def setUp(self):
        cache.clear()
        self.mentor = make_user('mentor@example.com', role=Role.MENTOR)
        self.my_student = make_user('mine@example.com')
        self.other_student = make_user('other@example.com')
        self.link = MentorStudent.objects.create(
            mentor=self.mentor, student=self.my_student
        )
        self.client.force_authenticate(self.mentor)

    def test_mentor_cannot_reassign_link_to_another_student(self):
        self.client.patch(
            f'/dashboard/mentor/students/{self.link.id}/',
            {'student': self.other_student.id}, format='json',
        )
        self.link.refresh_from_db()
        self.assertEqual(self.link.student_id, self.my_student.id)

    def test_mentor_cannot_steal_link_by_setting_mentor(self):
        rogue = make_user('rogue@example.com', role=Role.MENTOR)
        self.client.patch(
            f'/dashboard/mentor/students/{self.link.id}/',
            {'mentor': rogue.id}, format='json',
        )
        self.link.refresh_from_db()
        self.assertEqual(self.link.mentor_id, self.mentor.id)

    def test_mentor_can_still_edit_allowed_fields(self):
        response = self.client.patch(
            f'/dashboard/mentor/students/{self.link.id}/',
            {'notes': 'Yaxshi natija'}, format='json',
        )
        self.assertEqual(response.status_code, 200)
        self.link.refresh_from_db()
        self.assertEqual(self.link.notes, 'Yaxshi natija')


class MentorAlertTests(APITestCase):
    """Mentor faqat o'ziga biriktirilgan talaba uchun ogohlantirish ocha oladi."""

    def setUp(self):
        cache.clear()
        self.mentor = make_user('mentor2@example.com', role=Role.MENTOR)
        self.my_student = make_user('mine2@example.com')
        self.stranger = make_user('stranger@example.com')
        MentorStudent.objects.create(mentor=self.mentor, student=self.my_student)
        self.client.force_authenticate(self.mentor)

    def _payload(self, student):
        return {
            'student': student.id,
            'alert_type': MentorAlert.AlertType.LOW_PERFORMANCE,
            'message': 'Diqqat talab qiladi',
        }

    def test_alert_for_assigned_student_allowed(self):
        response = self.client.post(
            '/dashboard/mentor/alerts/', self._payload(self.my_student), format='json'
        )
        self.assertEqual(response.status_code, 201)

    def test_alert_for_unassigned_student_forbidden(self):
        response = self.client.post(
            '/dashboard/mentor/alerts/', self._payload(self.stranger), format='json'
        )
        self.assertEqual(response.status_code, 403)
        self.assertFalse(MentorAlert.objects.filter(student=self.stranger).exists())

    def test_status_cannot_be_set_on_create(self):
        payload = self._payload(self.my_student)
        payload['status'] = 'resolved'
        response = self.client.post('/dashboard/mentor/alerts/', payload, format='json')
        self.assertEqual(response.status_code, 201)
        # `status` read-only bo'lgani uchun mijoz qiymati e'tiborga olinmaydi.
        self.assertEqual(
            MentorAlert.objects.get(pk=response.data['id']).status,
            MentorAlert.Status.OPEN,
        )
