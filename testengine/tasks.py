"""Test dvijoki fon vazifalari."""

import logging

from celery import shared_task

from testengine.services import finish_expired_sessions

logger = logging.getLogger('testengine.tasks')


@shared_task(ignore_result=True)
def finish_expired_sessions_task():
    """Imtihon muddati o'tgan, lekin yakunlanmagan sessiyalarni yopadi.

    Sessiya foydalanuvchi qaytib kelganda ham avtomatik yopiladi
    (`ensure_not_expired`), lekin u umuman qaytib kelmasligi mumkin —
    shunda sessiya abadiy "ochiq" bo'lib qolardi va statistikani buzardi.
    """
    return finish_expired_sessions()
