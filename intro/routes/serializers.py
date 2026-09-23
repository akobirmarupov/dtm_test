from rest_framework import serializers

from catalog.routes.serializers import (
    absolute_file_url,
    translated_options,
)
from common.i18n import LanguageContextMixin, translated
from intro.models import MAX_VIDEO_SIZE, IntroQuestion


class IntroQuestionSerializer(LanguageContextMixin, serializers.ModelSerializer):
    """Mijozga ketadigan ko'rinish — to'g'ri javob ATAYIN yo'q."""

    text = serializers.SerializerMethodField()
    options = serializers.SerializerMethodField()
    image = serializers.SerializerMethodField()
    video = serializers.SerializerMethodField()

    class Meta:
        model = IntroQuestion
        fields = ['id', 'kind', 'text', 'options', 'image', 'video', 'video_url']
        read_only_fields = fields

    def get_text(self, obj) -> str:
        return translated(obj, 'text', self.language)

    def get_options(self, obj) -> dict:
        return translated_options(obj, self.language)

    def get_image(self, obj) -> str | None:
        return absolute_file_url(obj.image, self.context.get('request'))

    def get_video(self, obj) -> str | None:
        return absolute_file_url(obj.video, self.context.get('request'))


class IntroAnswerSerializer(serializers.Serializer):
    question = serializers.IntegerField()
    selected_option = serializers.CharField(max_length=1, allow_blank=True)


class IntroSubmitSerializer(serializers.Serializer):
    """`POST /intro/submit/` so'rovi."""

    token = serializers.CharField()
    answers = IntroAnswerSerializer(many=True)


class IntroQuestionAdminSerializer(serializers.ModelSerializer):
    """Admin savol qo'shadi: matn, rasm va video shu yerdan yuklanadi."""

    class Meta:
        model = IntroQuestion
        fields = [
            'id', 'kind',
            'text', 'text_ru', 'text_en',
            'options', 'options_ru', 'options_en',
            'correct_option',
            'image', 'video', 'video_url',
            'explanation', 'explanation_ru', 'explanation_en',
            'order', 'is_active', 'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def validate_options(self, value):
        if not isinstance(value, dict) or len(value) < 2:
            raise serializers.ValidationError(
                "Kamida ikkita variant bo'lishi kerak: "
                '{"A": "Birinchi", "B": "Ikkinchi"}'
            )
        if any(not str(text).strip() for text in value.values()):
            raise serializers.ValidationError("Variant matni bo'sh bo'lmasin.")
        return value

    def validate_video(self, value):
        if value and value.size > MAX_VIDEO_SIZE:
            raise serializers.ValidationError(
                f"Video hajmi {MAX_VIDEO_SIZE // (1024 * 1024)} MB dan oshmasligi kerak. "
                f"Kattaroq video uchun havola (video_url) ishlating."
            )
        return value

    def validate(self, attrs):
        """Mantiqiy savolda to'g'ri javob majburiy va u variantlar ichida bo'lsin."""
        instance = getattr(self, 'instance', None)

        def current(name):
            return attrs[name] if name in attrs else getattr(instance, name, None)

        kind = current('kind') or IntroQuestion.Kind.LOGIC
        correct = (current('correct_option') or '').strip()
        options = current('options') or {}

        if kind == IntroQuestion.Kind.LOGIC:
            if not correct:
                raise serializers.ValidationError({
                    'correct_option': "Mantiqiy savolda to'g'ri javob ko'rsatilishi kerak.",
                })
            if correct not in options:
                raise serializers.ValidationError({
                    'correct_option': f"«{correct}» variantlar ichida yo'q: {list(options)}.",
                })
        elif correct:
            raise serializers.ValidationError({
                'correct_option': "Psixologik savolda to'g'ri javob bo'lmaydi — bo'sh qoldiring.",
            })

        return attrs
