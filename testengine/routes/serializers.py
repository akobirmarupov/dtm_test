from rest_framework import serializers

from testengine.models import (
    MAX_QUESTION_COUNT,
    MIN_QUESTION_COUNT,
    Answer,
    TestResult,
    TestSession,
)
from account.models import User
from catalog.models import Question, Subject, Topic
from catalog.routes.serializers import absolute_image_url, translated_options
from common.i18n import LanguageContextMixin, translated


class SubjectMinimalSerializer(LanguageContextMixin, serializers.ModelSerializer):
    name = serializers.SerializerMethodField()

    class Meta:
        model = Subject
        fields = ["id", "name"]
        read_only_fields = fields

    def get_name(self, obj) -> str:
        return translated(obj, 'name', self.language)


class UserMinimalSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "email", "full_name", "avatar_url"]


class QuestionForTestSerializer(LanguageContextMixin, serializers.ModelSerializer):
    """Test paytida ko'rsatiladigan savol.

    * `correct_option` BU YERDA YO'Q — aks holda mijoz javobni oldindan bilib
      oladi.
    * Matn va variantlar so'rov tilida (uz/ru/en) qaytadi.
    * `image` — savolga rasm biriktirilgan bo'lsa uning to'liq manzili,
      bo'lmasa `null`.
    """

    text = serializers.SerializerMethodField()
    options = serializers.SerializerMethodField()
    topic_name = serializers.SerializerMethodField()
    image = serializers.SerializerMethodField()
    has_image = serializers.SerializerMethodField()

    class Meta:
        model = Question
        fields = [
            "id", "topic_id", "topic_name", "text", "options",
            "image", "image_caption", "has_image", "difficulty",
        ]
        read_only_fields = fields

    def get_text(self, obj) -> str:
        return translated(obj, 'text', self.language)

    def get_options(self, obj) -> dict:
        return translated_options(obj, self.language)

    def get_topic_name(self, obj) -> str:
        return translated(obj.topic, 'name', self.language)

    def get_image(self, obj) -> str | None:
        return absolute_image_url(obj, self.context.get('request'))

    def get_has_image(self, obj) -> bool:
        return bool(obj.image)


class MyAnswerSerializer(serializers.ModelSerializer):
    """Foydalanuvchining joriy tanlovi — to'g'ri/noto'g'ri ma'lumotisiz."""

    class Meta:
        model = Answer
        fields = ["id", "selected_option", "confidence", "time_spent_seconds", "updated_at"]
        read_only_fields = fields


class SessionQuestionSerializer(serializers.Serializer):
    """Test varaqasining bitta qatori: savol + mening tanlovim.

    `is_correct` yo'q — natija faqat `finish` dan keyin ochiladi.
    """

    order = serializers.IntegerField(read_only=True)
    question = QuestionForTestSerializer(read_only=True)
    my_answer = serializers.SerializerMethodField()
    is_answered = serializers.SerializerMethodField()

    def get_my_answer(self, obj) -> dict | None:
        answer = self._answer(obj)
        return MyAnswerSerializer(answer).data if answer else None

    def get_is_answered(self, obj) -> bool:
        return self._answer(obj) is not None

    def _answer(self, obj):
        answers = self.context.get('answers') or {}
        return answers.get(obj.question_id)


class SessionQuestionReviewSerializer(serializers.Serializer):
    """Yakunlangan sessiya tahlili — to'g'ri javob shu yerda ochiladi."""

    order = serializers.IntegerField(read_only=True)
    question = QuestionForTestSerializer(read_only=True)
    correct_option = serializers.SerializerMethodField()
    selected_option = serializers.SerializerMethodField()
    is_correct = serializers.SerializerMethodField()
    is_answered = serializers.SerializerMethodField()
    time_spent_seconds = serializers.SerializerMethodField()

    def get_correct_option(self, obj) -> str:
        return obj.question.correct_option

    def get_selected_option(self, obj) -> str | None:
        answer = self._answer(obj)
        return answer.selected_option if answer else None

    def get_is_correct(self, obj) -> bool:
        answer = self._answer(obj)
        return bool(answer and answer.is_correct)

    def get_is_answered(self, obj) -> bool:
        return self._answer(obj) is not None

    def get_time_spent_seconds(self, obj) -> int:
        answer = self._answer(obj)
        return answer.time_spent_seconds if answer else 0

    def _answer(self, obj):
        answers = self.context.get('answers') or {}
        return answers.get(obj.question_id)


