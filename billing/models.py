import uuid

from django.db import models
from common.models import BaseModel


class Plan(BaseModel):
    name = models.CharField('Nomi (UZ)', max_length=100)
    name_ru = models.CharField('Nomi (RU)', max_length=100, blank=True)
    name_en = models.CharField('Nomi (EN)', max_length=100, blank=True)
    description = models.TextField('Tavsif (UZ)', blank=True)
    description_ru = models.TextField('Tavsif (RU)', blank=True)
    description_en = models.TextField('Tavsif (EN)', blank=True)
    price = models.DecimalField('Narxi', max_digits=12, decimal_places=2)
    duration_days = models.PositiveIntegerField('Muddati (kun)')
    is_active = models.BooleanField('Faol', default=True)
    code = models.SlugField('Tizim kodi', max_length=32, blank=True,
        help_text="Kodda murojaat qilish uchun barqaror kalit: free, pro_basic, pro_full.",)
    is_pro = models.BooleanField('Pullik tarif', default=False,
        help_text="Faqat belgi: tarif pullik ekanini bildiradi. Cheklovlar "
                  "quyidagi maydonlardan olinadi, bu ptichkadan emas.",)
    daily_topic_limit = models.PositiveSmallIntegerField('Kunlik mavzu limiti', null=True, blank=True,
        help_text="Bir kunda nechta TURLI mavzuda test ishlash mumkin. ""Bo'sh qoldirilsa — cheklovsiz.",)
    max_question_count = models.PositiveSmallIntegerField('Bir testdagi maksimal savol', default=60,)
    can_choose_question_count = models.BooleanField("Savol sonini o'zi tanlaydi", default=True,
        help_text="O'chirilsa test har doim eng kichik to'plam bilan boshlanadi.",)
    can_use_exam_mode = models.BooleanField('Imtihon rejimi (vaqt chegarasi bilan)', default=True,
        help_text="O'chirilsa faqat «O'rganish» rejimi ochiq bo'ladi.",)
    can_view_explanations = models.BooleanField('Yechim izohlarini ko\'radi', default=False,)
    explanation_limit_per_day = models.PositiveSmallIntegerField('Kunlik izoh limiti', null=True, blank=True,
        help_text="Kuniga nechta testning izohini ochish mumkin. ""Bo'sh qoldirilsa — cheklovsiz.",)
    mistake_test_daily_limit = models.PositiveSmallIntegerField('Xatolardan test tuzish (kuniga)',
        null=True, blank=True,
        help_text="Bo'sh — cheksiz, 0 — faqat xatolar ro'yxatini ko'radi.",)
    review_cards_daily_limit = models.PositiveSmallIntegerField('Takrorlash kartalari (kuniga)',
        null=True, blank=True,
        help_text="Bo'sh — cheksiz, 0 — takrorlash yopiq.",)
    can_view_analytics = models.BooleanField('Zaif mavzular va batafsil tahlil', default=True,
        help_text="O'chirilsa faqat umumiy ball va daraja ko'rinadi.",)
    history_days = models.PositiveSmallIntegerField('Natijalar tarixi (kun)', null=True, blank=True,
        help_text="Necha kunlik natija ko'rinadi. Bo'sh qoldirilsa — butun tarix.",)
    streak_freezes_per_month = models.PositiveSmallIntegerField('Streak muzlatish (oyiga)',
        null=True, blank=True, default=1,
        help_text="Bo'sh — cheksiz, 0 — muzlatish yo'q.",)
    features = models.JSONField("Qo'shimcha imkoniyatlar", default=dict, blank=True,
        help_text="Kelajakdagi flaglar uchun erkin JSON. Masalan: "'{"ai_tutor": true, "mock_exam": false}',)

    class Meta:
        ordering = ['price', 'id']
        constraints = [
            models.UniqueConstraint(
                fields=['code'], condition=models.Q(code__gt=''), name='uniq_plan_code'
            ),
        ]

    def __str__(self):
        return self.name

    @property
    def is_free(self) -> bool:
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
