from django.db import models
from django.utils import timezone



class BaseModel(models.Model):
    created_at = models.DateTimeField('Yaratilgan sana', auto_now_add=True)
    updated_at = models.DateTimeField('Yangilangan sana', auto_now=True)

    class Meta:
        abstract = True



class Role(models.TextChoices):
    STUDENT = "student", "Talaba"
    MENTOR = "mentor", "Mentor"
    ADMIN = "admin", "Administrator"
    SUPPORT = "support", "Qo'llab-quvvatlash"
 

class DailyFeatureUsage(BaseModel):
    """Kunlik hisoblagich — tarif limitlari shunga tayanadi.

    Nega umumiy model: «kuniga nechta» degan cheklov bir nechta bo'limda
    kerak bo'ladi (xatolar banki, takrorlash kartalari, streak muzi). Har biri
    uchun alohida jadval yasash o'rniga bitta hisoblagich yetadi.

    Mavzu limiti (`testengine.DailyTopicUsage`) va izoh limiti
    (`testengine.ExplanationUsage`) bu yerga KO'CHIRILMADI — ular oddiy sanoq
    emas, «qaysi mavzu» va «qaysi sessiya» ekanini ham eslab qoladi.
    """

    class Feature(models.TextChoices):
        MISTAKE_TEST = 'mistake_test', 'Xatolardan test tuzish'
        REVIEW_CARD = 'review_card', 'Takrorlash kartasi'
        STREAK_FREEZE = 'streak_freeze', 'Streak muzlatish'

    user = models.ForeignKey(
        'account.User', on_delete=models.CASCADE, related_name='daily_feature_usages'
    )
    feature = models.CharField('Imkoniyat', max_length=32, choices=Feature.choices)
    date = models.DateField('Sana (UZT)', default=timezone.localdate)
    count = models.PositiveIntegerField('Nechta marta', default=0)

    class Meta:
        verbose_name = 'Kunlik foydalanish'
        verbose_name_plural = 'Kunlik foydalanishlar'
        ordering = ['-date', 'feature']
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'feature', 'date'], name='uniq_daily_feature_usage'
            ),
        ]
        indexes = [
            models.Index(fields=['user', 'feature', 'date']),
        ]

    def __str__(self):
        return f'{self.user} - {self.get_feature_display()} ({self.date}): {self.count}'
