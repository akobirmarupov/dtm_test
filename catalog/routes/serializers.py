import re

from rest_framework import serializers

from catalog.models import Grade, Question, Subject, Topic
from common.i18n import LANGUAGE_SUFFIX,LanguageContextMixin,translated,translations_of



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
    name = serializers.SerializerMethodField()
    translations = serializers.SerializerMethodField()
    grade_count = serializers.SerializerMethodField()
    topic_count = serializers.SerializerMethodField()
    has_test = serializers.SerializerMethodField()

    class Meta:
        model = Subject
        fields = [
            "id", "name", "translations", "grade_count", "topic_count",
            "has_test", "created_at", "updated_at",
        ]
        read_only_fields = fields

    def get_name(self, obj) -> str:
        return translated(obj, 'name', self.language)

    def get_translations(self, obj) -> dict:
        return translations_of(obj, 'name')

    def get_grade_count(self, obj) -> int:
        value = getattr(obj, 'active_grade_count', None)
        if value is not None:
            return value
        return obj.grades.filter(is_active=True).count()

    def get_topic_count(self, obj) -> int:
        value = getattr(obj, 'active_topic_count', None)
        if value is not None:
            return value
        return obj.topics.filter(is_active=True).count()

    def get_has_test(self, obj) -> bool:
        """Shu fanda test ochish mumkin bo'lgan hech bo'lmasa bitta mavzu
        bormi. Savollar SONI ATAYIN qaytarilmaydi — foydalanuvchi baza
        hajmini bilmasligi kerak."""
        from testengine.models import MIN_TIER
        value = getattr(obj, 'testable_topic_count', None)
        if value is not None:
            return value > 0
        return obj.topics.filter(
            is_active=True, available_question_count__gte=MIN_TIER
        ).exists()


# ---------------------------------------------------------------------------
# Grade (Sinf / Kitob)
# ---------------------------------------------------------------------------
class GradeSerializer(LanguageContextMixin, serializers.ModelSerializer):
    name = serializers.SerializerMethodField()
    subject_name = serializers.SerializerMethodField()
    translations = serializers.SerializerMethodField()
    topic_count = serializers.SerializerMethodField()
    has_test = serializers.SerializerMethodField()

    class Meta:
        model = Grade
        fields = [
            "id", "subject", "subject_name", "name", "translations", "order",
            "is_active", "topic_count", "has_test", "created_at", "updated_at",
        ]
        read_only_fields = fields

    def get_name(self, obj) -> str:
        return translated(obj, 'name', self.language)

    def get_subject_name(self, obj) -> str:
        return translated(obj.subject, 'name', self.language)

    def get_translations(self, obj) -> dict:
        return translations_of(obj, 'name')

    def get_topic_count(self, obj) -> int:
        value = getattr(obj, 'active_topic_count', None)
        if value is not None:
            return value
        return obj.topics.filter(is_active=True).count()

    def get_has_test(self, obj) -> bool:
        from testengine.models import MIN_TIER
        value = getattr(obj, 'testable_topic_count', None)
        if value is not None:
            return value > 0
        return obj.topics.filter(
            is_active=True, available_question_count__gte=MIN_TIER
        ).exists()


class GradeWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Grade
        fields = ["id", "subject", "name", "name_ru", "name_en", "order", "is_active"]
        read_only_fields = ["id"]

    def validate_name(self, value):
        value = (value or '').strip()
        if not value:
            raise serializers.ValidationError("Sinf/kitob nomi bo'sh bo'lishi mumkin emas.")
        return value

    def validate(self, attrs):
        subject = attrs.get("subject", getattr(self.instance, "subject", None))
        name = attrs.get("name", getattr(self.instance, "name", None))
        if subject and name:
            qs = Grade.objects.filter(subject=subject, name__iexact=name.strip())
            if self.instance:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                raise serializers.ValidationError(
                    {"name": "Bu fan ichida shu nomli sinf/kitob allaqachon mavjud."}
                )
        return attrs


class SubjectWriteSerializer(serializers.ModelSerializer):
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
    grade_name = serializers.SerializerMethodField()
    translations = serializers.SerializerMethodField()
    has_test = serializers.SerializerMethodField()
    available_counts = serializers.SerializerMethodField()
    question_count = serializers.SerializerMethodField()

    class Meta:
        model = Topic
        fields = [
            "id", "subject", "subject_name", "grade", "grade_name", "name",
            "translations", "order", "is_active", "has_test",
            "available_counts", "question_count", "created_at", "updated_at",
        ]
        read_only_fields = fields

    def get_name(self, obj) -> str:
        return translated(obj, 'name', self.language)

    def get_subject_name(self, obj) -> str:
        return translated(obj.subject, 'name', self.language)

    def get_grade_name(self, obj) -> str | None:
        return translated(obj.grade, 'name', self.language) if obj.grade_id else None

    def get_translations(self, obj) -> dict:
        return translations_of(obj, 'name')

    def get_has_test(self, obj) -> bool:
        from testengine.models import MIN_TIER
        return obj.is_active and obj.available_question_count >= MIN_TIER

    def get_available_counts(self, obj) -> list[int]:
        """Shu foydalanuvchi tanlay oladigan savol sonlari."""
        from billing.entitlements import entitlements_for_request
        from testengine.access import tiers_for

        request = self.context.get('request')
        entitlements = self.context.get('entitlements')
        if entitlements is None and request is not None:
            entitlements = entitlements_for_request(request)
        if entitlements is None:
            from testengine.access import get_available_tiers
            return get_available_tiers(obj.available_question_count)
        return tiers_for(entitlements, obj.available_question_count)

    def get_question_count(self, obj) -> int | None:
        from common.models import Role
        request = self.context.get('request')
        user = getattr(request, 'user', None)
        if getattr(user, 'role', None) in (Role.MENTOR, Role.ADMIN):
            return obj.available_question_count
        return None


