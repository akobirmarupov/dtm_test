from django.contrib import admin

from unfold.admin import ModelAdmin

from .models import (
    Achievement, ReviewCard, Streak,
    UserAchievement, XPTransaction,)


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


@admin.register(Achievement)
class AchievementAdmin(ModelAdmin):
    """Yutuq ta'rifi. Yangi nishon qo'shish uchun deploy KERAK EMAS —
    shu yerdan qo'shiladi va darhol ishlaydi."""

    list_display = ('icon', 'name', 'code', 'metric', 'threshold', 'xp_reward',
                    'is_active', 'unlocked_count')
    list_filter = ('metric', 'is_active')
    search_fields = ('code', 'name', 'name_ru', 'name_en')
    list_editable = ('is_active',)
    ordering = ('metric', 'threshold')
    fieldsets = (
        ('Asosiy', {'fields': ('code', 'icon', 'is_active', 'order')}),
        ('Shart', {
            'fields': ('metric', 'threshold', 'xp_reward'),
            'description': "Yutuq `metric` qiymati `threshold` ga yetganda beriladi. "
                           "«Fan darajasi» uchun qiymat ⭐ x10 (4.2 ⭐ -> 42).",
        }),
        ("O'zbekcha", {'fields': ('name', 'description')}),
        ('Ruscha', {'fields': ('name_ru', 'description_ru')}),
        ('Inglizcha', {'fields': ('name_en', 'description_en')}),
    )

    @admin.display(description='Qo\'lga kiritganlar')
    def unlocked_count(self, obj):
        return obj.unlocked_by.count()


@admin.register(UserAchievement)
class UserAchievementAdmin(ModelAdmin):
    list_display = ('user', 'achievement', 'value_at_unlock', 'created_at')
    list_filter = ('achievement__metric', 'created_at')
    search_fields = ('user__email', 'achievement__code')
    autocomplete_fields = ('user', 'achievement')
    ordering = ('-created_at',)
    readonly_fields = ('user', 'achievement', 'value_at_unlock', 'created_at', 'updated_at')

    def has_add_permission(self, request):
        return False
