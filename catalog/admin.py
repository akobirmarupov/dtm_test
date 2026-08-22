from django.contrib import admin
from django.utils.html import format_html

from unfold.admin import ModelAdmin, TabularInline

from .models import Question, Subject, Topic


class TopicInline(TabularInline):
    model = Topic
    extra = 0
    fields = ("name", "name_ru", "name_en")
    show_change_link = True


@admin.register(Subject)
class SubjectAdmin(ModelAdmin):
    list_display = ("name", "name_ru", "name_en", "created_at")
    search_fields = ("name", "name_ru", "name_en")
    ordering = ("name",)
    inlines = (TopicInline,)
    fieldsets = (
        ("O'zbekcha", {"fields": ("name",)}),
        ("Tarjimalar", {"fields": ("name_ru", "name_en")}),
    )


@admin.register(Topic)
class TopicAdmin(ModelAdmin):
    list_display = ("name", "subject", "name_ru", "name_en", "created_at")
    list_filter = ("subject",)
    search_fields = ("name", "name_ru", "name_en", "subject__name")
    autocomplete_fields = ("subject",)
    ordering = ("subject", "name")
    fieldsets = (
        ("Asosiy", {"fields": ("subject", "name")}),
        ("Tarjimalar", {"fields": ("name_ru", "name_en")}),
    )


@admin.register(Question)
class QuestionAdmin(ModelAdmin):
    list_display = (
        "id", "short_text", "topic", "difficulty", "correct_option",
        "image_preview", "created_at",
    )
    list_filter = ("difficulty", "topic__subject", "topic")
    search_fields = ("text", "text_ru", "text_en", "topic__name")
    autocomplete_fields = ("topic",)
    ordering = ("-created_at",)
    readonly_fields = ("image_preview",)

    fieldsets = (
        ("Asosiy", {"fields": ("topic", "difficulty", "correct_option")}),
        ("O'zbekcha", {"fields": ("text", "options")}),
        ("Ruscha (ixtiyoriy)", {"fields": ("text_ru", "options_ru")}),
        ("Inglizcha (ixtiyoriy)", {"fields": ("text_en", "options_en")}),
        ("Rasm (ixtiyoriy)", {"fields": ("image", "image_caption", "image_preview")}),
    )

    @admin.display(description="Savol matni")
    def short_text(self, obj):
        return obj.text[:60]

    @admin.display(description="Rasm")
    def image_preview(self, obj):
        if not obj.image:
            return "—"
        return format_html(
            '<img src="{}" style="max-height:120px;border-radius:8px" />', obj.image.url
        )
