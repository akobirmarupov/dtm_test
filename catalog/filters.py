import django_filters as filters
from django.db.models import Q

from catalog.models import Grade, Question, Subject, Topic


def _multilang(queryset, value, *fields):
    condition = Q()
    for field in fields:
        condition |= Q(**{f'{field}__icontains': value})
    return queryset.filter(condition)


class SubjectFilter(filters.FilterSet):
    name = filters.CharFilter(method='filter_name')

    class Meta:
        model = Subject
        fields = ["name"]

    def filter_name(self, queryset, name, value):
        return _multilang(queryset, value, 'name', 'name_ru', 'name_en')


class GradeFilter(filters.FilterSet):
    subject = filters.NumberFilter(field_name="subject_id")
    name = filters.CharFilter(method='filter_name')
    is_active = filters.BooleanFilter(field_name="is_active")

    class Meta:
        model = Grade
        fields = ["subject", "name", "is_active"]

    def filter_name(self, queryset, name, value):
        return _multilang(queryset, value, 'name', 'name_ru', 'name_en')


class TopicFilter(filters.FilterSet):
    subject = filters.NumberFilter(field_name="subject_id")
    grade = filters.NumberFilter(field_name="grade_id")
    name = filters.CharFilter(method='filter_name')
    is_active = filters.BooleanFilter(field_name="is_active")
    has_test = filters.BooleanFilter(method='filter_has_test')

    class Meta:
        model = Topic
        fields = ["subject", "grade", "name", "is_active", "has_test"]

    def filter_name(self, queryset, name, value):
        return _multilang(queryset, value, 'name', 'name_ru', 'name_en')

    def filter_has_test(self, queryset, name, value):
        from testengine.models import MIN_TIER
        if value:
            return queryset.filter(available_question_count__gte=MIN_TIER)
        return queryset.filter(available_question_count__lt=MIN_TIER)


class QuestionFilter(filters.FilterSet):
    topic = filters.NumberFilter(field_name="topic_id")
    grade = filters.NumberFilter(field_name="topic__grade_id")
    subject = filters.NumberFilter(field_name="topic__subject_id")
    difficulty = filters.NumberFilter(field_name="difficulty")
    difficulty_min = filters.NumberFilter(field_name="difficulty", lookup_expr="gte")
    difficulty_max = filters.NumberFilter(field_name="difficulty", lookup_expr="lte")
    text = filters.CharFilter(method='filter_text')
    has_image = filters.BooleanFilter(method='filter_has_image')
    status = filters.ChoiceFilter(choices=Question.Status.choices)
    is_active = filters.BooleanFilter(field_name="is_active")
    source = filters.CharFilter(field_name="source", lookup_expr="icontains")
    source_year = filters.NumberFilter(field_name="source_year")
    has_explanation = filters.BooleanFilter(method='filter_has_explanation')

    class Meta:
        model = Question
        fields = [
            "topic", "grade", "subject", "difficulty", "difficulty_min",
            "difficulty_max", "text", "has_image", "status", "is_active",
            "source", "source_year", "has_explanation",
        ]

    def filter_text(self, queryset, name, value):
        return _multilang(queryset, value, 'text', 'text_ru', 'text_en')

    def filter_has_image(self, queryset, name, value):
        if value:
            return queryset.exclude(image='').exclude(image__isnull=True)
        return queryset.filter(Q(image='') | Q(image__isnull=True))

    def filter_has_explanation(self, queryset, name, value):
        has = Q(explanation__gt='') | (
            ~Q(explanation_image='') & Q(explanation_image__isnull=False)
        )
        return queryset.filter(has) if value else queryset.exclude(has)
