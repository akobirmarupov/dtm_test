from django.db import models
from django.utils import timezone

from common.models import BaseModel


class ReviewCard(BaseModel):
    user = models.ForeignKey('account.User', on_delete=models.CASCADE, related_name='review_cards')
    question = models.ForeignKey('catalog.Question', on_delete=models.CASCADE, related_name='review_cards')
    stability_days = models.FloatField('Eslab qolish kuchi', default=1.0)
    next_review_date = models.DateField('Keyingi takrorlash sanasi', default=timezone.now)

    def __str__(self):
        return f'{self.user} - {self.question_id}'


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
