from rest_framework import serializers

from account.models import Device, Language, User


class GoogleAuthSerializer(serializers.Serializer):
    """Android va web mijozlar uchun Google `id_token`."""

    id_token = serializers.CharField()
    device = serializers.DictField(required=False)


class AppleAuthSerializer(serializers.Serializer):
    """iPhone/iPad uchun Apple ID `identity_token`.

    `full_name` — Apple ismni FAQAT birinchi kirishda beradi, tokenda emas.
    Shuning uchun mijoz uni alohida yuboradi.
    """

    identity_token = serializers.CharField()
    full_name = serializers.CharField(required=False, allow_blank=True)
    nonce = serializers.CharField(required=False, allow_blank=True)
    device = serializers.DictField(required=False)


class DeviceSerializer(serializers.ModelSerializer):
    platform_display = serializers.CharField(source='get_platform_display', read_only=True)

    class Meta:
        model = Device
        fields = [
            "id", "device_id", "platform", "platform_display", "push_token",
            "model_name", "os_version", "app_version", "language",
            "is_active", "last_seen_at", "created_at",
        ]
        read_only_fields = ["id", "platform_display", "last_seen_at", "created_at"]

    def validate_device_id(self, value):
        value = str(value).strip()
        if not value:
            raise serializers.ValidationError("device_id bo'sh bo'lishi mumkin emas.")
        return value


class UserSerializer(serializers.ModelSerializer):
    role_display = serializers.CharField(source='get_role_display', read_only=True)
    has_google = serializers.SerializerMethodField()
    has_apple = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            "id", "email", "full_name", "avatar_url", "role", "role_display",
            "language", "phone_number", "telegram_username", "region",
            "target_major", "xp_total", "has_google", "has_apple", "created_at",
        ]
        read_only_fields = fields

    def get_has_google(self, obj) -> bool:
        return bool(obj.google_id)

    def get_has_apple(self, obj) -> bool:
        return bool(obj.apple_id)


class ProfileUpdateSerializer(serializers.ModelSerializer):
    """Foydalanuvchi o'zi tahrirlay oladigan maydonlar.

    `role` va `xp_total` ATAYIN yo'q — aks holda har kim o'zini admin qilib
    oladi yoki XP sini shishirib leaderboardni buzadi.
    """

    class Meta:
        model = User
        fields = [
            "full_name", "avatar_url", "language", "phone_number",
            "telegram_username", "region", "target_major",
            "consent_share_with_universities",
        ]

    def validate_language(self, value):
        if value not in Language.values:
            raise serializers.ValidationError(
                f"Til quyidagilardan biri bo'lishi kerak: {', '.join(Language.values)}"
            )
        return value

    def validate_phone_number(self, value):
        value = str(value or '').strip()
        if value and not value.replace('+', '').replace(' ', '').isdigit():
            raise serializers.ValidationError("Telefon raqami noto'g'ri formatda.")
        return value

    def validate_telegram_username(self, value):
        return str(value or '').strip().lstrip('@')

    def update(self, instance, validated_data):
        from django.utils import timezone

        if 'consent_share_with_universities' in validated_data:
            if validated_data['consent_share_with_universities'] != \
                    instance.consent_share_with_universities:
                instance.consent_updated_at = timezone.now()

        return super().update(instance, validated_data)


class LogoutSerializer(serializers.Serializer):
    refresh = serializers.CharField()
    device_id = serializers.CharField(required=False, allow_blank=True)
