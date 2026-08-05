from django.db import models

from common.models import BaseModel


class Subject(BaseModel):
    name = models.CharField('Nomi', max_length=100)

    def __str__(self):
        return self.name


class Topic(BaseModel):
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name='topics')
    name = models.CharField('Nomi', max_length=150)

    def __str__(self):
        return self.name


class Question(BaseModel):
    class Difficulty(models.IntegerChoices):
        VERY_EASY = 1, 'Juda oson'
        EASY = 2, 'Oson'
        MEDIUM = 3, "O'rtacha"
        HARD = 4, 'Qiyin'
        VERY_HARD = 5, 'Juda qiyin'

    topic = models.ForeignKey(Topic, on_delete=models.CASCADE, related_name='questions')
    text = models.TextField('Savol matni')
    options = models.JSONField('Variantlar')
    correct_option = models.CharField("To'g'ri javob", max_length=1)
    difficulty = models.PositiveSmallIntegerField(
        'Qiyinlik darajasi', choices=Difficulty.choices, default=Difficulty.MEDIUM
    )

    def __str__(self):
        return self.text[:50]
