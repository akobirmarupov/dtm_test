from rest_framework import serializers

from testengine.models import TestSession, Answer, TestResult
from catalog.models import Question, Subject
from account.models import User


class SubjectMinimalSerializer(serializers.ModelSerializer):
    class Meta:
        model = Subject
        fields = ["id", "name"]


class UserMinimalSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "email", "full_name", "avatar_url"]


class QuestionForTestSerializer(serializers.ModelSerializer):
    class Meta:
        model = Question
        fields = ["id", "topic_id", "text", "options", "difficulty"]
        read_only_fields = fields


class TestSessionSerializer(serializers.ModelSerializer):
    subject = SubjectMinimalSerializer(read_only=True)
    user = UserMinimalSerializer(read_only=True)
    mode_display = serializers.CharField(source='get_mode_display', read_only=True)
    duration_seconds = serializers.SerializerMethodField()

    class Meta:
        model = TestSession
        fields = [
            "id", "user", "subject", "mode", "mode_display",
            "started_at", "finished_at", "duration_seconds", "created_at", "updated_at"
        ]
        read_only_fields = ["id", "user", "started_at", "finished_at", "created_at", "updated_at"]

    def get_duration_seconds(self, obj):
        if obj.finished_at and obj.started_at:
            return int((obj.finished_at - obj.started_at).total_seconds())
        return None


class TestSessionCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = TestSession
        fields = ["subject", "mode"]

    def validate_subject(self, value):
        if value is None:
            raise serializers.ValidationError("Fan tanlab oling.")
        return value

    def validate_mode(self, value):
        if value not in dict(TestSession.Mode.choices):
            raise serializers.ValidationError("Noto'g'ri rejim tanlab olingiz.")
        return value


class TestSessionDetailSerializer(serializers.ModelSerializer):
    subject = SubjectMinimalSerializer(read_only=True)
    user = UserMinimalSerializer(read_only=True)
    mode_display = serializers.CharField(source='get_mode_display', read_only=True)
    answers_count = serializers.SerializerMethodField()
    correct_answers_count = serializers.SerializerMethodField()
    incorrect_answers_count = serializers.SerializerMethodField()
    is_finished = serializers.SerializerMethodField()
    duration_seconds = serializers.SerializerMethodField()

    class Meta:
        model = TestSession
        fields = [
            "id", "user", "subject", "mode", "mode_display",
            "started_at", "finished_at", "duration_seconds",
            "answers_count", "correct_answers_count", "incorrect_answers_count",
            "is_finished", "created_at", "updated_at"
        ]
        read_only_fields = fields

    def get_answers_count(self, obj):
        return obj.answers.count()

    def get_correct_answers_count(self, obj):
        return obj.answers.filter(is_correct=True).count()

    def get_incorrect_answers_count(self, obj):
        return obj.answers.filter(is_correct=False).count()

    def get_is_finished(self, obj):
        return obj.finished_at is not None

    def get_duration_seconds(self, obj):
        if obj.finished_at and obj.started_at:
            return int((obj.finished_at - obj.started_at).total_seconds())
        return None


class AnswerSerializer(serializers.ModelSerializer):
    confidence_display = serializers.CharField(source='get_confidence_display', read_only=True)
    question_text = serializers.CharField(source='question.text', read_only=True)
    question_difficulty = serializers.IntegerField(source='question.difficulty', read_only=True)

    class Meta:
        model = Answer
        fields = [
            "id", "session", "question", "question_text", "question_difficulty",
            "selected_option", "is_correct", "confidence", "confidence_display",
            "time_spent_seconds", "created_at", "updated_at"
        ]
        read_only_fields = ["id", "session", "created_at", "updated_at", "is_correct"]


class AnswerCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Answer
        fields = ["question", "selected_option", "is_correct", "confidence", "time_spent_seconds"]
        read_only_fields = ["is_correct"]

    def validate_selected_option(self, value):
        value = str(value).strip().upper()
        if not value or len(value) != 1 or not value.isalpha():
            raise serializers.ValidationError("Tanglangan variant bitta harf bo'lishi kerak (A, B, C, D, E, F).")
        return value

    def validate_confidence(self, value):
        if value and value not in dict(Answer.Confidence.choices):
            raise serializers.ValidationError("Noto'g'ri ishonch darajasi.")
        return value

    def validate_time_spent_seconds(self, value):
        if value < 0:
            raise serializers.ValidationError("Sarflangan vaqt manfiy bo'lishi mumkin emas.")
        return value


class TestResultSerializer(serializers.ModelSerializer):
    session_detail = TestSessionSerializer(source='session', read_only=True)
    subject = SubjectMinimalSerializer(source='session.subject', read_only=True)
    user = UserMinimalSerializer(source='session.user', read_only=True)
    mode = serializers.CharField(source='session.mode', read_only=True)
    mode_display = serializers.CharField(source='session.get_mode_display', read_only=True)
    accuracy_percent = serializers.SerializerMethodField()
    total_questions = serializers.SerializerMethodField()

    class Meta:
        model = TestResult
        fields = [
            "id", "session", "session_detail", "subject", "user", "mode", "mode_display",
            "total_score", "correct_count", "incorrect_count", "total_questions",
            "accuracy_percent", "duration_seconds", "created_at", "updated_at"
        ]
        read_only_fields = fields

    def get_accuracy_percent(self, obj):
        total = obj.correct_count + obj.incorrect_count
        if total == 0:
            return 0
        return round((obj.correct_count / total) * 100, 2)

    def get_total_questions(self, obj):
        return obj.correct_count + obj.incorrect_count


class BulkAnswerItemSerializer(serializers.Serializer):
    """Bulk ro'yxatidagi bitta javob elementi. is_correct BU YERDA YO'Q —
    uni backend view o'zi question.correct_option bilan solishtirib hisoblaydi."""
    question = serializers.IntegerField()
    selected_option = serializers.CharField()
    confidence = serializers.ChoiceField(
        choices=Answer.Confidence.choices, required=False, allow_blank=True, default=""
    )
    time_spent_seconds = serializers.IntegerField(required=False, min_value=0, default=0)

    def validate_selected_option(self, value):
        value = str(value).strip().upper()
        if not value or len(value) != 1 or not value.isalpha():
            raise serializers.ValidationError("Tanglangan variant bitta harf bo'lishi kerak (A, B, C, D, E, F).")
        return value


class BulkAnswerSerializer(serializers.Serializer):
    """Ko'p javoblarni saqlash uchun"""
    answers = BulkAnswerItemSerializer(many=True, required=True)

    def validate_answers(self, value):
        if not value:
            raise serializers.ValidationError("Javoblar ro'yxati bo'sh bo'lishi mumkin emas.")
        return value