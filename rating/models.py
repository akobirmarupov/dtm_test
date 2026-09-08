from django.db import models
from django.utils import timezone
from common.models import BaseModel


class Rating(BaseModel):
    class PeriodChoices(models.TextChoices):
        DAILY = 'daily', 'Bugungi kun'
        WEEKLY = 'weekly', 'Bu hafta'
        ALL_TIME = 'all_time', 'Umumiy'

    user = models.ForeignKey('account.User', on_delete=models.CASCADE, related_name='ratings')
    period = models.CharField('Reyting turi', max_length=20, choices=PeriodChoices.choices)    
    stars = models.FloatField('⭐ Daraja', default=0.0)    
    tests_completed = models.PositiveIntegerField('Tugagan testlar soni', default=0)
    correct_answers = models.PositiveIntegerField("To'g'ri javoblar soni", default=0)
    incorrect_answers = models.PositiveIntegerField("Noto'g'ri javoblar soni", default=0)
    unanswered_answers = models.PositiveIntegerField('Javobsiz savollar soni', default=0)
    earned_points = models.FloatField('Olingan ball', default=0.0)
    possible_points = models.FloatField('Mumkin bo\'lgan ball', default=0.0)
    xp = models.PositiveIntegerField('Davr XP si', default=0)
    rank = models.PositiveIntegerField('Reyting joylanishi', null=True, blank=True)
    period_start_date = models.DateField('Davr boshlanish sanasi')
    period_end_date = models.DateField('Davr tugash sanasi')
    last_updated = models.DateTimeField('Oxirgi yangilangan vaqt', auto_now=True)

    class Meta:
        unique_together = ('user', 'period', 'period_start_date', 'period_end_date')
        ordering = ['-xp', '-stars']
        indexes = [
            models.Index(fields=['period', '-xp']),
            models.Index(fields=['period', '-stars']),
            models.Index(fields=['period', 'period_start_date']),
        ]

    def __str__(self):
        return f'{self.user.email} - {self.get_period_display()} ({self.stars:.1f} ⭐)'

    @property
    def accuracy_percentage(self):
        total = self.correct_answers + self.incorrect_answers
        if total == 0:
            return 0
        return round(self.correct_answers / total * 100, 2)

    @property
    def completion_percentage(self):
        total = self.correct_answers + self.incorrect_answers + self.unanswered_answers
        if total == 0:
            return 0
        return round((total - self.unanswered_answers) / total * 100, 2)


class RatingHistory(BaseModel):
    user = models.ForeignKey('account.User', on_delete=models.CASCADE, related_name='rating_history')
    rating = models.ForeignKey(Rating, on_delete=models.CASCADE, related_name='history')
    previous_stars = models.FloatField("Oldingi ⭐", null=True, blank=True)
    new_stars = models.FloatField("Yangi ⭐")
    stars_change = models.FloatField("O'zgarish miqdori")  # +0.5, -0.2, etc.
    previous_rank = models.PositiveIntegerField("Oldingi reyting joylanishi", null=True, blank=True)
    new_rank = models.PositiveIntegerField("Yangi reyting joylanishi", null=True, blank=True)
    reason = models.CharField('O\'zgarish sababi', max_length=255)
    test_session = models.ForeignKey('testengine.TestSession', on_delete=models.SET_NULL, null=True, blank=True,related_name='rating_changes')
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
    user = models.ForeignKey('account.User', on_delete=models.CASCADE, related_name='topic_ratings')
    topic = models.ForeignKey('catalog.Topic', on_delete=models.CASCADE, related_name='ratings')
    stars = models.FloatField('⭐ Mavzu reytingi', default=0.0)
    tests_completed = models.PositiveIntegerField('Tugagan testlar', default=0)
    correct_answers = models.PositiveIntegerField("To'g'ri javoblar", default=0)
    incorrect_answers = models.PositiveIntegerField("Noto'g'ri javoblar", default=0)
    unanswered_answers = models.PositiveIntegerField('Javobsiz savollar', default=0)
    earned_points = models.FloatField('Olingan ball', default=0.0)
    possible_points = models.FloatField("Mumkin bo'lgan ball", default=0.0)
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
        total = self.correct_answers + self.incorrect_answers
        if total == 0:
            return 0
        return round(self.correct_answers / total * 100, 2)

    @property
    def needs_practice(self) -> bool:
        answered = self.correct_answers + self.incorrect_answers
        return answered >= 10 and self.stars < 3.0


