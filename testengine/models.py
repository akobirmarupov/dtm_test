from django.db import models
from django.utils import timezone

from common.models import BaseModel

DEFAULT_QUESTION_COUNT = 15
MIN_QUESTION_COUNT = 1
MAX_QUESTION_COUNT = 100


QUESTION_COUNT_TIERS = (20, 25, 30, 35, 40, 45, 50, 55, 60)
MIN_TIER = QUESTION_COUNT_TIERS[0]
MAX_TIER = QUESTION_COUNT_TIERS[-1]


EXAM_SECONDS_PER_QUESTION = 90
PRACTICE_MAX_SECONDS_PER_QUESTION = 600

# DTM blok imtihoni: bir nechta fan ketma-ket, bitta umumiy taymer.
MOCK_EXAM_MIN_SUBJECTS = 2
MOCK_EXAM_MAX_SUBJECTS = 5
MOCK_EXAM_DEFAULT_QUESTION_COUNT = 30


class MockExam(BaseModel):
    """DTM blok imtihoni: bir nechta fan ketma-ket, bitta umumiy muddat.

    Har bir fan uchun alohida `TestSession` ochiladi — javob berish, sinxron
    qilish, natija hisoblash hammasi mavjud kod bilan ishlaydi. `MockExam`
    ularni bitta imtihonga bog'lab turadi va umumiy taymerni ushlaydi.
    """

    user = models.ForeignKey(
        'account.User', on_delete=models.CASCADE, related_name='mock_exams'
    )
    time_limit_seconds = models.PositiveIntegerField('Umumiy vaqt (soniya)')
    expires_at = models.DateTimeField('Tugash muddati')
    finished_at = models.DateTimeField('Yakunlangan vaqti', null=True, blank=True)
    auto_finished = models.BooleanField('Avtomatik yakunlangan', default=False)

    class Meta:
        verbose_name = 'Blok imtihoni'
        verbose_name_plural = 'Blok imtihonlari'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['expires_at'], condition=models.Q(finished_at__isnull=True),
                         name='idx_mock_exam_open_expiry'),
        ]

    def __str__(self):
        return f'{self.user} - blok imtihoni #{self.pk}'

    @property
    def is_finished(self) -> bool:
        return self.finished_at is not None

    @property
    def is_expired(self) -> bool:
        if self.finished_at is not None:
            return False
        return timezone.now() >= self.expires_at

    @property
    def seconds_left(self) -> int:
        if self.finished_at is not None:
            return 0
        return max(int((self.expires_at - timezone.now()).total_seconds()), 0)


class TestSession(BaseModel):
    class Mode(models.TextChoices):
        PRACTICE = 'practice', "O'rganish"
        EXAM = 'exam', 'Imtihon'

    user = models.ForeignKey('account.User', on_delete=models.CASCADE, related_name='test_sessions')
    subject = models.ForeignKey('catalog.Subject', on_delete=models.CASCADE, related_name='test_sessions')
    topic = models.ForeignKey('catalog.Topic', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='test_sessions', verbose_name='Mavzu',)
    grade = models.ForeignKey('catalog.Grade', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='test_sessions', verbose_name='Sinf / Kitob',)
    mode = models.CharField('Rejim', max_length=10, choices=Mode.choices, default=Mode.PRACTICE)
    question_count = models.PositiveSmallIntegerField('Savollar soni', default=DEFAULT_QUESTION_COUNT )
    started_at = models.DateTimeField('Boshlangan vaqti', auto_now_add=True)
    finished_at = models.DateTimeField('Tugagan vaqti', null=True, blank=True)
    time_limit_seconds = models.PositiveIntegerField('Vaqt chegarasi (soniya)', null=True, blank=True)
    expires_at = models.DateTimeField('Tugash muddati', null=True, blank=True)
    auto_finished = models.BooleanField('Avtomatik yakunlangan', default=False)
    mock_exam = models.ForeignKey(
        MockExam, on_delete=models.CASCADE, related_name='sessions',
        null=True, blank=True, verbose_name='Blok imtihoni',
    )
    exam_order = models.PositiveSmallIntegerField(
        'Imtihondagi tartibi', default=0,
        help_text='Blok imtihonida fanlar shu tartibda chiqadi.',
    )

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['expires_at'], condition=models.Q(finished_at__isnull=True),
                         name='idx_session_open_expiry'),
            models.Index(fields=['mock_exam', 'exam_order']),
        ]

    def __str__(self):
        return f'{self.user} - {self.subject}'

    @property
    def is_finished(self) -> bool:
        return self.finished_at is not None

    @property
    def is_expired(self) -> bool:
        if self.finished_at is not None or self.expires_at is None:
            return False
        return timezone.now() >= self.expires_at

    @property
    def seconds_left(self) -> int | None:
        if self.expires_at is None:
            return None
        if self.finished_at is not None:
            return 0
        return max(int((self.expires_at - timezone.now()).total_seconds()), 0)


