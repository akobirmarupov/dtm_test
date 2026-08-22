import re

from rest_framework import serializers

from catalog.models import Question, Subject, Topic
from common.i18n import (
    LANGUAGE_SUFFIX,
    LanguageContextMixin,
    translated,
    translations_of,
)


OPTION_KEY_PATTERN = re.compile(r"^[A-Z]$")


def validate_options_payload(value, field_label="Variantlar"):
    """`{'A': 'matn', 'B': '...'}` ko'rinishini tekshirib, normalizatsiya qiladi."""
    if not isinstance(value, dict) or not (2 <= len(value) <= 6):
        raise serializers.ValidationError(
            f"{field_label} 2 dan 6 tagacha bo'lgan {{'A': '...'}} obyekti bo'lishi kerak."
        )

    normalized = {}
    seen_texts = set()
    for key, text in value.items():
        key = str(key).strip().upper()
        if not OPTION_KEY_PATTERN.match(key):
            raise serializers.ValidationError(
                "Har bir variant kaliti bitta katta lotin harfi bo'lishi kerak (masalan: A, B, C)."
            )
        if not isinstance(text, str) or not text.strip():
            raise serializers.ValidationError(f"'{key}' varianti matni bo'sh bo'lishi mumkin emas.")
        if key in normalized:
            raise serializers.ValidationError(f"'{key}' kaliti takrorlangan.")

        normalized_text = text.strip().lower()
        if normalized_text in seen_texts:
            raise serializers.ValidationError("Variant matnlari bir-biridan farq qilishi kerak.")
        seen_texts.add(normalized_text)
        normalized[key] = text.strip()

    return normalized


# ---------------------------------------------------------------------------
# Subject
# ---------------------------------------------------------------------------
class SubjectSerializer(LanguageContextMixin, serializers.ModelSerializer):
    """O'qish uchun. `name` — so'rov tiliga mos tarjima; tarjima yo'q bo'lsa
    o'zbekchasi qaytadi."""

    name = serializers.SerializerMethodField()
    translations = serializers.SerializerMethodField()

    class Meta:
        model = Subject
        fields = ["id", "name", "translations", "created_at", "updated_at"]
        read_only_fields = fields

    def get_name(self, obj) -> str:
        return translated(obj, 'name', self.language)

    def get_translations(self, obj) -> dict:
        return translations_of(obj, 'name')


class SubjectWriteSerializer(serializers.ModelSerializer):
    """Yaratish/tahrirlash. `name` — o'zbekcha (majburiy), qolgan tillar ixtiyoriy."""

    class Meta:
        model = Subject
        fields = ["id", "name", "name_ru", "name_en"]
        read_only_fields = ["id"]

    def validate_name(self, value):
        value = value.strip()
        if not value:
            raise serializers.ValidationError("Fan nomi bo'sh bo'lishi mumkin emas.")
        qs = Subject.objects.filter(name__iexact=value)
        if self.instance:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise serializers.ValidationError("Bu nomdagi fan allaqachon mavjud.")
        return value

    def validate_name_ru(self, value):
        return (value or '').strip()

    def validate_name_en(self, value):
        return (value or '').strip()


# ---------------------------------------------------------------------------
# Topic
# ---------------------------------------------------------------------------
class TopicSerializer(LanguageContextMixin, serializers.ModelSerializer):
    name = serializers.SerializerMethodField()
    subject_name = serializers.SerializerMethodField()
    translations = serializers.SerializerMethodField()

    class Meta:
        model = Topic
        fields = [
            "id", "subject", "subject_name", "name", "translations",
            "created_at", "updated_at",
        ]
        read_only_fields = fields

    def get_name(self, obj) -> str:
        return translated(obj, 'name', self.language)

    def get_subject_name(self, obj) -> str:
        return translated(obj.subject, 'name', self.language)

    def get_translations(self, obj) -> dict:
        return translations_of(obj, 'name')


class TopicWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Topic
        fields = ["id", "subject", "name", "name_ru", "name_en"]
        read_only_fields = ["id"]

    def validate_name(self, value):
        value = value.strip()
        if not value:
            raise serializers.ValidationError("Mavzu nomi bo'sh bo'lishi mumkin emas.")
        return value

    def validate(self, attrs):
        subject = attrs.get("subject", getattr(self.instance, "subject", None))
        name = attrs.get("name", getattr(self.instance, "name", None))
        if subject and name:
            qs = Topic.objects.filter(subject=subject, name__iexact=name.strip())
            if self.instance:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                raise serializers.ValidationError(
                    {"name": "Bu fan ichida shu nomli mavzu allaqachon mavjud."}
                )
        return attrs


# ---------------------------------------------------------------------------
# Question
# ---------------------------------------------------------------------------
class QuestionSerializer(LanguageContextMixin, serializers.ModelSerializer):
    """Talaba ko'radigan savol. `correct_option` ATAYIN yo'q."""

    text = serializers.SerializerMethodField()
    options = serializers.SerializerMethodField()
    topic_name = serializers.SerializerMethodField()
    image = serializers.SerializerMethodField()
    has_image = serializers.SerializerMethodField()

    class Meta:
        model = Question
        fields = [
            "id", "topic", "topic_name", "text", "options",
            "image", "image_caption", "has_image", "difficulty",
        ]
        read_only_fields = fields

    def get_text(self, obj) -> str:
        return translated(obj, 'text', self.language)

    def get_options(self, obj) -> dict:
        return translated_options(obj, self.language)

    def get_topic_name(self, obj) -> str:
        return translated(obj.topic, 'name', self.language)

    def get_image(self, obj) -> str | None:
        return absolute_image_url(obj, self.context.get('request'))

    def get_has_image(self, obj) -> bool:
        return bool(obj.image)


