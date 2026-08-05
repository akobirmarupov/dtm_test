from django.contrib import admin

from unfold.admin import ModelAdmin

from .models import Payment, Plan, Subscription


@admin.register(Plan)
class PlanAdmin(ModelAdmin):
    list_display = ("name", "price", "duration_days", "created_at")
    search_fields = ("name",)
    ordering = ("price",)


@admin.register(Subscription)
class SubscriptionAdmin(ModelAdmin):
    list_display = ("user", "plan", "status", "starts_at", "expires_at")
    list_filter = ("status", "plan")
    search_fields = ("user__email", "user__full_name")
    autocomplete_fields = ("user", "plan")
    ordering = ("-starts_at",)


@admin.register(Payment)
class PaymentAdmin(ModelAdmin):
    list_display = ("user", "provider", "provider_transaction_id", "amount", "status", "created_at")
    list_filter = ("provider", "status")
    search_fields = ("user__email", "provider_transaction_id")
    autocomplete_fields = ("user", "subscription")
    ordering = ("-created_at",)

    def get_readonly_fields(self, request, obj=None):
        if obj is None:
            return ()
        return ("provider", "provider_transaction_id", "amount")

