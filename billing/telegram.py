"""Obuna arizasini admin bilan Telegram orqali bog'lash.

Ikki qism bor va ular bir-biridan mustaqil:

1. **Foydalanuvchi uchun havola** — "Admin bilan bog'lanish" tugmasi.
   Havola ariza ma'lumotlari bilan oldindan to'ldiriladi, foydalanuvchi
   faqat "Yuborish" ni bosadi. Bu hech qanday sozlamasiz ishlaydi.

2. **Adminga xabar** — bot orqali avtomatik yuboriladi. Buning uchun
   `TELEGRAM_BOT_TOKEN` va `TELEGRAM_ADMIN_CHAT_ID` sozlangan bo'lishi
   kerak. Sozlanmagan bo'lsa xatolik bermaydi, shunchaki log yoziladi va
   1-qism baribir ishlaydi.
"""

from __future__ import annotations

import logging
from urllib.parse import quote

import requests
from django.conf import settings

logger = logging.getLogger('billing.telegram')

TELEGRAM_API = 'https://api.telegram.org/bot{token}/sendMessage'
REQUEST_TIMEOUT = 10


def admin_link() -> str:
    return getattr(settings, 'ADMIN_TELEGRAM_LINK', '') or ''


def admin_username() -> str:
    """`https://t.me/akobir_ETA` -> `akobir_ETA`."""
    link = admin_link()
    if not link:
        return ''
    return link.rstrip('/').split('/')[-1].lstrip('@')


def format_price(amount) -> str:
    """`50000.00` -> `50 000 so'm`."""
    try:
        value = int(float(amount))
    except (TypeError, ValueError):
        return str(amount)
    return f"{value:,}".replace(',', ' ') + " so'm"


def application_text(payment) -> str:
    """Adminga boradigan ariza matni."""
    user = payment.user
    plan = payment.plan

    lines = [
        '🆕 Yangi obuna arizasi',
        '',
        f'👤 Foydalanuvchi: {user.full_name or "—"}',
        f'✉️ Email: {user.email}',
    ]
    if payment.contact_phone:
        lines.append(f'📞 Telefon: {payment.contact_phone}')
    if payment.contact_telegram:
        lines.append(f'💬 Telegram: @{payment.contact_telegram}')

    lines += [
        '',
        f'📦 Tarif: {plan.name if plan else "—"}',
        f'💰 Summa: {format_price(payment.amount)}',
        f'📅 Muddat: {plan.duration_days if plan else "—"} kun',
        '',
        f'🧾 Ariza raqami: #{payment.id} ({payment.provider_transaction_id})',
    ]
    if payment.note:
        lines += ['', f'📝 Izoh: {payment.note}']

    return '\n'.join(lines)


def user_prefilled_message(payment) -> str:
    """Foydalanuvchi adminga yuboradigan tayyor matn."""
    plan = payment.plan
    return (
        f'Assalomu alaykum! Men #{payment.id} raqamli obuna arizasini yubordim.\n'
        f'Tarif: {plan.name if plan else "—"} — {format_price(payment.amount)}.\n'
        f'Email: {payment.user.email}'
    )


def contact_payload(payment=None) -> dict:
    """Frontend uchun "Admin bilan bog'lanish" tugmasi ma'lumoti."""
    username = admin_username()
    url = admin_link()

    if payment is not None and username:
        # `?text=` — Telegram chatni oldindan to'ldirilgan xabar bilan ochadi.
        url = f'https://t.me/{username}?text={quote(user_prefilled_message(payment))}'

    return {
        'label': "Admin bilan bog'lanish",
        'url': url,
        'username': f'@{username}' if username else '',
        'prefilled_message': user_prefilled_message(payment) if payment else '',
    }


def send_to_admin(text: str) -> bool:
    """Adminga Telegram xabarini yuboradi. Sozlanmagan bo'lsa False."""
    token = getattr(settings, 'TELEGRAM_BOT_TOKEN', '')
    chat_id = getattr(settings, 'TELEGRAM_ADMIN_CHAT_ID', '')

    if not token or not chat_id:
        logger.info(
            'Telegram bot sozlanmagan (TELEGRAM_BOT_TOKEN/TELEGRAM_ADMIN_CHAT_ID) — '
            'ariza faqat bazaga yozildi.'
        )
        return False

    try:
        response = requests.post(
            TELEGRAM_API.format(token=token),
            json={
                'chat_id': chat_id,
                'text': text,
                'disable_web_page_preview': True,
            },
            timeout=REQUEST_TIMEOUT,
        )
        response.raise_for_status()
    except requests.RequestException as exc:
        # Ariza baribir bazada — admin panelda ko'rinadi. Shuning uchun bu
        # xatolik foydalanuvchining so'roviga ta'sir qilmaydi.
        logger.warning('Telegramga xabar yuborilmadi: %s', exc)
        return False

    return True