class SessionQuestion(BaseModel):
    session = models.ForeignKey(TestSession, on_delete=models.CASCADE, related_name='session_questions')
    question = models.ForeignKey('catalog.Question', on_delete=models.CASCADE, related_name='session_questions')
    order = models.PositiveSmallIntegerField('Tartib raqami')

    class Meta:
        ordering = ['order']
        verbose_name = 'Sessiya savoli'
        verbose_name_plural = 'Sessiya savollari'
        constraints = [
            models.UniqueConstraint(
                fields=['session', 'order'], name='uniq_session_question_order'
            ),
            models.UniqueConstraint(
                fields=['session', 'question'], name='uniq_session_question'
            ),
        ]

    def __str__(self):
        return f'{self.session_id} #{self.order}'


class Answer(BaseModel):
    class Confidence(models.TextChoices):
        SURE = 'sure', 'Ishonchli'
        GUESS = 'guess', 'Taxmin'

    session = models.ForeignKey(TestSession, on_delete=models.CASCADE, related_name='answers')
    question = models.ForeignKey('catalog.Question', on_delete=models.CASCADE, related_name='answers')
    selected_option = models.CharField('Tanlangan javob', max_length=1)
    is_correct = models.BooleanField("To'g'ri/noto'g'ri")
    confidence = models.CharField('Ishonch darajasi', max_length=10, choices=Confidence.choices, blank=True)
    time_spent_seconds = models.PositiveIntegerField('Sarflangan vaqt (soniya)', default=0)

    class Meta:
        ordering = ['id']
        constraints = [
            models.UniqueConstraint(
                fields=['session', 'question'], name='uniq_answer_per_session_question'
            ),
        ]
        indexes = [
            models.Index(fields=['session']),
        ]

    def __str__(self):
        return f'{self.session} - {self.question_id}'


class TestResult(BaseModel):
    session = models.OneToOneField(TestSession, on_delete=models.CASCADE, related_name='result')
    total_score = models.PositiveIntegerField('Umumiy ball', default=0)
    correct_count = models.PositiveIntegerField("To'g'ri javoblar soni", default=0)
    incorrect_count = models.PositiveIntegerField("Noto'g'ri javoblar soni", default=0)
    unanswered_count = models.PositiveIntegerField('Javobsiz savollar soni', default=0)
    duration_seconds = models.PositiveIntegerField('Davomiyligi (soniya)', default=0)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.session} natijasi'

    @property
    def total_questions(self) -> int:
        return self.correct_count + self.incorrect_count + self.unanswered_count

    @property
    def accuracy_percent(self) -> float:
        total = self.total_questions
        if not total:
            return 0.0
        return round((self.correct_count / total) * 100, 2)


class DailyTopicUsage(BaseModel):
    user = models.ForeignKey('account.User', on_delete=models.CASCADE, related_name='daily_topic_usages')
    topic = models.ForeignKey('catalog.Topic', on_delete=models.CASCADE, related_name='daily_usages')
    date = models.DateField('Sana (UZT)', default=timezone.localdate)
    sessions_started = models.PositiveSmallIntegerField('Ochilgan testlar', default=1)

    class Meta:
        ordering = ['-date', '-id']
        verbose_name = 'Kunlik mavzu hisobi'
        verbose_name_plural = 'Kunlik mavzu hisoblari'
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'topic', 'date'], name='uniq_daily_topic_usage'
            ),
        ]
        indexes = [
            models.Index(fields=['user', 'date']),
        ]

    def __str__(self):
        return f'{self.user_id} - {self.topic_id} ({self.date})'


class ExplanationUsage(BaseModel):
    user = models.ForeignKey('account.User', on_delete=models.CASCADE, related_name='explanation_usages')
    session = models.ForeignKey(TestSession, on_delete=models.CASCADE, related_name='explanation_usages')
    date = models.DateField('Sana (UZT)', default=timezone.localdate)

    class Meta:
        ordering = ['-date', '-id']
        verbose_name = 'Izoh ochilishi'
        verbose_name_plural = 'Izoh ochilishlari'
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'session', 'date'], name='uniq_explanation_usage'
            ),
        ]
        indexes = [
            models.Index(fields=['user', 'date']),
        ]

    def __str__(self):
        return f'{self.user_id} - session {self.session_id} ({self.date})'
