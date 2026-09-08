from django.db import models
from django.utils import timezone

from common.models import BaseModel


class ReviewCard(BaseModel):
    user = models.ForeignKey('account.User', on_delete=models.CASCADE, related_name='review_cards')
    question = models.ForeignKey('catalog.Question', on_delete=models.CASCADE, related_name='review_cards')
    ease_factor = models.FloatField('Yengillik koeffitsiyenti', default=2.5)
    interval_days = models.PositiveIntegerField('Interval (kun)', default=0)
    repetitions = models.PositiveIntegerField('Ketma-ket to\'g\'ri javoblar', default=0)
    lapses = models.PositiveIntegerField('Unutishlar soni', default=0)
    last_reviewed_at = models.DateTimeField('Oxirgi takrorlash', null=True, blank=True)
    stability_days = models.FloatField('Eslab qolish kuchi', default=1.0)
    next_review_date = models.DateField('Keyingi takrorlash sanasi', default=timezone.now)

    class Meta:
        ordering = ['next_review_date', 'id']
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'question'], name='uniq_review_card_per_question'
            ),
        ]
        indexes = [
            models.Index(fields=['user', 'next_review_date']),
        ]

    def __str__(self):
        return f'{self.user} - {self.question_id}'

    @property
    def is_due(self) -> bool:
        return self.next_review_date <= timezone.localdate()


class Streak(BaseModel):
    user = models.OneToOneField('account.User', on_delete=models.CASCADE, related_name='streak')
    current_streak = models.PositiveIntegerField('Joriy ketma-ketlik', default=0)
    longest_streak = models.PositiveIntegerField('Eng uzun ketma-ketlik', default=0)
    last_activity_date = models.DateField('Oxirgi faollik sanasi', null=True, blank=True)
    freezes_available = models.PositiveIntegerField("Mavjud 'muz'lar soni", default=1)

    def __str__(self):
        return f'{self.user} - {self.current_streak}'


class XPTransaction(BaseModel):
    class Source(models.TextChoices):
        TEST = 'test', 'Test yakunlandi'
        STREAK = 'streak', 'Streak'
        REVIEW = 'review', 'Takrorlash'
        BONUS = 'bonus', 'Bonus'

    user = models.ForeignKey('account.User', on_delete=models.CASCADE, related_name='xp_transactions')
    amount = models.IntegerField('XP miqdori')
    source = models.CharField('Manba', max_length=10, choices=Source.choices)
    description = models.CharField('Izoh', max_length=255, blank=True)

    def __str__(self):
        return f'{self.user} - {self.amount} XP'


class Achievement(BaseModel):
    class Metric(models.TextChoices):
        QUESTIONS_ANSWERED = 'questions', 'Javob berilgan savollar'
        CORRECT_ANSWERS = 'correct', "To'g'ri javoblar"
        TESTS_COMPLETED = 'tests', 'Yakunlangan testlar'
        CURRENT_STREAK = 'streak', 'Ketma-ket kunlar'
        TOTAL_XP = 'xp', 'Umumiy XP'
        SUBJECT_STARS = 'subject_stars', 'Fan darajasi (⭐ x10)'
        PERFECT_TESTS = 'perfect', 'Xatosiz testlar'

    code = models.SlugField('Kod', max_length=64, unique=True)
    name = models.CharField('Nomi (UZ)', max_length=100)
    name_ru = models.CharField('Nomi (RU)', max_length=100, blank=True)
    name_en = models.CharField('Nomi (EN)', max_length=100, blank=True)
    description = models.CharField('Tavsif (UZ)', max_length=255, blank=True)
    description_ru = models.CharField('Tavsif (RU)', max_length=255, blank=True)
    description_en = models.CharField('Tavsif (EN)', max_length=255, blank=True)
    icon = models.CharField('Ikonka', max_length=32, blank=True, help_text='Emoji yoki ikonka kodi')
    metric = models.CharField('O\'lchov', max_length=20, choices=Metric.choices)
    threshold = models.PositiveIntegerField('Chegara qiymati')
    xp_reward = models.PositiveIntegerField('XP mukofoti', default=0)
    order = models.PositiveSmallIntegerField('Tartib', default=0)
    is_active = models.BooleanField('Faol', default=True)

    class Meta:
        ordering = ['metric', 'threshold', 'order']
        verbose_name = 'Yutuq'
        verbose_name_plural = 'Yutuqlar'

    def __str__(self):
        return f'{self.name} ({self.get_metric_display()} >= {self.threshold})'


class UserAchievement(BaseModel):
    user = models.ForeignKey(
        'account.User', on_delete=models.CASCADE, related_name='achievements'
    )
    achievement = models.ForeignKey(
        Achievement, on_delete=models.CASCADE, related_name='unlocked_by'
    )
    value_at_unlock = models.PositiveIntegerField('Qiymat', default=0)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Foydalanuvchi yutug\'i'
        verbose_name_plural = 'Foydalanuvchi yutuqlari'
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'achievement'], name='uniq_user_achievement'
            ),
        ]
        indexes = [
            models.Index(fields=['user', '-created_at']),
        ]

    def __str__(self):
        return f'{self.user_id} - {self.achievement.code}'