class SubjectRating(BaseModel):
    user = models.ForeignKey('account.User', on_delete=models.CASCADE, related_name='subject_ratings')
    subject = models.ForeignKey('catalog.Subject', on_delete=models.CASCADE, related_name='ratings')
    stars = models.FloatField('⭐ Fan reytingi', default=0.0)
    tests_completed = models.PositiveIntegerField('Tugagan testlar', default=0)
    correct_answers = models.PositiveIntegerField("To'g'ri javoblar", default=0)
    incorrect_answers = models.PositiveIntegerField("Noto'g'ri javoblar", default=0)
    unanswered_answers = models.PositiveIntegerField('Javobsiz savollar', default=0)
    earned_points = models.FloatField('Olingan ball', default=0.0)
    possible_points = models.FloatField("Mumkin bo'lgan ball", default=0.0)
    topics_completed = models.PositiveIntegerField("O'tigan mavzular soni", default=0)
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
        total = self.correct_answers + self.incorrect_answers
        if total == 0:
            return 0
        return (self.correct_answers / total) * 100


class Leaderboard(BaseModel):
    class PeriodChoices(models.TextChoices):
        DAILY = 'daily', 'Bugungi kun'
        WEEKLY = 'weekly', 'Bu hafta'
        ALL_TIME = 'all_time', 'Umumiy'

    period = models.CharField('Davr', max_length=20, choices=PeriodChoices.choices)
    period_start_date = models.DateField('Davr boshlanishi')
    period_end_date = models.DateField('Davr tugashi')
    rank = models.PositiveIntegerField("O'rni")
    user = models.ForeignKey('account.User', on_delete=models.CASCADE, related_name='leaderboard_entries')
    xp = models.PositiveIntegerField('XP', default=0)
    stars = models.FloatField('⭐ Daraja', default=0.0)
    tests_completed = models.PositiveIntegerField('Tugagan testlar', default=0)
    generated_at = models.DateTimeField('Hisoblangan vaqti', auto_now=True)

    class Meta:
        ordering = ['period', 'rank']
        verbose_name = 'Leaderboard qatori'
        verbose_name_plural = 'Leaderboard'
        constraints = [
            models.UniqueConstraint(
                fields=['period', 'period_start_date', 'rank'],
                name='uniq_leaderboard_rank',
            ),
        ]
        indexes = [
            models.Index(fields=['period', 'period_start_date', 'rank']),
            models.Index(fields=['user', 'period']),
        ]

    def __str__(self):
        return f'#{self.rank} {self.user_id} ({self.get_period_display()}) - {self.xp} XP'


# Ligalar
class League(BaseModel):
    class Tier(models.IntegerChoices):
        BRONZE = 1, 'Bronza'
        SILVER = 2, 'Kumush'
        GOLD = 3, 'Oltin'
        PLATINUM = 4, 'Platina'
        DIAMOND = 5, 'Olmos'

    tier = models.PositiveSmallIntegerField('Daraja', choices=Tier.choices, default=Tier.BRONZE)
    group_number = models.PositiveIntegerField('Guruh raqami', default=1)
    period_start_date = models.DateField('Hafta boshlanishi')
    period_end_date = models.DateField('Hafta tugashi')
    is_closed = models.BooleanField('Yakunlangan', default=False)

    class Meta:
        ordering = ['-period_start_date', '-tier', 'group_number']
        verbose_name = 'Liga'
        verbose_name_plural = 'Ligalar'
        constraints = [
            models.UniqueConstraint(
                fields=['tier', 'group_number', 'period_start_date'],
                name='uniq_league_group_per_week',
            ),
        ]
        indexes = [
            models.Index(fields=['period_start_date', 'tier']),
        ]

    def __str__(self):
        return f'{self.get_tier_display()} #{self.group_number} ({self.period_start_date})'


class LeagueMembership(BaseModel):
    class Outcome(models.TextChoices):
        PROMOTED = 'promoted', "Ko'tarildi"
        STAYED = 'stayed', 'Qoldi'
        DEMOTED = 'demoted', 'Tushdi'

    league = models.ForeignKey(League, on_delete=models.CASCADE, related_name='memberships')
    user = models.ForeignKey('account.User', on_delete=models.CASCADE, related_name='league_memberships')
    xp = models.PositiveIntegerField('Haftalik XP', default=0)
    rank = models.PositiveIntegerField("O'rni", null=True, blank=True)
    outcome = models.CharField('Natija', max_length=10, choices=Outcome.choices, blank=True)

    class Meta:
        ordering = ['-xp', 'id']
        verbose_name = 'Liga a\'zoligi'
        verbose_name_plural = 'Liga a\'zoliklari'
        constraints = [
            models.UniqueConstraint(
                fields=['league', 'user'], name='uniq_league_membership'
            ),
        ]
        indexes = [
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['league', '-xp']),
        ]

    def __str__(self):
        return f'{self.user_id} - {self.league} ({self.xp} XP)'
