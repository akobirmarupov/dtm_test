import django_filters
from billing.models import Plan, Subscription, Payment


class PlanFilter(django_filters.FilterSet):
    price_min = django_filters.NumberFilter(field_name='price', lookup_expr='gte')
    price_max = django_filters.NumberFilter(field_name='price', lookup_expr='lte')
    duration_days_min = django_filters.NumberFilter(field_name='duration_days', lookup_expr='gte')
    duration_days_max = django_filters.NumberFilter(field_name='duration_days', lookup_expr='lte')

    class Meta:
        model = Plan
        fields = ['name']


class SubscriptionFilter(django_filters.FilterSet):
    status = django_filters.ChoiceFilter(choices=Subscription.Status.choices)
    starts_at_after = django_filters.DateTimeFilter(field_name='starts_at', lookup_expr='gte')
    starts_at_before = django_filters.DateTimeFilter(field_name='starts_at', lookup_expr='lte')
    expires_at_after = django_filters.DateTimeFilter(field_name='expires_at', lookup_expr='gte')
    expires_at_before = django_filters.DateTimeFilter(field_name='expires_at', lookup_expr='lte')

    class Meta:
        model = Subscription
        fields = ['user', 'plan', 'status']


class PaymentFilter(django_filters.FilterSet):
    status = django_filters.ChoiceFilter(choices=Payment.Status.choices)
    provider = django_filters.ChoiceFilter(choices=Payment.Provider.choices)
    amount_min = django_filters.NumberFilter(field_name='amount', lookup_expr='gte')
    amount_max = django_filters.NumberFilter(field_name='amount', lookup_expr='lte')
    created_at_after = django_filters.DateTimeFilter(field_name='created_at', lookup_expr='gte')
    created_at_before = django_filters.DateTimeFilter(field_name='created_at', lookup_expr='lte')

    class Meta:
        model = Payment
        fields = ['user', 'status', 'provider']
