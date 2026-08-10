from rest_framework import serializers
from billing.models import Plan, Subscription, Payment


class PlanSerializer(serializers.ModelSerializer):
    class Meta:
        model = Plan
        fields = ['id', 'name', 'price', 'duration_days', 'is_active']
        read_only_fields = ['id']


class SubscriptionSerializer(serializers.ModelSerializer):
    plan = PlanSerializer(read_only=True)
    plan_id = serializers.PrimaryKeyRelatedField(
        queryset=Plan.objects.all(),
        write_only=True,
        source='plan'
    )

    class Meta:
        model = Subscription
        fields = ['id', 'plan', 'plan_id', 'user', 'status', 'starts_at', 'expires_at', 'created_at']
        read_only_fields = ['id', 'plan', 'user', 'status', 'starts_at', 'expires_at', 'created_at']


class PaymentSerializer(serializers.ModelSerializer):
    user_email = serializers.CharField(source='user.email', read_only=True)

    class Meta:
        model = Payment
        fields = ['id', 'user', 'user_email', 'subscription', 'amount', 'status', 'created_at']
        read_only_fields = fields
