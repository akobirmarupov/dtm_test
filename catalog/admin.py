from django.contrib import admin
from django.utils.html import format_html

from unfold.admin import ModelAdmin, TabularInline

from .models import Grade, Question, Subject, Topic


class GradeInline(TabularInline):
    model = Grade
    extra = 0
    fields = ("name", "name_ru", "name_en", "order", "is_active")
    ordering = ("order", "id")
    show_change_link = True


class TopicInline(TabularInline):
    model = Topic
    fk_name = "grade"
    extra = 0
    fields = ("name", "name_ru", "name_en", "order", "is_active", "available_question_count")
    readonly_fields = ("available_question_count",)
    ordering = ("order", "name")
    show_change_link = True


@admin.register(Subject)
class SubjectAdmin(ModelAdmin):
    list_display = ("name", "name_ru", "name_en", "grade_count", "created_at")
    search_fields = ("name", "name_ru", "name_en")
    ordering = ("name",)
    inlines = (GradeInline,)
    fieldsets = (
        ("O'zbekcha", {"fields": ("name",)}),
        ("Tarjimalar", {"fields": ("name_ru", "name_en")}),
    )

    @admin.display(description="Sinf/kitoblar")
    def grade_count(self, obj):
        return obj.grades.count()


@admin.register(Grade)
class GradeAdmin(ModelAdmin):
    """Sinf yoki kitob. Nom erkin: «7-sinf» ham, «Milliy sertifikat uchun» ham."""

    list_display = ("name", "subject", "order", "is_active", "topic_count", "created_at")
    list_filter = ("subject", "is_active")
    search_fields = ("name", "name_ru", "name_en", "subject__name")
    autocomplete_fields = ("subject",)
    ordering = ("subject", "order", "id")
    list_editable = ("order", "is_active")
    inlines = (TopicInline,)
    fieldsets = (
        ("Asosiy", {"fields": ("subject", "name", "order", "is_active")}),
        ("Tarjimalar", {"fields": ("name_ru", "name_en")}),
    )

    @admin.display(description="Mavzular")
    def topic_count(self, obj):
        return obj.topics.count()


@admin.register(Topic)
class TopicAdmin(ModelAdmin):
    list_display = (
        "name", "grade", "subject", "order", "is_active",
        "available_question_count", "test_ready", "created_at",
    )
    list_filter = ("grade__subject", "grade", "is_active")
    search_fields = ("name", "name_ru", "name_en", "grade__name", "subject__name")
    autocomplete_fields = ("grade",)
    ordering = ("subject", "order", "name")
    list_editable = ("order", "is_active")
    # `subject` avtomatik to'ldiriladi (`grade.subject`), `available_question_count`
    # esa signal orqali — ikkalasi ham qo'lda tahrirlanmaydi.
    readonly_fields = ("subject", "available_question_count")
    fieldsets = (
        ("Asosiy", {"fields": ("grade", "subject", "name", "order", "is_active")}),
        ("Tarjimalar", {"fields": ("name_ru", "name_en")}),
        ("Statistika", {"fields": ("available_question_count",)}),
    )

    @admin.display(description="Test tayyor", boolean=True)
    def test_ready(self, obj):
        from testengine.models import MIN_TIER
        return obj.available_question_count >= MIN_TIER


