"""Obuna biznes-qoidalari.

Asosiy qoida (foydalanuvchi talabi):

* Foydalanuvchi tarif tanlab ARIZA yuboradi; admin Telegramda tasdiqlaydi.
* Tasdiqlangach obuna `duration_days` muddatga faollashadi.
* Aktiv obuna davomida AYNI YOKI ARZONROQ tarifni qayta olib bo'lmaydi —
  muddat tugagunicha kutish kerak.
* Lekin QIMMATROQ tarifga (upgrade) istalgan paytda o'tish mumkin.
  Upgrade'da eski obunaning qolgan kunlari yangisiga qo'shib beriladi —
  aks holda foydalanuvchi to'lagan kunlari kuyib ketadi.
"""

from __future__ import annotations

import logging
from datetime import timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.db import transaction
from django.utils import timezone

from billing.models import Payment, Plan, Subscription

logger = logging.getLogger('billing')


class SubscriptionError(Exception):
    """Ariza qabul qilinmadi. `code` mijozda ajratib ishlatish uchun."""

    def __init__(self, message, code='not_allowed', available_at=None):
        super().__init__(message)
        self.message = message
        self.code = code
        self.available_at = available_at


def active_subscription(user, now=None):
    """Foydalanuvchining hozir amal qilayotgan obunasi (yoki None)."""
    now = now or timezone.now()
    return (
        Subscription.objects
        .filter(user=user, status=Subscription.Status.ACTIVE, expires_at__gt=now)
        .select_related('plan')
        .order_by('-plan__price', '-expires_at')
        .first()
    )


def pending_payment(user):
    """Admin javobini kutayotgan ariza (yoki None)."""
    return (
        Payment.objects
        .filter(user=user, status=Payment.Status.PENDING)
        .select_related('plan')
        .order_by('-created_at')
        .first()
    )


def plan_eligibility(user, plan, now=None, current=None, pending=None):
    """Shu foydalanuvchi shu tarifga ariza bera oladimi?

    Qaytadi: `{can_request, reason_code, reason, available_at, is_upgrade}`.
    """
    now = now or timezone.now()
    current = current if current is not None else active_subscription(user, now)
    pending = pending if pending is not None else pending_payment(user)

    if not plan.is_active:
        return {
            'can_request': False,
            'reason_code': 'plan_inactive',
            'reason': "Bu tarif hozircha mavjud emas.",
            'available_at': None,
            'is_upgrade': False,
        }

    if pending is not None:
        return {
            'can_request': False,
            'reason_code': 'pending_request',
            'reason': "Sizning arizangiz allaqachon ko'rib chiqilmoqda. "
                      "Iltimos admin javobini kuting.",
            'available_at': None,
            'is_upgrade': False,
        }

    if current is None:
        return {
            'can_request': True,
            'reason_code': 'ok',
            'reason': '',
            'available_at': None,
            'is_upgrade': False,
        }

    current_price = Decimal(current.plan.price)
    new_price = Decimal(plan.price)

    if new_price > current_price:
        return {
            'can_request': True,
            'reason_code': 'upgrade',
            'reason': f"«{current.plan.name}» tarifidan «{plan.name}» tarifiga "
                      f"o'tmoqchisiz. Qolgan kunlaringiz yangi obunaga qo'shiladi.",
            'available_at': None,
            'is_upgrade': True,
        }

    if plan.id == current.plan_id:
        reason = (
            f"Sizda «{plan.name}» tarifi allaqachon faol. Uni qayta olish uchun "
            f"joriy muddat tugashini kuting."
        )
        code = 'already_active'
    else:
        reason = (
            f"Sizda qimmatroq «{current.plan.name}» tarifi faol. Arzonroq tarifga "
            f"o'tish uchun joriy muddat tugashini kuting."
        )
        code = 'downgrade_blocked'

    return {
        'can_request': False,
        'reason_code': code,
        'reason': reason,
        'available_at': current.expires_at,
        'is_upgrade': False,
    }


def eligibility_overview(user, now=None):
    """Barcha faol tariflar bo'yicha holat — frontend tarif ekrani uchun.

    Bitta so'rovda: qaysi tugma bosiladigan, qaysisi «X sanagacha
    kutiladi» deb ko'rsatiladi.
    """
    now = now or timezone.now()
    current = active_subscription(user, now)
    pending = pending_payment(user)

    plans = Plan.objects.filter(is_active=True).order_by('price', 'id')
    return current, pending, [
        (plan, plan_eligibility(user, plan, now, current, pending)) for plan in plans
    ]