class SessionProgressSerializer(serializers.Serializer):
    total_questions = serializers.IntegerField(read_only=True)
    answered_count = serializers.IntegerField(read_only=True)
    unanswered_count = serializers.IntegerField(read_only=True)
    unanswered_orders = serializers.ListField(
        child=serializers.IntegerField(), read_only=True
    )
    is_finished = serializers.BooleanField(read_only=True)


class TestSessionSerializer(serializers.ModelSerializer):
    subject = SubjectMinimalSerializer(read_only=True)
    user = UserMinimalSerializer(read_only=True)
    mode_display = serializers.CharField(source='get_mode_display', read_only=True)
    is_finished = serializers.BooleanField(read_only=True)
    duration_seconds = serializers.SerializerMethodField()

    class Meta:
        model = TestSession
        fields = [
            "id", "user", "subject", "mode", "mode_display", "question_count",
            "started_at", "finished_at", "is_finished", "duration_seconds",
            "created_at", "updated_at",
        ]
        read_only_fields = fields

    def get_duration_seconds(self, obj) -> int | None:
        if obj.finished_at and obj.started_at:
            return int((obj.finished_at - obj.started_at).total_seconds())
        return None


class TestSessionCreateSerializer(serializers.Serializer):
    """Yangi sessiya so'rovi: qaysi fan, qaysi rejim, nechta savol."""

    subject = serializers.PrimaryKeyRelatedField(queryset=Subject.objects.all())
    mode = serializers.ChoiceField(
        choices=TestSession.Mode.choices, default=TestSession.Mode.PRACTICE
    )
    question_count = serializers.IntegerField(
        required=False, min_value=MIN_QUESTION_COUNT, max_value=MAX_QUESTION_COUNT
    )
    topics = serializers.PrimaryKeyRelatedField(
        queryset=Topic.objects.all(), many=True, required=False
    )

    def validate(self, attrs):
        subject = attrs.get('subject')
        topics = attrs.get('topics') or []
        foreign = [topic.id for topic in topics if topic.subject_id != subject.id]
        if foreign:
            raise serializers.ValidationError(
                {"topics": f"Mavzular tanlangan fanga tegishli emas: {foreign}"}
            )
        return attrs


class TestSessionUpdateSerializer(serializers.ModelSerializer):
    """Yakunlanmagan sessiyada faqat rejimni almashtirish mumkin."""

    class Meta:
        model = TestSession
        fields = ["mode"]


class TestSessionDetailSerializer(TestSessionSerializer):
    total_questions = serializers.SerializerMethodField()
    answered_count = serializers.SerializerMethodField()
    unanswered_count = serializers.SerializerMethodField()

    class Meta(TestSessionSerializer.Meta):
        fields = TestSessionSerializer.Meta.fields + [
            "total_questions", "answered_count", "unanswered_count",
        ]
        read_only_fields = fields

    def _progress(self, obj):
        progress = self.context.get('progress')
        if progress is None:
            from testengine.services import session_progress
            progress = session_progress(obj)
            self.context['progress'] = progress
        return progress

    def get_total_questions(self, obj) -> int:
        return self._progress(obj)['total_questions']

    def get_answered_count(self, obj) -> int:
        return self._progress(obj)['answered_count']

    def get_unanswered_count(self, obj) -> int:
        return self._progress(obj)['unanswered_count']


class AnswerSerializer(LanguageContextMixin, serializers.ModelSerializer):
    """Test DAVOM etayotganda qaytariladigan javob — natijasiz."""

    confidence_display = serializers.CharField(source='get_confidence_display', read_only=True)
    question_text = serializers.SerializerMethodField()
    question_difficulty = serializers.IntegerField(source='question.difficulty', read_only=True)

    def get_question_text(self, obj) -> str:
        return translated(obj.question, 'text', self.language)

    class Meta:
        model = Answer
        fields = [
            "id", "session", "question", "question_text", "question_difficulty",
            "selected_option", "confidence", "confidence_display",
            "time_spent_seconds", "created_at", "updated_at",
        ]
        read_only_fields = fields


