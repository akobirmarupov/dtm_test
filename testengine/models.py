from django.db import models

from common.models import BaseModel


class TestSession(BaseModel):
    class Mode(models.TextChoices):
        PRACTICE = 'practice', "O'rganish"
        EXAM = 'exam', 'Imtihon'

    user = models.ForeignKey('account.User', on_delete=models.CASCADE, related_name='test_sessions')
    subject = models.ForeignKey('catalog.Subject', on_delete=models.CASCADE, related_name='test_sessions')
    mode = models.CharField('Rejim', max_length=10, choices=Mode.choices, default=Mode.PRACTICE)
    started_at = models.DateTimeField('Boshlangan vaqti', auto_now_add=True)
    finished_at = models.DateTimeField('Tugagan vaqti', null=True, blank=True)

    def __str__(self):
        return f'{self.user} - {self.subject}'


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

    def __str__(self):
        return f'{self.session} - {self.question_id}'


class TestResult(BaseModel):
    session = models.OneToOneField(TestSession, on_delete=models.CASCADE, related_name='result')
    total_score = models.PositiveIntegerField('Umumiy ball', default=0)
    correct_count = models.PositiveIntegerField("To'g'ri javoblar soni", default=0)
    incorrect_count = models.PositiveIntegerField("Noto'g'ri javoblar soni", default=0)
    duration_seconds = models.PositiveIntegerField('Davomiyligi (soniya)', default=0)

    def __str__(self):
        return f'{self.session} natijasi'
