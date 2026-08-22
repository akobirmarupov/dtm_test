import django_filters as filters
from django.db.models import Q

from catalog.models import Question, Subject, Topic


class SubjectFilter(filters.FilterSet):
    # Qidiruv uchala tilda ham ishlashi kerak: ruscha interfeysdagi
    # foydalanuvchi "Математика" deb yozganda ham fan topilsin.
    name = filters.CharFilter(method='filter_name')

    class Meta:
        model = Subject
        fields = ["name"]

    def filter_name(self, queryset, name, value):
        return queryset.filter(
            Q(name__icontains=value)
            | Q(name_ru__icontains=value)
            | Q(name_en__icontains=value)
        )


class TopicFilter(filters.FilterSet):
    subject = filters.NumberFilter(field_name="subject_id")
    name = filters.CharFilter(method='filter_name')

    class Meta:
        model = Topic
        fields = ["subject", "name"]

    def filter_name(self, queryset, name, value):
        return queryset.filter(
            Q(name__icontains=value)
            | Q(name_ru__icontains=value)
            | Q(name_en__icontains=value)
        )


class QuestionFilter(filters.FilterSet):
    topic = filters.NumberFilter(field_name="topic_id")
    subject = filters.NumberFilter(field_name="topic__subject_id")
    difficulty = filters.NumberFilter(field_name="difficulty")
    difficulty_min = filters.NumberFilter(field_name="difficulty", lookup_expr="gte")
    difficulty_max = filters.NumberFilter(field_name="difficulty", lookup_expr="lte")
    text = filters.CharFilter(method='filter_text')
    has_image = filters.BooleanFilter(method='filter_has_image')

    class Meta:
        model = Question
        fields = [
            "topic", "subject", "difficulty", "difficulty_min",
            "difficulty_max", "text", "has_image",
        ]

    def filter_text(self, queryset, name, value):
        return queryset.filter(
            Q(text__icontains=value)
            | Q(text_ru__icontains=value)
            | Q(text_en__icontains=value)
        )

    def filter_has_image(self, queryset, name, value):
        if value:
            return queryset.exclude(image='').exclude(image__isnull=True)
        return queryset.filter(Q(image='') | Q(image__isnull=True))
