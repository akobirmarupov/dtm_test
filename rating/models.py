from django.db import models
from django.utils import timezone
from common.models import BaseModel


class Rating(BaseModel):
    """
    Talabalarning reyting sistemasi.
    XP'ni yulduzga (⭐) bog'langan.
    3 ta reyting turi: daily (bugungi kun), weekly (bu hafta), all_time (umumiy)
    """
    
    class PeriodChoices(models.TextChoices):
        DAILY = 'daily', 'Bugungi kun'
        WEEKLY = 'weekly', 'Bu hafta'
        ALL_TIME = 'all_time', 'Umumiy'

    user = models.ForeignKey('account.User', on_delete=models.CASCADE, related_name='ratings')
    period = models.CharField('Reyting turi', max_length=20, choices=PeriodChoices.choices)    
    stars = models.FloatField('⭐ XP yulduzlari', default=0.0)    
    tests_completed = models.PositiveIntegerField('Tugagan testlar soni', default=0)
    correct_answers = models.PositiveIntegerField("To'g'ri javoblar soni", default=0)
    incorrect_answers = models.PositiveIntegerField("Noto'g'ri javoblar soni", default=0)
    
    # Leaderboard rank
    rank = models.PositiveIntegerField('Reyting joylanishi', null=True, blank=True)
    
    # Vaqt ma'lumotlari
    period_start_date = models.DateField('Davr boshlanish sanasi')
    period_end_date = models.DateField('Davr tugash sanasi')
    last_updated = models.DateTimeField('Oxirgi yangilangan vaqt', auto_now=True)

    class Meta:
        unique_together = ('user', 'period', 'period_start_date', 'period_end_date')
        ordering = ['-stars', '-tests_completed']
        indexes = [
            models.Index(fields=['period', '-stars']),
            models.Index(fields=['period', 'period_start_date']),
        ]

    def __str__(self):
        return f'{self.user.email} - {self.get_period_display()} ({self.stars:.1f} ⭐)'

    @property
    def xp_equivalent(self):
        """XP'ni yulduzdan qayta hisoblash (ishlatiladigan joyda)"""
        # XP scaling: 1 yulduz = 100 XP
        return int(self.stars * 100)

    @property
    def accuracy_percentage(self):
        """To'g'rilik foizi"""
        total = self.correct_answers + self.incorrect_answers
        if total == 0:
            return 0
        return (self.correct_answers / total) * 100


class RatingHistory(BaseModel):
    """
    Reyting o'zgarishlarining tarixi.
    Har safar reyting yangilanganda yangi yozuv.
    """
    
    user = models.ForeignKey('account.User', on_delete=models.CASCADE, related_name='rating_history')
    rating = models.ForeignKey(Rating, on_delete=models.CASCADE, related_name='history')
    
    # O'zgarishlar
    previous_stars = models.FloatField("Oldingi ⭐", null=True, blank=True)
    new_stars = models.FloatField("Yangi ⭐")
    stars_change = models.FloatField("O'zgarish miqdori")  # +0.5, -0.2, etc.
    
    previous_rank = models.PositiveIntegerField("Oldingi reyting joylanishi", null=True, blank=True)
    new_rank = models.PositiveIntegerField("Yangi reyting joylanishi", null=True, blank=True)
    
    # Sababi
    reason = models.CharField('O\'zgarish sababi', max_length=255)
    
    # Test ma'lumotlari (kim yangiladi)
    test_session = models.ForeignKey(
        'testengine.TestSession', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='rating_changes'
    )
    
    period = models.CharField('Qaysi davr yangilandi', max_length=20, choices=Rating.PeriodChoices.choices)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['period', '-created_at']),
        ]

    def __str__(self):
        return f'{self.user.email} - {self.period}: {self.previous_stars} → {self.new_stars}'


