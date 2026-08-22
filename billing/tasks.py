"""Billing fon vazifalari.

Telegramga xabar yuborish tarmoq so'rovi — uni HTTP so'rov ichida bajarish
foydalanuvchini kutdiradi va Telegram ishlamay qolsa arizani ham buzadi.
Shuning uchun Celery'ga chiqarilgan.
"""

import logging

from celery import shared_task

from billing.models import Payment
from billing.services import expire_due_subscriptions
from billing.telegram import application_text, send_to_admin

logger = logging.getLogger('billing.tasks')


@shared_task(ignore_result=True)
def notify_admin_about_request_task(payment_id):
    """Yangi obuna arizasi haqida adminga Telegram xabar yuboradi."""
    payment = (
        Payment.objects
        .select_related('user', 'plan')
        .filter(pk=payment_id)
        .first()
    )
    if payment is None:
        logger.warning('Ariza topilmadi: id=%s', payment_id)
        return

    if send_to_admin(application_text(payment)):
        logger.info('Ariza adminga yuborildi: payment_id=%s', payment_id)


@shared_task(ignore_result=True)
def expire_subscriptions_task():
    """Muddati tugagan obunalarni yopadi (Celery beat kunlik chaqiradi)."""
    return expire_due_subscriptions()
