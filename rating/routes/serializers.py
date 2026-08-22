from drf_spectacular.utils import extend_schema_serializer
from rest_framework import serializers

from rating.models import Rating, RatingHistory, TopicRating, SubjectRating


class RatingSerializer(serializers.ModelSerializer):
    """GET /rating/me/ — foydalanuvchining joriy davr reytingi (faqat o'qish)."""
    period_display = serializers.CharField(source='get_period_display', read_only=True)
    accuracy_percentage = serializers.FloatField(read_only=True)

    class Meta:
        model = Rating
        fields = [
            'id', 'period', 'period_display', 'stars', 'rank',
            'tests_completed', 'correct_answers', 'incorrect_answers',
            'accuracy_percentage', 'period_start_date', 'period_end_date', 'last_updated',
        ]
        read_only_fields = fields


class TopicRatingSerializer(serializers.ModelSerializer):
    """GET /rating/topics/ — mavzu bo'yicha reyting, sahifalangan ro'yxat."""
    topic_name = serializers.CharField(source='topic.name', read_only=True)
    subject_name = serializers.CharField(source='topic.subject.name', read_only=True)
    accuracy_percentage = serializers.FloatField(read_only=True)

    class Meta:
        model = TopicRating
        fields = [
            'id', 'topic', 'topic_name', 'subject_name', 'stars',
            'tests_completed', 'correct_answers', 'incorrect_answers',
            'accuracy_percentage', 'last_updated',
        ]
        read_only_fields = fields


class SubjectRatingSerializer(serializers.ModelSerializer):
    """GET /rating/subjects/ — fan bo'yicha reyting, sahifalangan ro'yxat."""
    subject_name = serializers.CharField(source='subject.name', read_only=True)
    accuracy_percentage = serializers.FloatField(read_only=True)

    class Meta:
        model = SubjectRating
        fields = [
            'id', 'subject', 'subject_name', 'stars', 'tests_completed',
            'correct_answers', 'incorrect_answers', 'topics_completed',
            'accuracy_percentage', 'last_updated',
        ]
        read_only_fields = fields


class RatingHistorySerializer(serializers.ModelSerializer):
    """GET /rating/history/ — reyting o'zgarishlari tarixi."""
    period_display = serializers.CharField(source='get_period_display', read_only=True)

    class Meta:
        model = RatingHistory
        fields = [
            'id', 'period', 'period_display', 'previous_stars', 'new_stars',
            'stars_change', 'previous_rank', 'new_rank', 'reason', 'created_at',
        ]
        read_only_fields = fields


@extend_schema_serializer(component_name='RatingLeaderboardEntry')
class LeaderboardEntrySerializer(serializers.Serializer):
    """GET /rating/leaderboard/{period}/ — reyting qatori, Rating'dan olinadi."""
    rank = serializers.IntegerField()
    user_id = serializers.IntegerField()
    full_name = serializers.CharField()
    stars = serializers.FloatField()
    tests_completed = serializers.IntegerField()
    is_current_user = serializers.BooleanField()
