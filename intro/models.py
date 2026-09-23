"""Kirish testi — ilovaga birinchi marta kirgan odam uchun.

Nega alohida ilova: bu savollar DTM savollari EMAS. Ular mantiqiy va
psixologik — odamni qiziqtirish uchun. Agar ular `catalog.Question` ichida
tursa, mavzudagi savol sanog'iga, reytingga va statistikaga qo'shilib ketadi.

Bazada nechta savol bo'lishidan qat'i nazar (30 ta ham, 500 ta ham) har
kirganda tasodifiy 4 tasi chiqadi.
"""

from django.core.validators import FileExtensionValidator
from django.db import models

from common.models import BaseModel

# Bir kirishda ko'rsatiladigan savollar soni.
INTRO_QUESTION_COUNT = 4

# Video hajmi chegarasi (bayt). Katta fayl serverni ham, mobil internetni ham
# qiynaydi — YouTube havolasi (`video_url`) afzal.
MAX_VIDEO_SIZE = 50 * 1024 * 1024


class IntroQuestion(BaseModel):
    class Kind(models.TextChoices):
        LOGIC = 'logic', 'Mantiqiy'
        PSYCHOLOGY = 'psychology', 'Psixologik'

    kind = models.CharField(
        'Turi', max_length=12, choices=Kind.choices, default=Kind.LOGIC,
        help_text="Psixologik savolda to'g'ri javob bo'lmaydi.",
    )

    text = models.TextField('Savol matni (UZ)')
    text_ru = models.TextField('Savol matni (RU)', blank=True)
    text_en = models.TextField('Savol matni (EN)', blank=True)

    options = models.JSONField(
        'Variantlar (UZ)',
        help_text='Masalan: {"A": "Birinchi", "B": "Ikkinchi", "C": "Uchinchi"}',
    )
    options_ru = models.JSONField('Variantlar (RU)', null=True, blank=True)
    options_en = models.JSONField('Variantlar (EN)', null=True, blank=True)

    correct_option = models.CharField(
        "To'g'ri javob", max_length=1, blank=True,
        help_text="Mantiqiy savol uchun majburiy, psixologik uchun bo'sh qoldiriladi.",
    )

    image = models.ImageField(
        'Rasm (ixtiyoriy)', upload_to='intro/images/%Y/%m/', null=True, blank=True
    )
    video = models.FileField(
        'Video (ixtiyoriy)', upload_to='intro/videos/%Y/%m/', null=True, blank=True,
        validators=[FileExtensionValidator(['mp4', 'webm', 'mov', 'm4v'])],
        help_text="50 MB gacha. Doimiy saqlash uchun tashqi xotira kerak — "
                  "server diski redeploy'da tozalanadi.",
    )
    video_url = models.URLField(
        'Video havolasi (ixtiyoriy)', blank=True,
        help_text="YouTube yoki boshqa havola. Fayl yuklashdan ko'ra yengilroq.",
    )

    explanation = models.TextField(
        'Javobdan keyingi izoh (UZ)', blank=True,
        help_text="Test yakunida ko'rsatiladi.",
    )
    explanation_ru = models.TextField('Javobdan keyingi izoh (RU)', blank=True)
    explanation_en = models.TextField('Javobdan keyingi izoh (EN)', blank=True)

    order = models.PositiveSmallIntegerField('Tartib', default=0)
    is_active = models.BooleanField('Faol', default=True)

    class Meta:
        verbose_name = 'Kirish testi savoli'
        verbose_name_plural = 'Kirish testi savollari'
        ordering = ['order', 'id']
        indexes = [
            models.Index(fields=['is_active', 'kind']),
        ]

    def __str__(self):
        return self.text[:60]

    @property
    def has_correct_answer(self) -> bool:
        return bool(self.correct_option)
