
from __future__ import annotations

from django.core import signing

from billing.entitlements import GUEST_QUESTION_COUNT

SALT = 'testengine.guest.session'
TOKEN_MAX_AGE_SECONDS = 3 * 60 * 60


class GuestTokenError(Exception):
    def __init__(self, message, code='invalid_token'):
        super().__init__(message)
        self.message = message
        self.code = code


def issue_token(question_ids, topic_id=None, subject_id=None) -> str:
    payload = {
        'q': list(question_ids),
        't': topic_id,
        's': subject_id,
        'v': 1,
    }
    return signing.dumps(payload, salt=SALT, compress=True)


def read_token(token) -> dict:
    try:
        payload = signing.loads(token, salt=SALT, max_age=TOKEN_MAX_AGE_SECONDS)
    except signing.SignatureExpired:
        raise GuestTokenError(
            "Test muddati tugadi. Iltimos, testni qaytadan boshlang.",
            'token_expired',
        )
    except signing.BadSignature:
        raise GuestTokenError("Test tokeni yaroqsiz.", 'invalid_token')

    if not isinstance(payload, dict) or not payload.get('q'):
        raise GuestTokenError("Test tokeni yaroqsiz.", 'invalid_token')
    return payload


def build_guest_session(questions, topic=None, subject=None) -> dict:
    question_ids = [question.id for question in questions]
    return {
        'token': issue_token(
            question_ids,
            topic_id=getattr(topic, 'id', None),
            subject_id=getattr(subject, 'id', None),
        ),
        'question_count': len(question_ids),
        'questions': questions,
        'topic': topic,
        'subject': subject,
        'is_guest': True,
    }


def registration_prompt(answered_count, total_questions) -> dict:
    return {
        'requires_registration': True,
        'results_hidden': True,
        'total_questions': total_questions,
        'answered_count': answered_count,
        'code': 'registration_required',
        'title': "Natijangiz tayyor",
        'detail': (
            "Natijangizni ko'rish, xatolaringizni bilish, reytingda ishtirok "
            "etish va cheksiz test ishlash uchun ro'yxatdan o'ting."
        ),
        'actions': [
            {'code': 'register', 'label': "Ro'yxatdan o'tish", 'is_primary': True},
            {'code': 'later', 'label': 'Keyinroq', 'is_primary': False},
        ],
        'guest_question_count': GUEST_QUESTION_COUNT,
    }
