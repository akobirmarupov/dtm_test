import django_filters as filters

from testengine.models import Answer, TestResult, TestSession


class TestSessionFilter(filters.FilterSet):
    user = filters.NumberFilter(field_name="user_id")
    subject = filters.NumberFilter(field_name="subject_id")
    mode = filters.ChoiceFilter(field_name="mode", choices=TestSession.Mode.choices)
    started_at_after = filters.DateTimeFilter(field_name="started_at", lookup_expr="gte")
    started_at_before = filters.DateTimeFilter(field_name="started_at", lookup_expr="lte")
    finished_at_after = filters.DateTimeFilter(field_name="finished_at", lookup_expr="gte")
    finished_at_before = filters.DateTimeFilter(field_name="finished_at", lookup_expr="lte")
    is_finished = filters.BooleanFilter(field_name="finished_at", method="filter_is_finished")

    def filter_is_finished(self, queryset, name, value):
        if value:
            return queryset.filter(finished_at__isnull=False)
        else:
            return queryset.filter(finished_at__isnull=True)

    class Meta:
        model = TestSession
        fields = ["user", "subject", "mode", "started_at_after", "started_at_before", "finished_at_after", "finished_at_before", "is_finished"]


class AnswerFilter(filters.FilterSet):
    session = filters.NumberFilter(field_name="session_id")
    question = filters.NumberFilter(field_name="question_id")
    is_correct = filters.BooleanFilter(field_name="is_correct")
    confidence = filters.ChoiceFilter(field_name="confidence", choices=Answer.Confidence.choices)
    time_spent_min = filters.NumberFilter(field_name="time_spent_seconds", lookup_expr="gte")
    time_spent_max = filters.NumberFilter(field_name="time_spent_seconds", lookup_expr="lte")

    class Meta:
        model = Answer
        fields = ["session", "question", "is_correct", "confidence", "time_spent_min", "time_spent_max"]


class TestResultFilter(filters.FilterSet):
    session = filters.NumberFilter(field_name="session_id")
    total_score_min = filters.NumberFilter(field_name="total_score", lookup_expr="gte")
    total_score_max = filters.NumberFilter(field_name="total_score", lookup_expr="lte")
    correct_count_min = filters.NumberFilter(field_name="correct_count", lookup_expr="gte")
    correct_count_max = filters.NumberFilter(field_name="correct_count", lookup_expr="lte")
    incorrect_count_min = filters.NumberFilter(field_name="incorrect_count", lookup_expr="gte")
    incorrect_count_max = filters.NumberFilter(field_name="incorrect_count", lookup_expr="lte")
    duration_min = filters.NumberFilter(field_name="duration_seconds", lookup_expr="gte")
    duration_max = filters.NumberFilter(field_name="duration_seconds", lookup_expr="lte")

    class Meta:
        model = TestResult
        fields = ["session", "total_score_min", "total_score_max", "correct_count_min", "correct_count_max", "incorrect_count_min", "incorrect_count_max", "duration_min", "duration_max"]
