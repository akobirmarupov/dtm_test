from django.db import models

from common.models import BaseModel

# Sessiya ochilganda nechta savol biriktiriladi (mijoz boshqacha so'ramasa).
DEFAULT_QUESTION_COUNT = 15
MIN_QUESTION_COUNT = 1
MAX_QUESTION_COUNT = 100


class TestSession(BaseModel):
    class Mode(models.TextChoices):
        PRACTICE = 'practice', "O'rganish"
        EXAM = 'exam', 'Imtihon'

    user = models.ForeignKey('account.User', on_delete=models.CASCADE, related_name='test_sessions')
    subject = models.ForeignKey('catalog.Subject', on_delete=models.CASCADE, related_name='test_sessions')
    mode = models.CharField('Rejim', max_length=10, choices=Mode.choices, default=Mode.PRACTICE)
    question_count = models.PositiveSmallIntegerField(
        'Savollar soni', default=DEFAULT_QUESTION_COUNT
    )
    started_at = models.DateTimeField('Boshlangan vaqti', auto_now_add=True)
    finished_at = models.DateTimeField('Tugagan vaqti', null=True, blank=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', '-created_at']),
        ]

    def __str__(self):
        return f'{self.user} - {self.subject}'

    @property
    def is_finished(self) -> bool:
        """Sessiya yakunlanganmi. Yakunlangandan keyin javoblar o'zgarmaydi
        va faqat shundan keyin to'g'ri/noto'g'ri ma'lumoti ochiladi."""
        return self.finished_at is not None


class SessionQuestion(BaseModel):
    """Sessiya ochilganda savollar ro'yxati SHU YERDA qotiriladi.

    Shu tufayli foydalanuvchi 10-savoldan 3-savolga qaytib, javobini
    o'zgartira oladi: savollar tartibi butun sessiya davomida o'zgarmaydi.
    """

    session = models.ForeignKey(
        TestSession, on_delete=models.CASCADE, related_name='session_questions'
    )
    question = models.ForeignKey(
        'catalog.Question', on_delete=models.CASCADE, related_name='session_questions'
    )
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
        # Bitta sessiyada bitta savolga faqat bitta javob bo'ladi. Javobni
        # o'zgartirish = shu yozuvni yangilash. Constraint bo'lmasa parallel
        # so'rovlar dublikat yaratib, keyin `update_or_create` ni buzadi.
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
