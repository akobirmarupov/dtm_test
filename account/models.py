from django.contrib.auth.base_user import AbstractBaseUser
from django.contrib.auth.models import PermissionsMixin
from django.db import models

from common.i18n import DEFAULT_LANGUAGE, SUPPORTED_LANGUAGES
from common.models import Role, BaseModel
from account.manager import UserManager


class Language(models.TextChoices):
    UZ = 'uz', "O'zbekcha"
    RU = 'ru', 'Ruscha'
    EN = 'en', 'Inglizcha'


class User(AbstractBaseUser, PermissionsMixin, BaseModel):
    email = models.EmailField(unique=True)
    google_id = models.CharField(max_length=100, unique=True, null=True, blank=True)
    # Apple "Sign in with Apple" beradigan barqaror foydalanuvchi identifikatori.
    apple_id = models.CharField(max_length=100, unique=True, null=True, blank=True)
    full_name = models.CharField(max_length=150, blank=True)
    avatar_url = models.URLField(blank=True)
    role = models.CharField(max_length=10, choices=Role.choices, default=Role.STUDENT)
    # Bo'sh qoldirilsa "foydalanuvchi tilni tanlamagan" degani bo'ladi va til
    # `Accept-Language` header'idan olinadi (`common.i18n.resolve_language`).
    language = models.CharField(
        'Interfeys tili', max_length=5, choices=Language.choices,
        default=DEFAULT_LANGUAGE, blank=True,
    )
    phone_number = models.CharField('Telefon raqami', max_length=20, blank=True)
    telegram_username = models.CharField('Telegram username', max_length=64, blank=True)
    region = models.CharField(max_length=100, blank=True)
    target_major = models.CharField(max_length=150, blank=True)
    xp_total = models.PositiveIntegerField(default=0)
    consent_share_with_universities = models.BooleanField(default=False)
    consent_updated_at = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    objects = UserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    def save(self, *args, **kwargs):
        # Bo'sh satr `unique` ni buzadi (ikkinchi bo'sh satr konflikt beradi),
        # NULL esa bermaydi — shuning uchun bo'shni NULL ga aylantiramiz.
        if self.google_id == "":
            self.google_id = None
        if self.apple_id == "":
            self.apple_id = None
        if self.language and self.language not in SUPPORTED_LANGUAGES:
            self.language = DEFAULT_LANGUAGE
        super().save(*args, **kwargs)

    def __str__(self):
        return self.email


class Device(BaseModel):
    """Foydalanuvchi kirgan qurilma.

    iPhone, Android smartfon, planshet, brauzer — hammasi shu yerda qayd
    etiladi. Push token saqlanadi, shuning uchun bildirishnomalarni aynan
    kerakli qurilmaga yuborish mumkin. Bir qurilma bir foydalanuvchida bir
    marta bo'ladi (`device_id` bo'yicha).
    """

    class Platform(models.TextChoices):
        IOS = 'ios', 'iOS (iPhone / iPad)'
        ANDROID = 'android', 'Android'
        WEB = 'web', 'Brauzer'
        DESKTOP = 'desktop', 'Desktop'
        OTHER = 'other', 'Boshqa'

    user = models.ForeignKey(
        'account.User', on_delete=models.CASCADE, related_name='devices'
    )
    device_id = models.CharField('Qurilma identifikatori', max_length=128)
    platform = models.CharField(
        'Platforma', max_length=10, choices=Platform.choices, default=Platform.OTHER
    )
    push_token = models.CharField('Push token', max_length=512, blank=True)
    model_name = models.CharField('Model', max_length=100, blank=True)
    os_version = models.CharField('OS versiyasi', max_length=50, blank=True)
    app_version = models.CharField('Ilova versiyasi', max_length=50, blank=True)
    language = models.CharField(
        'Til', max_length=5, choices=Language.choices, default=DEFAULT_LANGUAGE
    )
    is_active = models.BooleanField('Faol', default=True)
    last_seen_at = models.DateTimeField('Oxirgi faollik', auto_now=True)

    class Meta:
        ordering = ['-last_seen_at']
        verbose_name = 'Qurilma'
        verbose_name_plural = 'Qurilmalar'
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'device_id'], name='uniq_user_device'
            ),
        ]
        indexes = [
            models.Index(fields=['user', 'is_active']),
        ]

    def __str__(self):
        return f'{self.user} - {self.get_platform_display()} ({self.model_name or self.device_id})'
