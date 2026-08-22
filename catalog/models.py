from django.db import models

from common.models import BaseModel


class Subject(BaseModel):
    name = models.CharField('Nomi (UZ)', max_length=100)
    name_ru = models.CharField('Nomi (RU)', max_length=100, blank=True)
    name_en = models.CharField('Nomi (EN)', max_length=100, blank=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


class Topic(BaseModel):
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name='topics')
    name = models.CharField('Nomi (UZ)', max_length=150)
    name_ru = models.CharField('Nomi (RU)', max_length=150, blank=True)
    name_en = models.CharField('Nomi (EN)', max_length=150, blank=True)

    class Meta:
        ordering = ['name']

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

    text = models.TextField('Savol matni (UZ)')
    text_ru = models.TextField('Savol matni (RU)', blank=True)
    text_en = models.TextField('Savol matni (EN)', blank=True)

    options = models.JSONField('Variantlar (UZ)')
    options_ru = models.JSONField('Variantlar (RU)', null=True, blank=True)
    options_en = models.JSONField('Variantlar (EN)', null=True, blank=True)

    # Rasm IXTIYORIY: grafik/diagramma kerak bo'lgan savollar uchun. Bo'sh
    # qoldirilsa savol oddiy matnli savol bo'lib qolaveradi.
    image = models.ImageField(
        'Rasm (ixtiyoriy)', upload_to='questions/%Y/%m/', null=True, blank=True
    )
    image_caption = models.CharField('Rasm izohi', max_length=255, blank=True)

    correct_option = models.CharField("To'g'ri javob", max_length=1)
    difficulty = models.PositiveSmallIntegerField(
        'Qiyinlik darajasi', choices=Difficulty.choices, default=Difficulty.MEDIUM
    )

    class Meta:
        ordering = ['topic_id', 'id']
        indexes = [
            models.Index(fields=['topic', 'difficulty']),
        ]

    def __str__(self):
        return self.text[:50]
