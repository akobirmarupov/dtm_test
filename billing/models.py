import uuid

from django.db import models

from common.models import BaseModel


class Plan(BaseModel):
    """Tarif rejasi: masalan 0 so'm (Bepul), 50 000 so'm, 70 000 so'm.

    Tariflar bir-biridan NARXI bilan taqqoslanadi: aktiv obunasi bor
    foydalanuvchi faqat qimmatroq tarifga o'ta oladi (upgrade), bir xil yoki
    arzonroq tarifni esa muddat tugagunicha qayta ololmaydi.
    """

    name = models.CharField('Nomi (UZ)', max_length=100)
    name_ru = models.CharField('Nomi (RU)', max_length=100, blank=True)
    name_en = models.CharField('Nomi (EN)', max_length=100, blank=True)

    description = models.TextField('Tavsif (UZ)', blank=True)
    description_ru = models.TextField('Tavsif (RU)', blank=True)
    description_en = models.TextField('Tavsif (EN)', blank=True)

    price = models.DecimalField('Narxi', max_digits=12, decimal_places=2)
    duration_days = models.PositiveIntegerField('Muddati (kun)')
    is_active = models.BooleanField('Faol', default=True)

    class Meta:
        ordering = ['price', 'id']

    def __str__(self):
        return self.name

    @property
    def is_free(self) -> bool:
        """Bepul tarif admin tasdig'isiz darhol faollashadi."""
        return self.price is not None and self.price <= 0


class Subscription(BaseModel):
    class Status(models.TextChoices):
        PENDING = 'pending', 'Kutilmoqda'
        ACTIVE = 'active', 'Faol'
        EXPIRED = 'expired', "Muddati o'tgan"
        CANCELLED = 'cancelled', 'Bekor qilingan'

    user = models.ForeignKey('account.User', on_delete=models.CASCADE, related_name='subscriptions')
    plan = models.ForeignKey(Plan, on_delete=models.PROTECT, related_name='subscriptions')
    status = models.CharField('Holati', max_length=15, choices=Status.choices, default=Status.PENDING)
    starts_at = models.DateTimeField('Boshlangan vaqti')
    expires_at = models.DateTimeField('Tugash vaqti')

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'status', 'expires_at']),
        ]

    def __str__(self):
        return f'{self.user} - {self.plan}'

    @property
    def is_currently_active(self) -> bool:
        from django.utils import timezone
        return self.status == self.Status.ACTIVE and self.expires_at > timezone.now()

    @property
    def days_left(self) -> int:
        from django.utils import timezone
        if self.status != self.Status.ACTIVE:
            return 0
        remaining = self.expires_at - timezone.now()
        return max(remaining.days, 0)


class Payment(BaseModel):
    """Obuna uchun ARIZA.

    Hozircha to'lov shlyuzi yo'q: foydalanuvchi tarifni tanlab ariza
    yuboradi, admin bilan Telegram orqali bog'lanadi, admin to'lovni qabul
    qilgach arizani tasdiqlaydi va obuna faollashadi.
    """

    class Provider(models.TextChoices):
        PAYME = 'payme', 'Payme'
        CLICK = 'click', 'Click'
        MANUAL = 'manual', "Qo'lda (Telegram orqali)"

    class Status(models.TextChoices):
        PENDING = 'pending', 'Kutilmoqda'
        SUCCESS = 'success', 'Muvaffaqiyatli'
        FAILED = 'failed', 'Rad etilgan'
        CANCELLED = 'cancelled', 'Bekor qilingan'

    user = models.ForeignKey('account.User', on_delete=models.CASCADE, related_name='payments')
    plan = models.ForeignKey(
        Plan, on_delete=models.PROTECT, related_name='payments', null=True, blank=True
    )
    subscription = models.ForeignKey(
        Subscription, on_delete=models.SET_NULL, null=True, blank=True, related_name='payments')
    provider = models.CharField('Provayder', max_length=10, choices=Provider.choices)
    provider_transaction_id = models.CharField('Provayder tranzaksiya ID', max_length=100, unique=True)
    amount = models.DecimalField('Summa', max_digits=12, decimal_places=2)
    status = models.CharField('Holati', max_length=15, choices=Status.choices, default=Status.PENDING)

    # Ariza bilan birga adminga yuboriladigan ma'lumotlar.
    contact_phone = models.CharField('Aloqa telefoni', max_length=20, blank=True)
    contact_telegram = models.CharField('Telegram username', max_length=64, blank=True)
    note = models.TextField('Foydalanuvchi izohi', blank=True)

    rejection_reason = models.CharField('Rad etish sababi', max_length=255, blank=True)
    reviewed_by = models.ForeignKey(
        'account.User', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='reviewed_payments', verbose_name="Ko'rib chiqqan admin",
    )
    reviewed_at = models.DateTimeField("Ko'rib chiqilgan vaqti", null=True, blank=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'status']),
            models.Index(fields=['status', '-created_at']),
        ]

    def __str__(self):
        return f'{self.provider} - {self.provider_transaction_id}'

    @staticmethod
    def new_transaction_id(user_id) -> str:
        """Takrorlanmas ariza raqami. Vaqt tamg'asi yetarli emas — bir
        soniyada ikkita ariza tushsa `unique` buziladi."""
        return f'ariza-{user_id}-{uuid.uuid4().hex[:12]}'