class AnswerResultSerializer(AnswerSerializer):
    """Sessiya YAKUNLANGANDAN keyin — to'g'ri javob bilan birga."""

    correct_option = serializers.CharField(source='question.correct_option', read_only=True)

    class Meta(AnswerSerializer.Meta):
        fields = AnswerSerializer.Meta.fields + ["is_correct", "correct_option"]
        read_only_fields = fields


class AnswerCreateSerializer(serializers.Serializer):
    """Javob berish/o'zgartirish so'rovi."""

    question = serializers.PrimaryKeyRelatedField(queryset=Question.objects.all())
    selected_option = serializers.CharField()
    confidence = serializers.ChoiceField(
        choices=Answer.Confidence.choices, required=False, allow_blank=True, default=""
    )
    time_spent_seconds = serializers.IntegerField(required=False, min_value=0, default=0)

    def validate_selected_option(self, value):
        value = str(value).strip().upper()
        if len(value) != 1 or not value.isalpha():
            raise serializers.ValidationError(
                "Tanlangan variant bitta harf bo'lishi kerak (A, B, C, D, E, F)."
            )
        return value

    def validate(self, attrs):
        question = attrs.get('question')
        selected = attrs.get('selected_option')
        options = question.options if isinstance(question.options, dict) else {}
        available = {str(key).strip().upper() for key in options}
        if available and selected not in available:
            raise serializers.ValidationError({
                "selected_option": f"Bu savolda bunday variant yo'q. Mavjud: {sorted(available)}"
            })
        return attrs


class AnswerOptionSerializer(serializers.Serializer):
    """Tartib raqami bo'yicha javob berish — savol id si kerak emas."""

    selected_option = serializers.CharField()
    confidence = serializers.ChoiceField(
        choices=Answer.Confidence.choices, required=False, allow_blank=True, default=""
    )
    time_spent_seconds = serializers.IntegerField(required=False, min_value=0, default=0)

    def validate_selected_option(self, value):
        value = str(value).strip().upper()
        if len(value) != 1 or not value.isalpha():
            raise serializers.ValidationError(
                "Tanlangan variant bitta harf bo'lishi kerak (A, B, C, D, E, F)."
            )
        return value


class TestResultSerializer(serializers.ModelSerializer):
    session_detail = TestSessionSerializer(source='session', read_only=True)
    subject = SubjectMinimalSerializer(source='session.subject', read_only=True)
    user = UserMinimalSerializer(source='session.user', read_only=True)
    mode = serializers.CharField(source='session.mode', read_only=True)
    mode_display = serializers.CharField(source='session.get_mode_display', read_only=True)
    accuracy_percent = serializers.FloatField(read_only=True)
    total_questions = serializers.IntegerField(read_only=True)

    class Meta:
        model = TestResult
        fields = [
            "id", "session", "session_detail", "subject", "user", "mode", "mode_display",
            "total_score", "correct_count", "incorrect_count", "unanswered_count",
            "total_questions", "accuracy_percent", "duration_seconds",
            "created_at", "updated_at",
        ]
        read_only_fields = fields


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
        if len(value) != 1 or not value.isalpha():
            raise serializers.ValidationError(
                "Tanlangan variant bitta harf bo'lishi kerak (A, B, C, D, E, F)."
            )
        return value


class BulkAnswerSerializer(serializers.Serializer):
    """Ko'p javoblarni bir so'rovda saqlash (offline sync yoki 'hammasini
    yuborish')."""

    answers = BulkAnswerItemSerializer(many=True, required=True)

    def validate_answers(self, value):
        if not value:
            raise serializers.ValidationError("Javoblar ro'yxati bo'sh bo'lishi mumkin emas.")

        seen = set()
        for item in value:
            if item['question'] in seen:
                raise serializers.ValidationError(
                    f"{item['question']} ID'li savol ro'yxatda takrorlangan."
                )
            seen.add(item['question'])
        return value


class SessionFinishResponseSerializer(serializers.Serializer):
    """`finish` javobi: natija + to'liq tahlil bitta so'rovda."""

    session = TestSessionDetailSerializer(read_only=True)
    result = TestResultSerializer(read_only=True)
    review = SessionQuestionReviewSerializer(many=True, read_only=True)
