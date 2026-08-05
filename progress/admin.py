from django.contrib import admin

from unfold.admin import ModelAdmin

from .models import ReviewCard, Streak, XPTransaction


@admin.register(ReviewCard)
class ReviewCardAdmin(ModelAdmin):
    list_display = ("user", "question", "stability_days", "next_review_date")
    list_filter = ("next_review_date",)
    search_fields = ("user__email", "question__text")
    autocomplete_fields = ("user", "question")
    ordering = ("next_review_date",)


@admin.register(Streak)
class StreakAdmin(ModelAdmin):
    list_display = ("user", "current_streak", "longest_streak", "last_activity_date", "freezes_available")
    list_filter = ("last_activity_date",)
    search_fields = ("user__email",)
    autocomplete_fields = ("user",)
    ordering = ("-current_streak",)


@admin.register(XPTransaction)
class XPTransactionAdmin(ModelAdmin):
    list_display = ("user", "amount", "source", "description", "created_at")
    list_filter = ("source",)
    search_fields = ("user__email", "description")
    autocomplete_fields = ("user",)
    ordering = ("-created_at",)
