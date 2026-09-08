from django.db import models
from common.models import BaseModel


DEFAULT_GRADE_NAME = 'Umumiy'


class Subject(BaseModel):
    name = models.CharField('Nomi (UZ)', max_length=100)
    name_ru = models.CharField('Nomi (RU)', max_length=100, blank=True)
    name_en = models.CharField('Nomi (EN)', max_length=100, blank=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


class Grade(BaseModel):
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name='grades')
    name = models.CharField('Nomi (UZ)', max_length=150)
    name_ru = models.CharField('Nomi (RU)', max_length=150, blank=True)
    name_en = models.CharField('Nomi (EN)', max_length=150, blank=True)
    order = models.PositiveSmallIntegerField('Tartib', default=0)
    is_active = models.BooleanField('Faol', default=True)

    class Meta:
        ordering = ['subject_id', 'order', 'id']
        verbose_name = 'Sinf / Kitob'
        verbose_name_plural = 'Sinflar / Kitoblar'
        constraints = [
            models.UniqueConstraint(fields=['subject', 'name'], name='uniq_grade_per_subject'),
        ]
        indexes = [
            models.Index(fields=['subject', 'order']),
        ]

    def __str__(self):
        return f'{self.subject.name} — {self.name}'


class Topic(BaseModel):
    grade = models.ForeignKey(Grade, on_delete=models.CASCADE, related_name='topics',verbose_name='Sinf / Kitob',)
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name='topics',editable=False, verbose_name='Fan (avtomatik)',)
    name = models.CharField('Nomi (UZ)', max_length=150)
    name_ru = models.CharField('Nomi (RU)', max_length=150, blank=True)
    name_en = models.CharField('Nomi (EN)', max_length=150, blank=True)
    order = models.PositiveSmallIntegerField('Tartib', default=0)
    is_active = models.BooleanField('Faol', default=True)
    available_question_count = models.PositiveIntegerField('Mavjud savollar soni', default=0, editable=False)

    class Meta:
        ordering = ['subject_id', 'order', 'name']
        constraints = [
            models.UniqueConstraint(fields=['grade', 'name'], name='uniq_topic_per_grade'),
        ]
        indexes = [
            models.Index(fields=['grade', 'order']),
            models.Index(fields=['subject', 'is_active']),
        ]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if self.grade_id is None and self.subject_id is not None:
            grade, _ = Grade.objects.get_or_create(
                subject_id=self.subject_id,
                name=DEFAULT_GRADE_NAME,
                defaults={'order': 0},
            )
            self.grade_id = grade.id

        if self.grade_id is not None:
            cached_grade = self._state.fields_cache.get('grade')
            subject_id = (
                cached_grade.subject_id if cached_grade is not None
                else Grade.objects.values_list('subject_id', flat=True).get(pk=self.grade_id)
            )
            if self.subject_id != subject_id:
                self.subject_id = subject_id
                update_fields = kwargs.get('update_fields')
                if update_fields is not None:
                    kwargs['update_fields'] = set(update_fields) | {'subject'}

        super().save(*args, **kwargs)

    def recount_questions(self, save=True) -> int:
        total = Question.objects.available().filter(topic_id=self.pk).count()
        if total != self.available_question_count:
            self.available_question_count = total
            if save:
                Topic.objects.filter(pk=self.pk).update(available_question_count=total)
        return total


class QuestionQuerySet(models.QuerySet):
    def available(self):
        return self.filter(status=Question.Status.PUBLISHED, is_active=True)


class Question(BaseModel):
    class Difficulty(models.IntegerChoices):
        VERY_EASY = 1, 'Juda oson'
        EASY = 2, 'Oson'
        MEDIUM = 3, "O'rtacha"
        HARD = 4, 'Qiyin'
        VERY_HARD = 5, 'Juda qiyin'

    class Status(models.TextChoices):
        DRAFT = 'draft', 'Qoralama'
        REVIEW = 'review', 'Tekshiruvda'
        PUBLISHED = 'published', 'Chop etilgan'
        ARCHIVED = 'archived', 'Arxivlangan'

    topic = models.ForeignKey(Topic, on_delete=models.CASCADE, related_name='questions')
    text = models.TextField('Savol matni (UZ)')
    text_ru = models.TextField('Savol matni (RU)', blank=True)
    text_en = models.TextField('Savol matni (EN)', blank=True)
    options = models.JSONField('Variantlar (UZ)')
    options_ru = models.JSONField('Variantlar (RU)', null=True, blank=True)
    options_en = models.JSONField('Variantlar (EN)', null=True, blank=True)
    image = models.ImageField('Rasm (ixtiyoriy)', upload_to='questions/%Y/%m/', null=True, blank=True)
    image_caption = models.CharField('Rasm izohi', max_length=255, blank=True)
    correct_option = models.CharField("To'g'ri javob", max_length=1)
    difficulty = models.PositiveSmallIntegerField('Qiyinlik darajasi', choices=Difficulty.choices, default=Difficulty.MEDIUM)
    explanation = models.TextField('Yechim izohi (UZ)', blank=True)
    explanation_ru = models.TextField('Yechim izohi (RU)', blank=True)
    explanation_en = models.TextField('Yechim izohi (EN)', blank=True)
    explanation_image = models.ImageField('Yechim rasmi (ixtiyoriy)', upload_to='explanations/%Y/%m/', null=True, blank=True)
    hint = models.CharField('Maslahat (javobni ochmasdan)', max_length=500, blank=True)
    status = models.CharField('Holati', max_length=10, choices=Status.choices, default=Status.PUBLISHED)
    is_active = models.BooleanField('Faol', default=True)
    source = models.CharField('Manba', max_length=150, blank=True,
        help_text="Masalan: «DTM 2023, Matematika» yoki «Muallif savoli»",)
    source_year = models.PositiveSmallIntegerField('Manba yili', null=True, blank=True)
    author = models.ForeignKey('account.User', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='authored_questions', verbose_name='Muallif',)
    reviewed_by = models.ForeignKey('account.User', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='reviewed_questions', verbose_name='Tekshirgan',)
    times_answered = models.PositiveIntegerField('Javob berilgan', default=0, editable=False)
    times_correct = models.PositiveIntegerField("To'g'ri javob", default=0, editable=False)
    total_time_seconds = models.PositiveIntegerField('Jami sarflangan vaqt', default=0, editable=False)

    objects = QuestionQuerySet.as_manager()

    class Meta:
        ordering = ['topic_id', 'id']
        indexes = [
            models.Index(fields=['topic', 'difficulty']),
            models.Index(fields=['topic', 'status', 'is_active']),
        ]

    @classmethod
    def from_db(cls, db, field_names, values):
        instance = super().from_db(db, field_names, values)
        instance._previous_topic_id = instance.topic_id
        return instance

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        self._previous_topic_id = self.topic_id

    def __str__(self):
        return self.text[:50]

    @property
    def is_available(self) -> bool:
        return self.status == self.Status.PUBLISHED and self.is_active

    @property
    def p_value(self) -> float | None:
        if self.times_answered < 20:
            return None
        return round(self.times_correct / self.times_answered, 4)

    @property
    def observed_difficulty(self) -> int | None:
        p = self.p_value
        if p is None:
            return None
        for threshold, level in ((0.85, 1), (0.70, 2), (0.50, 3), (0.30, 4)):
            if p >= threshold:
                return level
        return 5

    @property
    def avg_time_seconds(self) -> int | None:
        if not self.times_answered:
            return None
        return round(self.total_time_seconds / self.times_answered)