@admin.register(Question)
class QuestionAdmin(ModelAdmin):
    list_display = (
        "id", "short_text", "topic", "status", "is_active", "difficulty",
        "observed", "correct_option", "has_explanation", "image_preview",
        "created_at",
    )
    list_filter = (
        "status", "is_active", "difficulty", "topic__subject",
        "topic__grade", "source_year",
    )
    search_fields = ("text", "text_ru", "text_en", "topic__name", "source")
    autocomplete_fields = ("topic", "author", "reviewed_by")
    ordering = ("-created_at",)
    list_editable = ("status", "is_active")
    readonly_fields = (
        "image_preview", "explanation_preview", "times_answered",
        "times_correct", "stats_summary",
    )
    actions = ("publish_questions", "archive_questions")

    fieldsets = (
        ("Asosiy", {"fields": ("topic", "difficulty", "correct_option")}),
        ("Holati", {
            "fields": ("status", "is_active", "author", "reviewed_by"),
            "description": "Faqat «Chop etilgan» va «Faol» savollar testga tushadi. "
                           "Xato savolni o'chirmasdan «Faol» ni olib tashlash "
                           "yetarli — javoblar tarixi buzilmaydi.",
        }),
        ("O'zbekcha", {"fields": ("text", "options")}),
        ("Ruscha (ixtiyoriy)", {"fields": ("text_ru", "options_ru")}),
        ("Inglizcha (ixtiyoriy)", {"fields": ("text_en", "options_en")}),
        ("Yechim izohi", {
            "fields": (
                "explanation", "explanation_ru", "explanation_en",
                "explanation_image", "explanation_preview", "hint",
            ),
            "description": "Foydalanuvchi NEGA xato qilganini bilmasa, test "
                           "o'rganish vositasi emas. Izoh Pro tarifda ochiladi.",
        }),
        ("Rasm (ixtiyoriy)", {"fields": ("image", "image_caption", "image_preview")}),
        ("Manba", {"fields": ("source", "source_year")}),
        ("Statistika", {
            "fields": ("times_answered", "times_correct", "stats_summary"),
            "description": "Qo'lda qo'yilgan qiyinlik taxminiy. Haqiqiy qiyinlik "
                           "shu yerda — foydalanuvchilar javoblaridan hisoblanadi.",
        }),
    )

    @admin.display(description="Savol matni")
    def short_text(self, obj):
        return obj.text[:60]

    @admin.display(description="Izoh", boolean=True)
    def has_explanation(self, obj):
        return bool(obj.explanation or obj.explanation_image)

    @admin.display(description="Haqiqiy qiyinlik")
    def observed(self, obj):
        level = obj.observed_difficulty
        if level is None:
            return "—"
        mismatch = abs(level - obj.difficulty) >= 2
        return format_html(
            '<span style="color:{}">{}</span>',
            '#e74c3c' if mismatch else 'inherit',
            level,
        )

    @admin.display(description="Tafsilot")
    def stats_summary(self, obj):
        if not obj.times_answered:
            return "Hali javob berilmagan."
        p_value = obj.p_value
        return format_html(
            "{} marta javob berilgan, {} tasi to'g'ri. "
            "To'g'ri javob ulushi: {}. O'rtacha vaqt: {} s.",
            obj.times_answered,
            obj.times_correct,
            f"{p_value:.0%}" if p_value is not None else "yetarli ma'lumot yo'q",
            obj.avg_time_seconds or 0,
        )

    @admin.display(description="Rasm")
    def image_preview(self, obj):
        if not obj.image:
            return "—"
        return format_html(
            '<img src="{}" style="max-height:120px;border-radius:8px" />', obj.image.url
        )

    @admin.display(description="Yechim rasmi")
    def explanation_preview(self, obj):
        if not obj.explanation_image:
            return "—"
        return format_html(
            '<img src="{}" style="max-height:120px;border-radius:8px" />',
            obj.explanation_image.url,
        )

    @admin.action(description="Tanlanganlarni chop etish")
    def publish_questions(self, request, queryset):
        updated = 0
        for question in queryset:
            question.status = Question.Status.PUBLISHED
            question.is_active = True
            question.reviewed_by = request.user
            # `save()` — signal ishlab, mavzudagi sanoq yangilanishi uchun
            # (`queryset.update()` signal chaqirmaydi).
            question.save(update_fields=['status', 'is_active', 'reviewed_by', 'updated_at'])
            updated += 1
        self.message_user(request, f"{updated} ta savol chop etildi.")

    @admin.action(description="Tanlanganlarni arxivlash")
    def archive_questions(self, request, queryset):
        updated = 0
        for question in queryset:
            question.status = Question.Status.ARCHIVED
            question.save(update_fields=['status', 'updated_at'])
            updated += 1
        self.message_user(request, f"{updated} ta savol arxivlandi.")
