from django.contrib import admin

from unfold.admin import ModelAdmin, StackedInline, TabularInline

from .models import Answer, TestResult, TestSession


class AnswerInline(TabularInline):
    model = Answer
    extra = 0
    fields = ("id", "question", "selected_option", "is_correct", "confidence", "time_spent_seconds")
    readonly_fields = ("question", "selected_option", "is_correct", "confidence", "time_spent_seconds")
    can_delete = False
    show_change_link = True


class TestResultInline(StackedInline):
    model = TestResult
    extra = 0
    can_delete = False


@admin.register(TestSession)
class TestSessionAdmin(ModelAdmin):
    list_display = ("id", "user", "subject", "mode", "started_at", "finished_at")
    list_filter = ("mode", "subject")
    search_fields = ("user__email", "user__full_name")
    autocomplete_fields = ("user", "subject")
    readonly_fields = ("started_at",)
    ordering = ("-started_at",)
    inlines = (AnswerInline, TestResultInline)


@admin.register(Answer)
class AnswerAdmin(ModelAdmin):
    list_display = ("id", "session", "question", "selected_option", "is_correct", "confidence", "time_spent_seconds")
    list_filter = ("is_correct", "confidence")
    search_fields = ("session__user__email", "question__text")
    autocomplete_fields = ("session", "question")
    ordering = ("-created_at",)


@admin.register(TestResult)
class TestResultAdmin(ModelAdmin):
    list_display = ("id", "session", "total_score", "correct_count", "incorrect_count", "duration_seconds")
    search_fields = ("session__user__email",)
    autocomplete_fields = ("session",)
    ordering = ("-created_at",)
