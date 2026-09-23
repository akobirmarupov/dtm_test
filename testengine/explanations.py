from __future__ import annotations

import logging

from django.conf import settings
from django.utils.module_loading import import_string

from common.i18n import DEFAULT_LANGUAGE, translated

logger = logging.getLogger('testengine.explanation')


class Explanation:
    __slots__ = ('text', 'image_url', 'source')

    def __init__(self, text='', image_url=None, source='static'):
        self.text = text or ''
        self.image_url = image_url
        self.source = source

    def __bool__(self):
        return bool(self.text or self.image_url)

    def as_dict(self):
        return {'text': self.text, 'image': self.image_url, 'source': self.source}


class ExplanationService:
    def for_question(self, question, *, answer=None, language=DEFAULT_LANGUAGE,
                     request=None) -> Explanation | None:
        raise NotImplementedError

    def for_review(self, review_items, *, language=DEFAULT_LANGUAGE, request=None) -> dict:
        result = {}
        for item in review_items:
            explanation = self.for_question(
                item.question, answer=None, language=language, request=request
            )
            if explanation:
                result[item.question_id] = explanation
        return result


class StaticExplanationService(ExplanationService):
    def for_question(self, question, *, answer=None, language=DEFAULT_LANGUAGE,
                     request=None) -> Explanation | None:
        text = translated(question, 'explanation', language)
        image_url = None
        if question.explanation_image:
            url = question.explanation_image.url
            image_url = request.build_absolute_uri(url) if request is not None else url

        if not text and not image_url:
            return None
        return Explanation(text=text, image_url=image_url, source='static')


def ai_tutor_allowed(request) -> bool:
    """Foydalanuvchining tarifida «AI tutor» ptichkasi bormi.

    Statik izoh hammaga (tarifi ruxsat bersa) ochiq, AI esa faqat shu
    ptichkasi bor tarifga — shuning uchun tekshiruv aynan shu yerda.
    """
    if request is None:
        return False
    from billing.entitlements import entitlements_for_request
    return bool(entitlements_for_request(request).feature('ai_tutor', False))


class AIExplanationService(StaticExplanationService):
    """AI tutor uchun tayyorlangan joy — hozir ishlamaydi.

    Yoqish uchun ikki qadam kerak:

    1. `generate()` ichida LLM chaqiruvini yozish;
    2. sozlamalarga
       ``EXPLANATION_SERVICE = 'testengine.explanations.AIExplanationService'``
       qo'shish.

    Shundan keyin ham AI izohi faqat tarifida `ai_tutor` ptichkasi bor
    foydalanuvchiga boradi; qolganlar statik izohni ko'raveradi. Shuning
    uchun ptichka katalogda `enforced: false` bilan turibdi — belgilash
    mumkin, lekin hozircha hech narsani o'zgartirmaydi.
    """

    def generate(self, question, answer, language) -> str | None:
        # TODO: LLM chaqiruvi. Kirish: savol matni, variantlar, to'g'ri javob,
        # foydalanuvchi tanlagan variant. Chiqish: qisqa tushuntirish.
        return None

    def for_question(self, question, *, answer=None, language=DEFAULT_LANGUAGE,
                     request=None) -> Explanation | None:
        static = super().for_question(
            question, answer=answer, language=language, request=request
        )
        if static is not None:
            return static

        if not ai_tutor_allowed(request):
            return None

        generated = self.generate(question, answer, language)
        if not generated:
            return None
        return Explanation(text=generated, source='ai')


_service = None


def get_explanation_service() -> ExplanationService:
    global _service
    if _service is None:
        path = getattr(
            settings, 'EXPLANATION_SERVICE',
            'testengine.explanations.StaticExplanationService',
        )
        try:
            _service = import_string(path)()
        except (ImportError, TypeError):
            logger.exception('EXPLANATION_SERVICE yuklanmadi: %s. Statik xizmat ishlatiladi.', path)
            _service = StaticExplanationService()
    return _service


def reset_explanation_service():
    global _service
    _service = None
