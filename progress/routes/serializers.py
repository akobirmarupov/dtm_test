from drf_spectacular.utils import extend_schema_serializer
from rest_framework import serializers

from progress.models import ReviewCard, Streak, XPTransaction



class ReviewCardSerializer(serializers.ModelSerializer):
    """GET /reviews/today/ va /reviews/ uchun — ro'yxatda ko'rsatish."""
    question_text = serializers.CharField(source='question.text', read_only=True)
    subject_name = serializers.CharField(source='question.topic.subject.name', read_only=True)
    topic_name = serializers.CharField(source='question.topic.name', read_only=True)

    class Meta:
        model = ReviewCard
        fields = [
            'id', 'question', 'question_text', 'subject_name', 'topic_name',
            'stability_days', 'next_review_date',
        ]
        read_only_fields = fields


class ReviewCardSubmitSerializer(serializers.Serializer):
    """POST /reviews/{id}/submit/ uchun kirish — javob to'g'ri/notog'riligi va sarflangan vaqt."""
    is_correct = serializers.BooleanField()
    response_time = serializers.IntegerField(min_value=0, help_text='soniyalarda')



class StreakSerializer(serializers.ModelSerializer):
    """GET /streak/ — foydalanuvchining joriy streak holati (faqat o'qish)."""

    class Meta:
        model = Streak
        fields = [
            'current_streak', 'longest_streak',
            'last_activity_date', 'freezes_available',
        ]
        read_only_fields = fields




class XPTransactionSerializer(serializers.ModelSerializer):
    """GET /xp/transactions/ — XP tarixi, sahifalangan ro'yxat."""
    source_display = serializers.CharField(source='get_source_display', read_only=True)

    class Meta:
        model = XPTransaction
        fields = [
            'id', 'amount', 'source', 'source_display',
            'description', 'created_at',
        ]
        read_only_fields = fields


class XPSummarySerializer(serializers.Serializer):
    """GET /xp/summary/ — agregatsiya qilingan qiymatlar, model'ga bog'liq emas."""
    xp_total = serializers.IntegerField()
    xp_today = serializers.IntegerField()
    xp_this_week = serializers.IntegerField()


@extend_schema_serializer(component_name='XPLeaderboardEntry')
class LeaderboardEntrySerializer(serializers.Serializer):
    """GET /leaderboard/weekly/ — reyting qatori, XPTransaction'lardan agregatsiya qilinadi."""
    rank = serializers.IntegerField()
    nickname = serializers.CharField()
    xp_this_week = serializers.IntegerField()
    is_current_user = serializers.BooleanField()