class TopicRating(BaseModel):
    """
    Har bir mavzu uchun alohida reyting.
    Qaysi mavzuda talaba yaxshi, qaysi mavzuda yomon ekanini ko'rish.
    """
    
    user = models.ForeignKey('account.User', on_delete=models.CASCADE, related_name='topic_ratings')
    topic = models.ForeignKey('catalog.Topic', on_delete=models.CASCADE, related_name='ratings')
    
    # ⭐ Mavzu reytingi
    stars = models.FloatField('⭐ Mavzu reytingi', default=0.0)
    
    # Mavzudagi statistika
    tests_completed = models.PositiveIntegerField('Tugagan testlar', default=0)
    correct_answers = models.PositiveIntegerField("To'g'ri javoblar", default=0)
    incorrect_answers = models.PositiveIntegerField("Noto'g'ri javoblar", default=0)
    
    # Oxirgi o'zgarish vaqti
    last_updated = models.DateTimeField('Oxirgi yangilangan vaqt', auto_now=True)

    class Meta:
        unique_together = ('user', 'topic')
        ordering = ['-stars']
        indexes = [
            models.Index(fields=['user', 'topic']),
            models.Index(fields=['user', '-stars']),
        ]

    def __str__(self):
        return f'{self.user.email} - {self.topic.name} ({self.stars:.1f} ⭐)'

    @property
    def accuracy_percentage(self):
        """To'g'rilik foizi"""
        total = self.correct_answers + self.incorrect_answers
        if total == 0:
            return 0
        return (self.correct_answers / total) * 100


class SubjectRating(BaseModel):
    """
    Har bir fan uchun alohida reyting.
    Fan bo'yicha o'rtacha reyting.
    """
    
    user = models.ForeignKey('account.User', on_delete=models.CASCADE, related_name='subject_ratings')
    subject = models.ForeignKey('catalog.Subject', on_delete=models.CASCADE, related_name='ratings')
    
    # ⭐ Fan reytingi (mavzuiarni o'rtachasi)
    stars = models.FloatField('⭐ Fan reytingi', default=0.0)
    
    # Fan statistikasi
    tests_completed = models.PositiveIntegerField('Tugagan testlar', default=0)
    correct_answers = models.PositiveIntegerField("To'g'ri javoblar", default=0)
    incorrect_answers = models.PositiveIntegerField("Noto'g'ri javoblar", default=0)
    
    # Qancha mavzu o'tigan
    topics_completed = models.PositiveIntegerField("O'tigan mavzular soni", default=0)
    
    # Oxirgi o'zgarish vaqti
    last_updated = models.DateTimeField('Oxirgi yangilangan vaqt', auto_now=True)

    class Meta:
        unique_together = ('user', 'subject')
        ordering = ['-stars']
        indexes = [
            models.Index(fields=['user', 'subject']),
            models.Index(fields=['user', '-stars']),
        ]

    def __str__(self):
        return f'{self.user.email} - {self.subject.name} ({self.stars:.1f} ⭐)'

    @property
    def accuracy_percentage(self):
        """To'g'rilik foizi"""
        total = self.correct_answers + self.incorrect_answers
        if total == 0:
            return 0
        return (self.correct_answers / total) * 100


class Leaderboard(BaseModel):
    """
    Leaderboard - top talabalar ro'yxati.
    3 ta davrda: daily, weekly, all_time
    """
    
    class PeriodChoices(models.TextChoices):
        DAILY = 'daily', 'Bugungi kun'
        WEEKLY = 'weekly', 'Bu hafta'
        ALL_TIME = 'all_time', 'Umumiy'

    period = models.CharField('Davr', max_length=20, choices=PeriodChoices.choices)
    rank = models.PositiveIntegerField('O\'rni')
    user = models.ForeignKey('account.User', on_delete=models.CASCADE, related_name='leaderboard_entries')
    
    stars = models.FloatField('⭐ Yulduzlar')
    tests_completed = models.PositiveIntegerField('Tugagan testlar')
    
    # Vaqt ma'lumotlari
    date = models.DateField('Sana', auto_now_add=True)
    last_updated = models.DateTimeField('Oxirgi yangilangan vaqt', auto_now=True)

    class Meta:
        unique_together = ('period', 'rank', 'date')
        ordering = ['-rank']
        indexes = [
            models.Index(fields=['period', 'date', 'rank']),
            models.Index(fields=['user', 'period']),
        ]

    def __str__(self):
        return f'#{self.rank} {self.user.email} ({self.get_period_display()}) - {self.stars:.1f} ⭐'
