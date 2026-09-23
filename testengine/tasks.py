"""Test dvijoki fon vazifalari."""

import logging

from celery import shared_task

from testengine.services import finish_expired_mock_exams, finish_expired_sessions

logger = logging.getLogger('testengine.tasks')


@shared_task(ignore_result=True)
def finish_expired_sessions_task():
    """Imtihon muddati o'tgan, lekin yakunlanmagan sessiyalarni yopadi.

    Sessiya foydalanuvchi qaytib kelganda ham avtomatik yopiladi
    (`ensure_not_expired`), lekin u umuman qaytib kelmasligi mumkin —
    shunda sessiya abadiy "ochiq" bo'lib qolardi va statistikani buzardi.
    """
    closed_sessions = finish_expired_sessions()
    # Blok imtihonining sessiyalari yopilgani bilan imtihonning o'zi ochiq
    # qolib ketmasligi kerak.
    closed_exams = finish_expired_mock_exams()
    return {'sessions': closed_sessions, 'mock_exams': closed_exams}
