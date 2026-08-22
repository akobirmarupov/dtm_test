from django.contrib import admin

from unfold.admin import ModelAdmin, StackedInline, TabularInline

from .models import Answer, SessionQuestion, TestResult, TestSession


class SessionQuestionInline(TabularInline):
    model = SessionQuestion
    extra = 0
    fields = ("order", "question")
    readonly_fields = ("order", "question")
    can_delete = False
    ordering = ("order",)
    show_change_link = True


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
    list_display = (
        "id", "user", "subject", "mode", "question_count",
        "answered", "started_at", "finished_at",
    )
    list_filter = ("mode", "subject", "finished_at")
    search_fields = ("user__email", "user__full_name")
    autocomplete_fields = ("user", "subject")
    readonly_fields = ("started_at",)
    ordering = ("-started_at",)
    inlines = (SessionQuestionInline, AnswerInline, TestResultInline)

    @admin.display(description="Javob berilgan")
    def answered(self, obj):
        return obj.answers.count()


@admin.register(SessionQuestion)
class SessionQuestionAdmin(ModelAdmin):
    list_display = ("id", "session", "order", "question")
    search_fields = ("session__user__email", "question__text")
    autocomplete_fields = ("session", "question")
    ordering = ("-session_id", "order")


@admin.register(Answer)
class AnswerAdmin(ModelAdmin):
    list_display = ("id", "session", "question", "selected_option", "is_correct", "confidence", "time_spent_seconds")
    list_filter = ("is_correct", "confidence")
    search_fields = ("session__user__email", "question__text")
    autocomplete_fields = ("session", "question")
    ordering = ("-created_at",)


@admin.register(TestResult)
class TestResultAdmin(ModelAdmin):
    list_display = (
        "id", "session", "total_score", "correct_count", "incorrect_count",
        "unanswered_count", "duration_seconds",
    )
    search_fields = ("session__user__email",)
    autocomplete_fields = ("session",)
    ordering = ("-created_at",)