class TopicWriteSerializer(serializers.ModelSerializer):
    subject = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = Topic
        fields = [
            "id", "grade", "subject", "name", "name_ru", "name_en",
            "order", "is_active",
        ]
        read_only_fields = ["id", "subject"]

    def validate_name(self, value):
        value = value.strip()
        if not value:
            raise serializers.ValidationError("Mavzu nomi bo'sh bo'lishi mumkin emas.")
        return value

    def validate(self, attrs):
        grade = attrs.get("grade", getattr(self.instance, "grade", None))
        name = attrs.get("name", getattr(self.instance, "name", None))
        if grade is None:
            raise serializers.ValidationError(
                {"grade": "Mavzu qaysi sinf/kitobga tegishli ekanini ko'rsating."}
            )
        if name:
            qs = Topic.objects.filter(grade=grade, name__iexact=name.strip())
            if self.instance:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                raise serializers.ValidationError(
                    {"name": "Bu sinf/kitob ichida shu nomli mavzu allaqachon mavjud."}
                )
        return attrs


# ---------------------------------------------------------------------------
# Question
# ---------------------------------------------------------------------------
class QuestionSerializer(LanguageContextMixin, serializers.ModelSerializer):
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


class FormSafeBooleanField(serializers.BooleanField):
    default_empty_html = serializers.empty


class QuestionWriteSerializer(serializers.ModelSerializer):
    is_active = FormSafeBooleanField(required=False)
    image = serializers.ImageField(required=False, allow_null=True)
    image_url = serializers.SerializerMethodField()
    explanation_image = serializers.ImageField(required=False, allow_null=True)
    explanation_image_url = serializers.SerializerMethodField()

    MAX_IMAGE_BYTES = 5 * 1024 * 1024

    class Meta:
        model = Question
        fields = [
            "id", "topic", "text", "text_ru", "text_en",
            "options", "options_ru", "options_en",
            "image", "image_url", "image_caption",
            "correct_option", "difficulty",
            "explanation", "explanation_ru", "explanation_en",
            "explanation_image", "explanation_image_url", "hint",
            "status", "is_active", "source", "source_year",
        ]
        read_only_fields = ["id", "image_url", "explanation_image_url"]

    def get_image_url(self, obj) -> str | None:
        return absolute_image_url(obj, self.context.get('request'))

    def get_explanation_image_url(self, obj) -> str | None:
        return absolute_file_url(obj.explanation_image, self.context.get('request'))

    def validate_explanation_image(self, value):
        if value in (None, ''):
            return None
        if value.size > self.MAX_IMAGE_BYTES:
            raise serializers.ValidationError(
                f"Rasm hajmi {self.MAX_IMAGE_BYTES // (1024 * 1024)} MB dan "
                f"oshmasligi kerak."
            )
        return value

    def validate_source_year(self, value):
        if value is None:
            return value
        if not (1990 <= value <= 2100):
            raise serializers.ValidationError("Yil 1990–2100 oralig'ida bo'lishi kerak.")
        return value

    def create(self, validated_data):

        request = self.context.get('request')
        user = getattr(request, 'user', None)
        if user is not None and getattr(user, 'is_authenticated', False):
            validated_data.setdefault('author', user)
        return super().create(validated_data)

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

        for field, label in (("options_ru", "Ruscha"), ("options_en", "Inglizcha")):
            translated_value = attrs.get(field, getattr(self.instance, field, None))
            if translated_value and options and set(translated_value) != set(options):
                raise serializers.ValidationError({
                    field: f"{label} variantlar kalitlari asosiy variantlar bilan "
                           f"bir xil bo'lishi kerak: {sorted(options)}"
                })

        return attrs


class QuestionAdminSerializer(QuestionWriteSerializer):
    topic_name = serializers.CharField(source='topic.name', read_only=True)
    subject_id = serializers.IntegerField(source='topic.subject_id', read_only=True)
    grade_id = serializers.IntegerField(source='topic.grade_id', read_only=True)
    has_image = serializers.SerializerMethodField()
    has_explanation = serializers.SerializerMethodField()
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    p_value = serializers.FloatField(read_only=True)
    observed_difficulty = serializers.IntegerField(read_only=True)
    avg_time_seconds = serializers.IntegerField(read_only=True)
    author_email = serializers.CharField(source='author.email', read_only=True, default=None)

    class Meta(QuestionWriteSerializer.Meta):
        fields = QuestionWriteSerializer.Meta.fields + [
            "topic_name", "subject_id", "grade_id", "has_image",
            "has_explanation", "status_display", "times_answered",
            "times_correct", "p_value", "observed_difficulty",
            "avg_time_seconds", "author_email", "created_at", "updated_at",
        ]

    def get_has_image(self, obj) -> bool:
        return bool(obj.image)

    def get_has_explanation(self, obj) -> bool:
        return bool(obj.explanation or obj.explanation_image)


# ---------------------------------------------------------------------------
# Yordamchilar
# ---------------------------------------------------------------------------
def translated_options(question, language) -> dict:
    base = question.options if isinstance(question.options, dict) else {}
    suffix = LANGUAGE_SUFFIX.get(language, '')
    if not suffix:
        return base

    candidate = getattr(question, f'options{suffix}', None)
    if isinstance(candidate, dict) and candidate and set(candidate) == set(base):
        return candidate
    return base


def absolute_file_url(file_field, request) -> str | None:
    if not file_field:
        return None
    url = file_field.url
    return request.build_absolute_uri(url) if request else url

def absolute_image_url(question, request) -> str | None:
    return absolute_file_url(question.image, request)
