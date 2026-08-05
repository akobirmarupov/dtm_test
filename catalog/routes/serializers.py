import re
from rest_framework import serializers
from catalog.models import Question, Subject, Topic


OPTION_KEY_PATTERN = re.compile(r"^[A-Z]$")


class SubjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = Subject
        fields = ["id", "name", "created_at", "updated_at"]
        read_only_fields = ["id", "created_at", "updated_at"]

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


class TopicSerializer(serializers.ModelSerializer):
    class Meta:
        model = Topic
        fields = ["id", "subject", "name", "created_at", "updated_at"]
        read_only_fields = ["id", "created_at", "updated_at"]

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
                raise serializers.ValidationError({"name": "Bu fan ichida shu nomli mavzu allaqachon mavjud."})
        return attrs


class QuestionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Question
        fields = ["id", "topic", "text", "options", "difficulty"]
        read_only_fields = fields


class QuestionWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Question
        fields = ["id", "topic", "text", "options", "correct_option", "difficulty"]
        read_only_fields = ["id"]

    def validate_text(self, value):
        value = value.strip()
        if len(value) < 5:
            raise serializers.ValidationError("Savol matni juda qisqa.")
        return value

    def validate_options(self, value):
        if not isinstance(value, dict) or not (2 <= len(value) <= 6):
            raise serializers.ValidationError(
                "Variantlar 2 dan 6 tagacha bo'lgan {'A': '...'} obyekti bo'lishi kerak."
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

    def validate_correct_option(self, value):
        value = str(value).strip().upper()
        if not OPTION_KEY_PATTERN.match(value):
            raise serializers.ValidationError(
                "To'g'ri javob faqat bitta harf bo'lishi kerak (masalan: A)."
            )
        return value

    def validate(self, attrs):
        options = attrs.get("options", getattr(self.instance, "options", None))
        correct_option = attrs.get("correct_option", getattr(self.instance, "correct_option", None))
        if options and correct_option and correct_option not in options:
            raise serializers.ValidationError(
                {"correct_option": "To'g'ri javob variantlar ro'yxatida mavjud emas."}
            )
        return attrs