class QuestionWriteSerializer(serializers.ModelSerializer):
    """Mentor/admin uchun: barcha tillar, rasm va to'g'ri javob."""

    image = serializers.ImageField(required=False, allow_null=True)
    image_url = serializers.SerializerMethodField()

    # Savol rasmi diagramma/grafik — bir necha yuz kilobayt yetadi. Chegara
    # bo'lmasa bitta savol serverdagi butun diskni yeb qo'yishi mumkin.
    MAX_IMAGE_BYTES = 5 * 1024 * 1024

    class Meta:
        model = Question
        fields = [
            "id", "topic", "text", "text_ru", "text_en",
            "options", "options_ru", "options_en",
            "image", "image_url", "image_caption",
            "correct_option", "difficulty",
        ]
        read_only_fields = ["id", "image_url"]

    def get_image_url(self, obj) -> str | None:
        return absolute_image_url(obj, self.context.get('request'))

    def validate_text(self, value):
        value = value.strip()
        if len(value) < 5:
            raise serializers.ValidationError("Savol matni juda qisqa.")
        return value

    def validate_image(self, value):
        if value in (None, ''):
            return None
        if value.size > self.MAX_IMAGE_BYTES:
            raise serializers.ValidationError(
                f"Rasm hajmi {self.MAX_IMAGE_BYTES // (1024 * 1024)} MB dan "
                f"oshmasligi kerak."
            )
        return value

    def validate_options(self, value):
        return validate_options_payload(value)

    def validate_options_ru(self, value):
        if value in (None, '', {}):
            return None
        return validate_options_payload(value, "Ruscha variantlar")

    def validate_options_en(self, value):
        if value in (None, '', {}):
            return None
        return validate_options_payload(value, "Inglizcha variantlar")

    def validate_correct_option(self, value):
        value = str(value).strip().upper()
        if not OPTION_KEY_PATTERN.match(value):
            raise serializers.ValidationError(
                "To'g'ri javob faqat bitta harf bo'lishi kerak (masalan: A)."
            )
        return value

    def validate(self, attrs):
        options = attrs.get("options", getattr(self.instance, "options", None))
        correct_option = attrs.get(
            "correct_option", getattr(self.instance, "correct_option", None)
        )
        if options and correct_option and correct_option not in options:
            raise serializers.ValidationError(
                {"correct_option": "To'g'ri javob variantlar ro'yxatida mavjud emas."}
            )

        # Tarjima qilingan variantlar kalitlari asosiy variantlar bilan bir xil
        # bo'lishi shart — aks holda ruscha ko'rinishda 'C' varianti yo'qolib,
        # foydalanuvchi tanlagan javob bazadagi javobga to'g'ri kelmay qoladi.
        for field, label in (("options_ru", "Ruscha"), ("options_en", "Inglizcha")):
            translated_value = attrs.get(field, getattr(self.instance, field, None))
            if translated_value and options and set(translated_value) != set(options):
                raise serializers.ValidationError({
                    field: f"{label} variantlar kalitlari asosiy variantlar bilan "
                           f"bir xil bo'lishi kerak: {sorted(options)}"
                })

        return attrs


class QuestionAdminSerializer(QuestionWriteSerializer):
    """Ro'yxatda qaytariladigan to'liq ko'rinish (mentor/admin)."""

    topic_name = serializers.CharField(source='topic.name', read_only=True)
    subject_id = serializers.IntegerField(source='topic.subject_id', read_only=True)
    has_image = serializers.SerializerMethodField()

    class Meta(QuestionWriteSerializer.Meta):
        fields = QuestionWriteSerializer.Meta.fields + [
            "topic_name", "subject_id", "has_image", "created_at", "updated_at",
        ]

    def get_has_image(self, obj) -> bool:
        return bool(obj.image)


# ---------------------------------------------------------------------------
# Yordamchilar
# ---------------------------------------------------------------------------
def translated_options(question, language) -> dict:
    """Variantlarni tanlangan tilda qaytaradi.

    Tarjima yo'q yoki kalitlari mos kelmasa asosiy variantlar qaytadi —
    javob kalitlari (A/B/C) har doim bir xil bo'lib qolishi shart.
    """
    base = question.options if isinstance(question.options, dict) else {}
    suffix = LANGUAGE_SUFFIX.get(language, '')
    if not suffix:
        return base

    candidate = getattr(question, f'options{suffix}', None)
    if isinstance(candidate, dict) and candidate and set(candidate) == set(base):
        return candidate
    return base


def absolute_image_url(question, request) -> str | None:
    """Rasmning to'liq URL manzili. Rasm yuklanmagan bo'lsa None."""
    if not question.image:
        return None
    url = question.image.url
    return request.build_absolute_uri(url) if request else url
