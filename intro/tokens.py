"""Kirish testi tokeni.

Savollar mijozga yuborilgandan keyin, javob kelganda «bu odam aynan shu 4 ta
savolni olgan edi» deb ishonch hosil qilish kerak. Bazaga sessiya yozmaymiz —
foydalanuvchi hali ro'yxatdan o'tmagan. Shuning uchun imzolangan token:
ichida savol id'lari turadi, imzo buzilsa qabul qilinmaydi.
"""

from __future__ import annotations

from django.core import signing

SALT = 'intro.test.session'
TOKEN_MAX_AGE_SECONDS = 60 * 60  # 1 soat


class IntroTokenError(Exception):
    def __init__(self, message, code='invalid_token'):
        super().__init__(message)
        self.message = message
        self.code = code


def issue_token(question_ids) -> str:
    return signing.dumps({'q': list(question_ids), 'v': 1}, salt=SALT, compress=True)


def read_token(token) -> dict:
    try:
        payload = signing.loads(token, salt=SALT, max_age=TOKEN_MAX_AGE_SECONDS)
    except signing.SignatureExpired:
        raise IntroTokenError(
            "Test muddati tugadi. Iltimos, qaytadan boshlang.", 'token_expired'
        )
    except signing.BadSignature:
        raise IntroTokenError("Test tokeni yaroqsiz.", 'invalid_token')

    if not isinstance(payload, dict) or not payload.get('q'):
        raise IntroTokenError("Test tokeni yaroqsiz.", 'invalid_token')
    return payload