@transaction.atomic
def create_subscription_request(user, plan, contact_phone='', contact_telegram='', note=''):
    """Ariza yaratadi.

    Bepul tarif bo'lsa admin kutilmaydi — obuna darhol faollashadi.
    Qaytadi: `(payment, subscription, auto_activated)`.
    """
    now = timezone.now()

    # Qoidalarni qulflangan holda tekshiramiz: ikkita parallel so'rov ikkita
    # ariza yaratib yubormasligi uchun. Foydalanuvchi qatorini qulflaymiz —
    # obuna qatorlarini qulflash yangi foydalanuvchida ish bermaydi
    # (qulflanadigan qator yo'q).
    get_user_model().objects.select_for_update().filter(pk=user.pk).first()

    verdict = plan_eligibility(user, plan, now)
    if not verdict['can_request']:
        raise SubscriptionError(
            verdict['reason'], verdict['reason_code'], verdict['available_at']
        )

    subscription = Subscription.objects.create(
        user=user,
        plan=plan,
        status=Subscription.Status.PENDING,
        starts_at=now,
        # Tasdiqlanmaguncha muddat yo'q; `starts_at` bilan teng qo'yamiz.
        expires_at=now,
    )

    payment = Payment.objects.create(
        user=user,
        plan=plan,
        subscription=subscription,
        provider=Payment.Provider.MANUAL,
        provider_transaction_id=Payment.new_transaction_id(user.id),
        amount=plan.price,
        status=Payment.Status.PENDING,
        contact_phone=(contact_phone or user.phone_number or '')[:20],
        contact_telegram=(contact_telegram or user.telegram_username or '').lstrip('@')[:64],
        note=note or '',
    )

    if plan.is_free:
        # 0 so'mlik tarif uchun admin tasdig'i ma'nosiz — darhol faollashtiramiz.
        activate_subscription(subscription, now=now)
        payment.status = Payment.Status.SUCCESS
        payment.reviewed_at = now
        payment.save(update_fields=['status', 'reviewed_at', 'updated_at'])
        subscription.refresh_from_db()

        logger.info(
            'Bepul tarif avtomatik faollashtirildi: user_id=%s plan_id=%s', user.id, plan.id
        )
        return payment, subscription, True

    logger.info(
        'Obuna arizasi yaratildi: payment_id=%s user_id=%s plan_id=%s summa=%s',
        payment.id, user.id, plan.id, plan.price,
    )
    return payment, subscription, False


def activate_subscription(subscription, now=None):
    """Obunani faollashtiradi va eski aktiv obunani yopadi.

    Upgrade bo'lsa eski obunaning QOLGAN VAQTI yangisiga qo'shiladi.
    """
    now = now or timezone.now()
    user = subscription.user

    previous = (
        Subscription.objects
        .filter(user=user, status=Subscription.Status.ACTIVE, expires_at__gt=now)
        .exclude(pk=subscription.pk)
        .select_related('plan')
        .order_by('-expires_at')
        .first()
    )

    bonus = timedelta()
    if previous is not None:
        bonus = max(previous.expires_at - now, timedelta())
        previous.status = Subscription.Status.CANCELLED
        previous.save(update_fields=['status', 'updated_at'])
        logger.info(
            'Upgrade: eski obuna yopildi id=%s, qolgan vaqt yangisiga qo\'shildi (%s kun)',
            previous.id, bonus.days,
        )

    subscription.status = Subscription.Status.ACTIVE
    subscription.starts_at = now
    subscription.expires_at = now + timedelta(days=subscription.plan.duration_days) + bonus
    subscription.save(update_fields=['status', 'starts_at', 'expires_at', 'updated_at'])
    return subscription


