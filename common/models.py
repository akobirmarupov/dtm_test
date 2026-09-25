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


class Feedback(BaseModel):
    class Type(models.TextChoices):
        FEEDBACK = 'feedback', 'Fikr / Taklif'
        BUG = 'bug', 'Muammo / Xatolik'
        FEATURE = 'feature', 'Yangi imkoniyat'

    user = models.ForeignKey(
        'account.User', on_delete=models.CASCADE, null=True, blank=True, related_name='feedbacks'
    )
    type = models.CharField('Turi', max_length=20, choices=Type.choices, default=Type.FEEDBACK)
    rating = models.PositiveSmallIntegerField('Baho (1-5)', default=5)
    title = models.CharField('Mavzu / Bo\'lim', max_length=255, blank=True)
    message = models.TextField('Xabar / Izoh')

    class Meta:
        verbose_name = 'Fikr va taklif'
        verbose_name_plural = 'Fikr va takliflar'
        ordering = ['-created_at']

    def __str__(self):
        user_str = str(self.user) if self.user else 'Anonim'
        return f"{user_str} ({self.rating}/5): {self.title or self.message[:30]}"

