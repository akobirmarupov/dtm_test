from django.contrib import admin, messages

from unfold.admin import ModelAdmin

from billing.services import SubscriptionError, approve_payment, reject_payment

from .models import Payment, Plan, Subscription


@admin.register(Plan)
class PlanAdmin(ModelAdmin):
    list_display = ("id", "name", "price", "duration_days", "is_active", "created_at")
    list_filter = ("is_active",)
    search_fields = ("name", "name_ru", "name_en")
    ordering = ("price", "id")
    fieldsets = (
        ("Asosiy", {"fields": ("price", "duration_days", "is_active")}),
        ("O'zbekcha", {"fields": ("name", "description")}),
        ("Ruscha", {"fields": ("name_ru", "description_ru")}),
        ("Inglizcha", {"fields": ("name_en", "description_en")}),
    )


@admin.register(Subscription)
class SubscriptionAdmin(ModelAdmin):
    list_display = ("id", "user", "plan", "status", "starts_at", "expires_at", "days_left")
    list_filter = ("status", "plan")
    search_fields = ("user__email", "user__full_name")
    autocomplete_fields = ("user", "plan")
    ordering = ("-starts_at",)

    @admin.display(description="Qolgan kun")
    def days_left(self, obj):
        return obj.days_left


@admin.register(Payment)
class PaymentAdmin(ModelAdmin):
    """Arizalar. Admin shu yerdan bir bosishda tasdiqlaydi yoki rad etadi."""

    list_display = (
        "id", "user", "plan", "amount", "status", "contact_phone",
        "contact_telegram", "reviewed_by", "created_at",
    )
    list_filter = ("status", "provider", "plan")
    search_fields = (
        "user__email", "user__full_name", "provider_transaction_id",
        "contact_phone", "contact_telegram",
    )
    autocomplete_fields = ("user", "plan", "subscription")
    ordering = ("-created_at",)
    actions = ("approve_selected", "reject_selected")

    def get_readonly_fields(self, request, obj=None):
        base = ("reviewed_by", "reviewed_at")
        if obj is None:
            return base
        return base + ("provider", "provider_transaction_id", "amount", "plan")

    @admin.action(description="Tanlangan arizalarni TASDIQLASH (obunani faollashtirish)")
    def approve_selected(self, request, queryset):
        approved = 0
        for payment in queryset.filter(status=Payment.Status.PENDING):
            try:
                approve_payment(payment, request.user)
                approved += 1
            except SubscriptionError as exc:
                self.message_user(
                    request, f"#{payment.id}: {exc.message}", level=messages.WARNING
                )
        self.message_user(request, f"{approved} ta ariza tasdiqlandi.", level=messages.SUCCESS)

    @admin.action(description="Tanlangan arizalarni RAD ETISH")
    def reject_selected(self, request, queryset):
        rejected = 0
        for payment in queryset.filter(status=Payment.Status.PENDING):
            try:
                reject_payment(payment, request.user, reason="Admin panel orqali rad etildi")
                rejected += 1
            except SubscriptionError as exc:
                self.message_user(
                    request, f"#{payment.id}: {exc.message}", level=messages.WARNING
                )
        self.message_user(request, f"{rejected} ta ariza rad etildi.", level=messages.SUCCESS)
