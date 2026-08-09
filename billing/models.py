from django.db import models

from common.models import BaseModel


class Plan(BaseModel):
    name = models.CharField('Nomi', max_length=100)
    price = models.DecimalField('Narxi', max_digits=12, decimal_places=2)
    duration_days = models.PositiveIntegerField('Muddati (kun)')

    def __str__(self):
        return self.name


class Subscription(BaseModel):
    class Status(models.TextChoices):
        ACTIVE = 'active', 'Faol'
        EXPIRED = 'expired', "Muddati o'tgan"
        CANCELLED = 'cancelled', 'Bekor qilingan'

    user = models.ForeignKey('account.User', on_delete=models.CASCADE, related_name='subscriptions')
    plan = models.ForeignKey(Plan, on_delete=models.CASCADE, related_name='subscriptions')
    status = models.CharField('Holati', max_length=15, choices=Status.choices, default=Status.ACTIVE)
    starts_at = models.DateTimeField('Boshlangan vaqti')
    expires_at = models.DateTimeField('Tugash vaqti')

    def __str__(self):
        return f'{self.user} - {self.plan}'


class Payment(BaseModel):
    class Provider(models.TextChoices):
        PAYME = 'payme', 'Payme'
        CLICK = 'click', 'Click'

    class Status(models.TextChoices):
        PENDING = 'pending', 'Kutilmoqda'
        SUCCESS = 'success', 'Muvaffaqiyatli'
        FAILED = 'failed', 'Muvaffaqiyatsiz'

    user = models.ForeignKey('account.User', on_delete=models.CASCADE, related_name='payments')
    subscription = models.ForeignKey(
        Subscription, on_delete=models.SET_NULL, null=True, blank=True, related_name='payments')
    provider = models.CharField('Provayder', max_length=10, choices=Provider.choices)
    provider_transaction_id = models.CharField('Provayder tranzaksiya ID', max_length=100, unique=True)
    amount = models.DecimalField('Summa', max_digits=12, decimal_places=2)
    status = models.CharField('Holati', max_length=15, choices=Status.choices, default=Status.PENDING)

    def __str__(self):
        return f'{self.provider} - {self.provider_transaction_id}'
