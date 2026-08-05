from django.contrib import admin

from unfold.admin import ModelAdmin, TabularInline

from .models import Question, Subject, Topic


class TopicInline(TabularInline):
    model = Topic
    extra = 0
    fields = ("name",)
    show_change_link = True


@admin.register(Subject)
class SubjectAdmin(ModelAdmin):
    list_display = ("name", "created_at")
    search_fields = ("name",)
    ordering = ("name",)
    inlines = (TopicInline,)


@admin.register(Topic)
class TopicAdmin(ModelAdmin):
    list_display = ("name", "subject", "created_at")
    list_filter = ("subject",)
    search_fields = ("name", "subject__name")
    autocomplete_fields = ("subject",)
    ordering = ("subject", "name")


@admin.register(Question)
class QuestionAdmin(ModelAdmin):
    list_display = ("short_text", "topic", "difficulty", "correct_option", "created_at")
    list_filter = ("difficulty", "topic__subject", "topic")
    search_fields = ("text", "topic__name")
    autocomplete_fields = ("topic",)
    ordering = ("-created_at",)

    @admin.display(description="Savol matni")
    def short_text(self, obj):
        return obj.text[:60]
