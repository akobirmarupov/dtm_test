"""Ko'p tillilik (uz / ru / en) uchun umumiy yordamchilar.

Kontent tarjimasi qo'shimcha kutubxonasiz, model ustunlari orqali saqlanadi:
`name` / `name_ru` / `name_en`. Sabab — `django-modeltranslation` kabi paket
migratsiyalarni o'zi generatsiya qiladi va bazadagi ustun nomlarini
yashiradi; bu yerda hammasi ochiq va oddiy.

Til quyidagi tartibda aniqlanadi:

1. `?lang=ru` query parametri (mobil ilovalar uchun eng qulayi);
2. `X-Language: ru` header;
3. Foydalanuvchi profilidagi `language`;
4. `Accept-Language` header;
5. `settings.LANGUAGE_CODE` (uz).
"""

from __future__ import annotations

from django.conf import settings

# Qo'llab-quvvatlanadigan tillar. Kalit — API da ishlatiladigan kod.
UZ = 'uz'
RU = 'ru'
EN = 'en'

SUPPORTED_LANGUAGES = (UZ, RU, EN)
DEFAULT_LANGUAGE = UZ

# `name` -> uz, `name_ru` -> ru, `name_en` -> en
LANGUAGE_SUFFIX = {UZ: '', RU: '_ru', EN: '_en'}


def normalize_language(value) -> str | None:
    """'ru-RU', 'RU', 'ru_ru' -> 'ru'. Noma'lum til uchun None."""
    if not value:
        return None
    code = str(value).strip().lower().replace('_', '-').split('-')[0]
    return code if code in SUPPORTED_LANGUAGES else None


def parse_accept_language(header) -> str | None:
    """`Accept-Language: ru-RU,ru;q=0.9,en;q=0.8` dan birinchi mos tilni oladi."""
    if not header:
        return None

    parsed = []
    for index, part in enumerate(str(header).split(',')):
        chunks = part.split(';')
        code = normalize_language(chunks[0])
        if not code:
            continue
        quality = 1.0
        for chunk in chunks[1:]:
            chunk = chunk.strip()
            if chunk.startswith('q='):
                try:
                    quality = float(chunk[2:])
                except ValueError:
                    quality = 0.0
        # `index` — bir xil q da header tartibini saqlaydi.
        parsed.append((-quality, index, code))

    if not parsed:
        return None
    parsed.sort()
    return parsed[0][2]


def resolve_language(request) -> str:
    """So'rov uchun amaldagi tilni qaytaradi."""
    if request is None:
        return DEFAULT_LANGUAGE

    query = getattr(request, 'query_params', None) or getattr(request, 'GET', {})
    language = normalize_language(query.get('lang')) if hasattr(query, 'get') else None
    if language:
        return language

    headers = getattr(request, 'headers', {})
    language = normalize_language(headers.get('X-Language'))
    if language:
        return language

    user = getattr(request, 'user', None)
    if user is not None and getattr(user, 'is_authenticated', False):
        language = normalize_language(getattr(user, 'language', None))
        if language:
            return language

    language = parse_accept_language(headers.get('Accept-Language'))
    if language:
        return language

    return normalize_language(getattr(settings, 'LANGUAGE_CODE', None)) or DEFAULT_LANGUAGE


def translated(obj, field: str, language: str = DEFAULT_LANGUAGE):
    """Modeldagi `field` ning tanlangan tildagi qiymati.

    Tarjima kiritilmagan bo'lsa asosiy (o'zbekcha) qiymat qaytadi — mijozda
    bo'sh matn chiqib qolmasligi uchun.
    """
    suffix = LANGUAGE_SUFFIX.get(language, '')
    if suffix:
        value = getattr(obj, f'{field}{suffix}', None)
        if value:
            return value
    return getattr(obj, field)


def translations_of(obj, field: str) -> dict:
    """Barcha tillardagi qiymatlar — admin/mentor tahrirlash oynasi uchun."""
    return {
        language: getattr(obj, f'{field}{suffix}', None) or None
        for language, suffix in LANGUAGE_SUFFIX.items()
    }


class LanguageContextMixin:
    """Serializerga `language` ni yetkazish uchun kichik yordamchi."""

    @property
    def language(self) -> str:
        context_language = (self.context or {}).get('language')
        if context_language in SUPPORTED_LANGUAGES:
            return context_language
        return resolve_language((self.context or {}).get('request'))
