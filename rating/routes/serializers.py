from drf_spectacular.utils import extend_schema_serializer
from rest_framework import serializers

from rating.models import Rating, RatingHistory, TopicRating, SubjectRating


class RatingSerializer(serializers.ModelSerializer):
    period_display = serializers.CharField(source='get_period_display', read_only=True)
    accuracy_percentage = serializers.FloatField(read_only=True)
    completion_percentage = serializers.FloatField(read_only=True)

    class Meta:
        model = Rating
        fields = [
            'id', 'period', 'period_display', 'stars', 'xp', 'rank',
            'tests_completed', 'correct_answers', 'incorrect_answers',
            'unanswered_answers', 'accuracy_percentage', 'completion_percentage',
            'period_start_date', 'period_end_date', 'last_updated',
        ]
        read_only_fields = fields


class TopicRatingSerializer(serializers.ModelSerializer):
    topic_name = serializers.CharField(source='topic.name', read_only=True)
    subject_name = serializers.CharField(source='topic.subject.name', read_only=True)
    accuracy_percentage = serializers.FloatField(read_only=True)
    needs_practice = serializers.BooleanField(read_only=True)

    class Meta:
        model = TopicRating
        fields = [
            'id', 'topic', 'topic_name', 'subject_name', 'stars',
            'tests_completed', 'correct_answers', 'incorrect_answers',
            'unanswered_answers', 'accuracy_percentage', 'needs_practice',
            'last_updated',
        ]
        read_only_fields = fields


class SubjectRatingSerializer(serializers.ModelSerializer):
    subject_name = serializers.CharField(source='subject.name', read_only=True)
    accuracy_percentage = serializers.FloatField(read_only=True)

    class Meta:
        model = SubjectRating
        fields = [
            'id', 'subject', 'subject_name', 'stars', 'tests_completed',
            'correct_answers', 'incorrect_answers', 'unanswered_answers',
            'topics_completed', 'accuracy_percentage', 'last_updated',
        ]
        read_only_fields = fields


class RatingHistorySerializer(serializers.ModelSerializer):
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
    rank = serializers.IntegerField()
    user_id = serializers.IntegerField()
    full_name = serializers.CharField()
    avatar_url = serializers.CharField(allow_null=True, required=False)
    xp = serializers.IntegerField()
    stars = serializers.FloatField()
    tests_completed = serializers.IntegerField()
    is_current_user = serializers.BooleanField()


@extend_schema_serializer(component_name='LeagueStanding')
class LeagueStandingSerializer(serializers.Serializer):
    rank = serializers.IntegerField()
    user_id = serializers.IntegerField()
    full_name = serializers.CharField()
    avatar_url = serializers.CharField(allow_null=True)
    xp = serializers.IntegerField()
    zone = serializers.ChoiceField(choices=['promotion', 'safe', 'demotion'])
    is_current_user = serializers.BooleanField()


@extend_schema_serializer(component_name='WeakTopic')
class WeakTopicSerializer(serializers.ModelSerializer):
    topic_name = serializers.CharField(source='topic.name', read_only=True)
    subject_id = serializers.IntegerField(source='topic.subject_id', read_only=True)
    subject_name = serializers.CharField(source='topic.subject.name', read_only=True)
    grade_id = serializers.IntegerField(source='topic.grade_id', read_only=True)
    grade_name = serializers.CharField(source='topic.grade.name', read_only=True, default=None)
    accuracy_percentage = serializers.FloatField(read_only=True)
    answered_count = serializers.SerializerMethodField()
    can_start_test = serializers.SerializerMethodField()

    class Meta:
        model = TopicRating
        fields = [
            'topic', 'topic_name', 'subject_id', 'subject_name',
            'grade_id', 'grade_name', 'stars', 'accuracy_percentage',
            'correct_answers', 'incorrect_answers', 'answered_count',
            'can_start_test', 'last_updated',
        ]
        read_only_fields = fields

    def get_answered_count(self, obj) -> int:
        return obj.correct_answers + obj.incorrect_answers

    def get_can_start_test(self, obj) -> bool:
        """Shu mavzuda test ochish mumkinmi — tavsiya tugmasi faol bo'lsinmi."""
        from testengine.models import MIN_TIER
        return obj.topic.available_question_count >= MIN_TIER
