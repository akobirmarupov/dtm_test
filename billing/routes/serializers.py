from rest_framework import serializers

from billing.models import Payment, Plan, Subscription
from common.i18n import LanguageContextMixin, translated, translations_of


class PlanSerializer(LanguageContextMixin, serializers.ModelSerializer):
    """Tarif — so'rov tilida. Frontend narxni o'zi formatlashi uchun
    `price` raqam bo'lib qoladi, `price_display` esa tayyor matn."""

    name = serializers.SerializerMethodField()
    description = serializers.SerializerMethodField()
    price_display = serializers.SerializerMethodField()
    is_free = serializers.BooleanField(read_only=True)
    translations = serializers.SerializerMethodField()

    class Meta:
        model = Plan
        fields = [
            'id', 'name', 'description', 'price', 'price_display', 'is_free',
            'duration_days', 'is_active', 'translations',
        ]
        read_only_fields = fields

    def get_name(self, obj) -> str:
        return translated(obj, 'name', self.language)

    def get_description(self, obj) -> str:
        return translated(obj, 'description', self.language) or ''

    def get_price_display(self, obj) -> str:
        from billing.telegram import format_price
        return "Bepul" if obj.is_free else format_price(obj.price)

    def get_translations(self, obj) -> dict:
        return {
            'name': translations_of(obj, 'name'),
            'description': translations_of(obj, 'description'),
        }


class PlanWriteSerializer(serializers.ModelSerializer):
    """Admin tarif yaratadi/tahrirlaydi."""

    class Meta:
        model = Plan
        fields = [
            'id', 'name', 'name_ru', 'name_en',
            'description', 'description_ru', 'description_en',
            'price', 'duration_days', 'is_active',
        ]
        read_only_fields = ['id']

    def validate_name(self, value):
        value = (value or '').strip()
        if not value:
            raise serializers.ValidationError("Tarif nomi bo'sh bo'lishi mumkin emas.")
        return value

    def validate_price(self, value):
        if value < 0:
            raise serializers.ValidationError("Narx manfiy bo'lishi mumkin emas.")
        return value

    def validate_duration_days(self, value):
        if value < 1:
            raise serializers.ValidationError("Muddat kamida 1 kun bo'lishi kerak.")
        return value


class SubscriptionSerializer(LanguageContextMixin, serializers.ModelSerializer):
    plan = PlanSerializer(read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    is_currently_active = serializers.BooleanField(read_only=True)
    days_left = serializers.IntegerField(read_only=True)

    class Meta:
        model = Subscription
        fields = [
            'id', 'plan', 'user', 'status', 'status_display', 'is_currently_active',
            'starts_at', 'expires_at', 'days_left', 'created_at',
        ]
        read_only_fields = fields


class PaymentSerializer(LanguageContextMixin, serializers.ModelSerializer):
    """Ariza. Foydalanuvchi ham, admin ham shu ko'rinishni oladi."""

    user_email = serializers.CharField(source='user.email', read_only=True)
    user_full_name = serializers.CharField(source='user.full_name', read_only=True)
    plan = PlanSerializer(read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    amount_display = serializers.SerializerMethodField()

    class Meta:
        model = Payment
        fields = [
            'id', 'user', 'user_email', 'user_full_name', 'plan', 'subscription',
            'provider', 'provider_transaction_id', 'amount', 'amount_display',
            'status', 'status_display', 'contact_phone', 'contact_telegram', 'note',
            'rejection_reason', 'reviewed_at', 'created_at',
        ]
        read_only_fields = fields

    def get_amount_display(self, obj) -> str:
        from billing.telegram import format_price
        return format_price(obj.amount)


class SubscriptionRequestSerializer(serializers.Serializer):
    """"Ariza yuborish" tugmasi ortidagi so'rov."""

    plan_id = serializers.IntegerField(required=False)
    plan = serializers.IntegerField(required=False)
    contact_phone = serializers.CharField(required=False, allow_blank=True, max_length=20)
    contact_telegram = serializers.CharField(required=False, allow_blank=True, max_length=64)
    note = serializers.CharField(required=False, allow_blank=True, max_length=1000)

    def validate(self, attrs):
        # Eski mijozlar `plan`, yangilari `plan_id` yuboradi — ikkalasi ham qabul.
        plan_id = attrs.get('plan_id') or attrs.get('plan')
        if not plan_id:
            raise serializers.ValidationError({"plan_id": "Tarif tanlanmagan."})
        attrs['plan_id'] = plan_id
        return attrs


class ContactPayloadSerializer(serializers.Serializer):
    label = serializers.CharField()
    url = serializers.CharField()
    username = serializers.CharField()
    prefilled_message = serializers.CharField()


class PlanEligibilitySerializer(serializers.Serializer):
    """Bitta tarif bo'yicha holat — tarif ekranidagi tugma shu asosda chiziladi."""

    plan = PlanSerializer(read_only=True)
    can_request = serializers.BooleanField()
    is_upgrade = serializers.BooleanField()
    reason_code = serializers.CharField()
    reason = serializers.CharField(allow_blank=True)
    available_at = serializers.DateTimeField(allow_null=True)


class EligibilityOverviewSerializer(serializers.Serializer):
    has_active_subscription = serializers.BooleanField()
    current_subscription = SubscriptionSerializer(allow_null=True)
    pending_request = PaymentSerializer(allow_null=True)
    plans = PlanEligibilitySerializer(many=True)
    contact = ContactPayloadSerializer()


class SubscriptionRequestResponseSerializer(serializers.Serializer):
    ariza = PaymentSerializer()
    subscription = SubscriptionSerializer()
    auto_activated = serializers.BooleanField()
    message = serializers.CharField()
    admin_telegram = serializers.CharField()
    contact = ContactPayloadSerializer()


class CurrentSubscriptionSerializer(serializers.Serializer):
    """`/subscriptions/current/` uchun BARQAROR shakl.

    Ilgari obuna bor/yo'qligiga qarab ikki xil JSON qaytardi — mobil mijoz
    uchun bu tipni aniqlashni imkonsiz qiladi. Endi shakl doim bir xil.
    """

    has_active_subscription = serializers.BooleanField()
    subscription = SubscriptionSerializer(allow_null=True)
    pending_request = PaymentSerializer(allow_null=True)


class PaymentRejectRequestSerializer(serializers.Serializer):
    reason = serializers.CharField(required=False, allow_blank=True, max_length=255)


class PaymentInfoSerializer(serializers.Serializer):
    message = serializers.CharField()
    admin_telegram = serializers.CharField()
    contact = ContactPayloadSerializer()


class DetailSerializer(serializers.Serializer):
    detail = serializers.CharField()


class SubscriptionErrorSerializer(serializers.Serializer):
    detail = serializers.CharField()
    code = serializers.CharField()
    available_at = serializers.DateTimeField(allow_null=True, required=False)
