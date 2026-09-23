from django.contrib import admin, messages
from unfold.admin import ModelAdmin
from billing.services import SubscriptionError, approve_payment, reject_payment
from .models import Payment, Plan, Subscription


@admin.register(Plan)
class PlanAdmin(ModelAdmin):
    list_display = (
        "id", "name", "code", "price", "duration_days", "is_pro",
        "daily_topic_limit", "can_view_explanations", "can_view_analytics",
        "is_active", "created_at",
    )
    list_filter = ("is_active", "is_pro", "can_view_explanations")
    search_fields = ("name", "name_ru", "name_en", "code")
    ordering = ("price", "id")
    list_editable = ("price", "is_active")
    fieldsets = (
        ("Asosiy", {"fields": ("code", "price", "duration_days", "is_active")}),
        ("Imkoniyatlar", {
            "fields": (
                "is_pro",
                "daily_topic_limit", "max_question_count", "can_choose_question_count",
                "can_use_exam_mode",
                "can_view_explanations", "explanation_limit_per_day",
                "mistake_test_daily_limit", "review_cards_daily_limit",
                "can_view_analytics", "history_days", "streak_freezes_per_month",
                "features",
            ),
            "description": (
                "Narx ham, cheklovlar ham SHU YERDA boshqariladi — kodda emas. "
                "Raqamli maydon bo'sh qoldirilsa CHEKSIZ, 0 qo'yilsa imkoniyat "
                "YOPIQ degani. «Pullik tarif» ptichkasi hech narsani bekor "
                "qilmaydi — u faqat belgi."
            ),
        }),
        ("O'zbekcha", {"fields": ("name", "description")}),
        ("Ruscha", {"fields": ("name_ru", "description_ru")}),
        ("Inglizcha", {"fields": ("name_en", "description_en")}),
    )

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        from billing.entitlements import invalidate_free_plan_cache
        invalidate_free_plan_cache()


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