@transaction.atomic
def approve_payment(payment, admin_user):
    """Admin arizani tasdiqlaydi -> obuna faollashadi."""
    # `of=('self',)` shart: `subscription` nullable FK, ya'ni LEFT OUTER JOIN
    # bo'ladi va PostgreSQL "FOR UPDATE cannot be applied to the nullable side
    # of an outer join" deb rad etadi. `of` bilan faqat payment qatori
    # qulflanadi.
    payment = Payment.objects.select_for_update(of=('self',)).select_related(
        'user', 'plan', 'subscription__plan'
    ).get(pk=payment.pk)

    if payment.status != Payment.Status.PENDING:
        raise SubscriptionError(
            "Bu ariza allaqachon ko'rib chiqilgan.", 'already_reviewed'
        )

    subscription = payment.subscription
    if subscription is None:
        # Ariza obunasiz qolgan bo'lsa (eski ma'lumot) — qayta yaratamiz.
        plan = payment.plan
        if plan is None:
            raise SubscriptionError(
                "Arizada tarif ko'rsatilmagan, tasdiqlab bo'lmaydi.", 'plan_missing'
            )
        now = timezone.now()
        subscription = Subscription.objects.create(
            user=payment.user, plan=plan,
            status=Subscription.Status.PENDING, starts_at=now, expires_at=now,
        )
        payment.subscription = subscription

    now = timezone.now()
    activate_subscription(subscription, now=now)

    payment.status = Payment.Status.SUCCESS
    payment.reviewed_by = admin_user
    payment.reviewed_at = now
    payment.save(update_fields=[
        'status', 'subscription', 'reviewed_by', 'reviewed_at', 'updated_at'
    ])

    logger.info(
        'Ariza tasdiqlandi: payment_id=%s user_id=%s obuna=%s tugaydi=%s admin_id=%s',
        payment.id, payment.user_id, subscription.id, subscription.expires_at, admin_user.id,
    )
    return payment, subscription


@transaction.atomic
def reject_payment(payment, admin_user, reason=''):
    """Admin arizani rad etadi -> kutilayotgan obuna bekor qilinadi."""
    payment = Payment.objects.select_for_update(of=('self',)).select_related(
        'user', 'subscription'
    ).get(pk=payment.pk)

    if payment.status != Payment.Status.PENDING:
        raise SubscriptionError(
            "Bu ariza allaqachon ko'rib chiqilgan.", 'already_reviewed'
        )

    now = timezone.now()
    payment.status = Payment.Status.FAILED
    payment.rejection_reason = (reason or '')[:255]
    payment.reviewed_by = admin_user
    payment.reviewed_at = now
    payment.save(update_fields=[
        'status', 'rejection_reason', 'reviewed_by', 'reviewed_at', 'updated_at'
    ])

    subscription = payment.subscription
    if subscription and subscription.status == Subscription.Status.PENDING:
        subscription.status = Subscription.Status.CANCELLED
        subscription.save(update_fields=['status', 'updated_at'])

    logger.info(
        'Ariza rad etildi: payment_id=%s user_id=%s sabab=%r admin_id=%s',
        payment.id, payment.user_id, reason, admin_user.id,
    )
    return payment


@transaction.atomic
def cancel_own_request(payment):
    """Foydalanuvchi o'z arizasini qaytarib oladi (hali tasdiqlanmagan bo'lsa)."""
    payment = Payment.objects.select_for_update(of=('self',)).select_related(
        'subscription'
    ).get(pk=payment.pk)

    if payment.status != Payment.Status.PENDING:
        raise SubscriptionError(
            "Faqat ko'rib chiqilmagan arizani bekor qilish mumkin.", 'already_reviewed'
        )

    payment.status = Payment.Status.CANCELLED
    payment.reviewed_at = timezone.now()
    payment.save(update_fields=['status', 'reviewed_at', 'updated_at'])

    subscription = payment.subscription
    if subscription and subscription.status == Subscription.Status.PENDING:
        subscription.status = Subscription.Status.CANCELLED
        subscription.save(update_fields=['status', 'updated_at'])

    return payment


def expire_due_subscriptions(now=None) -> int:
    """Muddati o'tgan obunalarni `expired` ga o'tkazadi.

    So'rovlar baribir `expires_at__gt=now` bilan filtrlansa ham, holat
    to'g'ri ko'rinishi uchun (admin panel, ro'yxatlar) buni davriy tozalab
    turish kerak.
    """
    now = now or timezone.now()
    updated = Subscription.objects.filter(
        status=Subscription.Status.ACTIVE, expires_at__lte=now
    ).update(status=Subscription.Status.EXPIRED, updated_at=now)

    if updated:
        logger.info('Muddati tugagan obunalar yopildi: %s ta', updated)
    return updated
