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


class AIExplanationService(StaticExplanationService):
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
