import django_filters as filters
from progress.models import ReviewCard, Streak, XPTransaction


class ReviewCardFilter(filters.FilterSet):
    user = filters.NumberFilter(field_name="user_id")
    question = filters.NumberFilter(field_name="question_id")
    stability_days_min = filters.NumberFilter(field_name="stability_days", lookup_expr="gte")
    stability_days_max = filters.NumberFilter(field_name="stability_days", lookup_expr="lte")
    next_review_date = filters.DateFilter(field_name="next_review_date")
    next_review_date_after = filters.DateFilter(field_name="next_review_date", lookup_expr="gte")
    next_review_date_before = filters.DateFilter(field_name="next_review_date", lookup_expr="lte")

    class Meta:
        model = ReviewCard
        fields = ["user", "question", "stability_days_min", "stability_days_max", 
                  "next_review_date", "next_review_date_after", "next_review_date_before"]


class StreakFilter(filters.FilterSet):
    user = filters.NumberFilter(field_name="user_id")
    current_streak_min = filters.NumberFilter(field_name="current_streak", lookup_expr="gte")
    current_streak_max = filters.NumberFilter(field_name="current_streak", lookup_expr="lte")
    longest_streak_min = filters.NumberFilter(field_name="longest_streak", lookup_expr="gte")
    longest_streak_max = filters.NumberFilter(field_name="longest_streak", lookup_expr="lte")
    last_activity_date = filters.DateFilter(field_name="last_activity_date")
    last_activity_date_after = filters.DateFilter(field_name="last_activity_date", lookup_expr="gte")
    last_activity_date_before = filters.DateFilter(field_name="last_activity_date", lookup_expr="lte")

    class Meta:
        model = Streak
        fields = ["user", "current_streak_min", "current_streak_max", "longest_streak_min", 
                  "longest_streak_max", "last_activity_date", "last_activity_date_after", 
                  "last_activity_date_before"]


class XPTransactionFilter(filters.FilterSet):
    user = filters.NumberFilter(field_name="user_id")
    source = filters.ChoiceFilter(field_name="source", choices=XPTransaction.Source.choices)
    amount_min = filters.NumberFilter(field_name="amount", lookup_expr="gte")
    amount_max = filters.NumberFilter(field_name="amount", lookup_expr="lte")
    created_at = filters.DateFilter(field_name="created_at")
    created_at_after = filters.DateFilter(field_name="created_at", lookup_expr="gte")
    created_at_before = filters.DateFilter(field_name="created_at", lookup_expr="lte")

    class Meta:
        model = XPTransaction
        fields = ["user", "source", "amount_min", "amount_max", "created_at", 
                  "created_at_after", "created_at_before"]
