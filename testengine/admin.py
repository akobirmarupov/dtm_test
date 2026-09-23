from django.contrib import admin

from unfold.admin import ModelAdmin, StackedInline, TabularInline

from .models import (
    Answer, DailyTopicUsage, ExplanationUsage, MockExam, SessionQuestion,
    TestResult, TestSession,
)



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


@admin.register(DailyTopicUsage)
class DailyTopicUsageAdmin(ModelAdmin):
    """Free foydalanuvchining kunlik mavzu hisobi.

    Faqat ko'rish uchun: qatorlar test boshlanganda avtomatik yoziladi va
    yangi kun kirishi bilan hisob o'z-o'zidan noldan boshlanadi.
    """

    list_display = ("date", "user", "topic", "sessions_started")
    list_filter = ("date", "topic__subject")
    search_fields = ("user__email", "topic__name")
    autocomplete_fields = ("user", "topic")
    ordering = ("-date", "-id")
    readonly_fields = ("user", "topic", "date", "sessions_started")

    def has_add_permission(self, request):
        return False


@admin.register(ExplanationUsage)
class ExplanationUsageAdmin(ModelAdmin):
    """Yechim izohlarini ochish hisobi (Pro-Basic kunlik limiti uchun)."""

    list_display = ("date", "user", "session")
    list_filter = ("date",)
    search_fields = ("user__email",)
    autocomplete_fields = ("user", "session")
    ordering = ("-date", "-id")
    readonly_fields = ("user", "session", "date")

    def has_add_permission(self, request):
        return False


@admin.register(MockExam)
class MockExamAdmin(ModelAdmin):
    """DTM blok imtihoni — bir nechta fan, bitta umumiy taymer."""

    list_display = (
        "id", "user", "subject_count", "time_limit_seconds",
        "expires_at", "finished_at", "auto_finished",
    )
    list_filter = ("auto_finished", "finished_at")
    search_fields = ("user__email", "user__full_name")
    autocomplete_fields = ("user",)
    ordering = ("-created_at",)
    readonly_fields = ("created_at", "updated_at")

    def get_queryset(self, request):
        return super().get_queryset(request).prefetch_related("sessions")

    @admin.display(description="Fanlar")
    def subject_count(self, obj):
        return obj.sessions.count()
