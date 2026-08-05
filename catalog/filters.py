import django_filters as filters

from catalog.models import Question, Subject, Topic


class SubjectFilter(filters.FilterSet):
    name = filters.CharFilter(field_name="name", lookup_expr="icontains")

    class Meta:
        model = Subject
        fields = ["name"]


class TopicFilter(filters.FilterSet):
    subject = filters.NumberFilter(field_name="subject_id")
    name = filters.CharFilter(field_name="name", lookup_expr="icontains")

    class Meta:
        model = Topic
        fields = ["subject", "name"]


class QuestionFilter(filters.FilterSet):
    topic = filters.NumberFilter(field_name="topic_id")
    subject = filters.NumberFilter(field_name="topic__subject_id")
    difficulty = filters.NumberFilter(field_name="difficulty")
    difficulty_min = filters.NumberFilter(field_name="difficulty", lookup_expr="gte")
    difficulty_max = filters.NumberFilter(field_name="difficulty", lookup_expr="lte")
    text = filters.CharFilter(field_name="text", lookup_expr="icontains")

    class Meta:
        model = Question
        fields = ["topic", "subject", "difficulty", "difficulty_min", "difficulty_max", "text"]
