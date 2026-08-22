"""Apple ID ("Sign in with Apple") tokenini tekshirish.

iPhone/iPad ilovasi Apple'dan `identity_token` (JWT) oladi va uni backendga
yuboradi. Biz tokenni Apple'ning ochiq kalitlari (JWKS) bilan tekshiramiz —
Apple'ga foydalanuvchi maxfiy ma'lumotini qayta yubormasdan.

Qo'shimcha kutubxona kerak emas: `PyJWT` va `cryptography` allaqachon
loyihada bor.
"""

from __future__ import annotations

import logging

import jwt
import requests
from django.conf import settings
from django.core.cache import cache
from jwt import PyJWKClient

logger = logging.getLogger('account.apple')

APPLE_ISSUER = 'https://appleid.apple.com'
APPLE_KEYS_URL = 'https://appleid.apple.com/auth/keys'

# JWKS kalitlari kamdan-kam almashadi; har login uchun Apple'ga chiqmaymiz.
JWKS_CACHE_KEY = 'apple:jwks'
JWKS_CACHE_TIMEOUT = 60 * 60 * 24
REQUEST_TIMEOUT = 10


class AppleAuthError(Exception):
    """Apple tokenini tekshirib bo'lmadi."""


def _allowed_audiences() -> list[str]:
    """Qabul qilinadigan `aud` qiymatlari — iOS bundle id va web client id."""
    audiences = []
    for name in ('APPLE_CLIENT_IDS', 'APPLE_CLIENT_ID', 'APPLE_BUNDLE_ID'):
        value = getattr(settings, name, None)
        if not value:
            continue
        if isinstance(value, (list, tuple, set)):
            audiences.extend(str(item).strip() for item in value if str(item).strip())
        else:
            audiences.append(str(value).strip())
    # Takrorlarni olib tashlaymiz, tartibni saqlab.
    return list(dict.fromkeys(audiences))


def _signing_key(token: str):
    """Token sarlavhasidagi `kid` ga mos Apple ochiq kalitini topadi."""
    jwks = cache.get(JWKS_CACHE_KEY)
    if jwks is None:
        try:
            response = requests.get(APPLE_KEYS_URL, timeout=REQUEST_TIMEOUT)
            response.raise_for_status()
            jwks = response.json()
        except (requests.RequestException, ValueError) as exc:
            raise AppleAuthError('Apple kalitlarini olishda xatolik') from exc
        cache.set(JWKS_CACHE_KEY, jwks, JWKS_CACHE_TIMEOUT)

    try:
        client = PyJWKClient(APPLE_KEYS_URL)
        return client.get_signing_key_from_jwt(token).key
    except Exception as exc:  # PyJWKClientError va h.k.
        # Kalit rotatsiya qilingan bo'lishi mumkin — keshni tozalab, bir marta
        # qayta urinib ko'rishga imkon beramiz.
        cache.delete(JWKS_CACHE_KEY)
        raise AppleAuthError('Apple imzo kaliti topilmadi') from exc


def verify_apple_token(token: str, expected_nonce: str | None = None) -> dict:
    """Apple `identity_token` ini tekshirib, foydalanuvchi ma'lumotini qaytaradi.

    Qaytadi: `{apple_id, email, email_verified, is_private_email}`.

    `email` bo'lmasligi mumkin (foydalanuvchi ulashmagan yoki takroriy
    login) — bunday holda `apple_id` bo'yicha topamiz.
    """
    audiences = _allowed_audiences()
    if not audiences:
        raise AppleAuthError(
            'APPLE_CLIENT_IDS sozlanmagan — Apple ID orqali kirish yoqilmagan.'
        )

    key = _signing_key(token)

    try:
        payload = jwt.decode(
            token,
            key=key,
            algorithms=['RS256'],
            audience=audiences,
            issuer=APPLE_ISSUER,
            options={'require': ['exp', 'iat', 'sub']},
        )
    except jwt.PyJWTError as exc:
        logger.warning('Apple tokeni rad etildi: %s', exc)
        raise AppleAuthError("Apple tokeni noto'g'ri yoki eskirgan") from exc

    # Replay hujumidan himoya: mijoz nonce yuborgan bo'lsa mos kelishi shart.
    if expected_nonce and payload.get('nonce') != expected_nonce:
        raise AppleAuthError("Apple tokenidagi nonce mos kelmadi")

    email = (payload.get('email') or '').strip().lower()

    return {
        'apple_id': payload['sub'],
        'email': email,
        'email_verified': str(payload.get('email_verified', 'false')).lower() == 'true',
        'is_private_email': str(payload.get('is_private_email', 'false')).lower() == 'true',
    }
