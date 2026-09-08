"""Subject -> Grade -> Topic ierarxiyasi va savol hayot sikli.

Mavjud mavzular `grade` siz qolib ketmasligi kerak, shuning uchun ko'chirish
uch bosqichda: ustun `null=True` bilan qo'shiladi, har bir fanga «Umumiy»
bo'limi ochilib mavzular unga biriktiriladi, keyin ustun majburiy qilinadi.
"""

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


DEFAULT_GRADE_NAME = 'Umumiy'


def create_default_grades(apps, schema_editor):
    Subject = apps.get_model('catalog', 'Subject')
    Grade = apps.get_model('catalog', 'Grade')
    Topic = apps.get_model('catalog', 'Topic')

    for subject in Subject.objects.all():
        topics = Topic.objects.filter(subject_id=subject.id, grade__isnull=True)
        if not topics.exists():
            continue
        grade, _ = Grade.objects.get_or_create(
            subject_id=subject.id, name=DEFAULT_GRADE_NAME, defaults={'order': 0}
        )
        topics.update(grade_id=grade.id)


def drop_default_grades(apps, schema_editor):
    Grade = apps.get_model('catalog', 'Grade')
    Grade.objects.filter(name=DEFAULT_GRADE_NAME).delete()


def backfill_question_counts(apps, schema_editor):
    Topic = apps.get_model('catalog', 'Topic')
    Question = apps.get_model('catalog', 'Question')

    counts = {}
    for topic_id in Question.objects.filter(
        status='published', is_active=True
    ).values_list('topic_id', flat=True):
        counts[topic_id] = counts.get(topic_id, 0) + 1

    for topic in Topic.objects.all().only('id'):
        total = counts.get(topic.id, 0)
        Topic.objects.filter(pk=topic.id).update(available_question_count=total)


class Migration(migrations.Migration):

    dependencies = [
        ('catalog', '0002_alter_question_options_alter_subject_options_and_more'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        # --- Grade ---------------------------------------------------------
        migrations.CreateModel(
            name='Grade',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Yaratilgan sana')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='Yangilangan sana')),
                ('name', models.CharField(max_length=150, verbose_name='Nomi (UZ)')),
                ('name_ru', models.CharField(blank=True, max_length=150, verbose_name='Nomi (RU)')),
                ('name_en', models.CharField(blank=True, max_length=150, verbose_name='Nomi (EN)')),
                ('order', models.PositiveSmallIntegerField(default=0, verbose_name='Tartib')),
                ('is_active', models.BooleanField(default=True, verbose_name='Faol')),
                ('subject', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='grades', to='catalog.subject')),
            ],
            options={
                'verbose_name': 'Sinf / Kitob',
                'verbose_name_plural': 'Sinflar / Kitoblar',
                'ordering': ['subject_id', 'order', 'id'],
            },
        ),
        migrations.AddConstraint(
            model_name='grade',
            constraint=models.UniqueConstraint(fields=('subject', 'name'), name='uniq_grade_per_subject'),
        ),
        migrations.AddIndex(
            model_name='grade',
            index=models.Index(fields=['subject', 'order'], name='catalog_gra_subject_dd8c28_idx'),
        ),

        # --- Topic ---------------------------------------------------------
        migrations.AddField(
            model_name='topic',
            name='grade',
            field=models.ForeignKey(
                null=True, on_delete=django.db.models.deletion.CASCADE,
                related_name='topics', to='catalog.grade', verbose_name='Sinf / Kitob',
            ),
        ),
        migrations.RunPython(create_default_grades, drop_default_grades),
        # PostgreSQL: yuqoridagi UPDATE kechiktirilgan FK triggerlarini ochiq
        # qoldiradi va shu tranzaksiyada CREATE INDEX ni rad etadi
        # ("cannot CREATE INDEX ... because it has pending trigger events").
        # Triggerlarni shu yerda majburan yopamiz.
        migrations.RunSQL(
            'SET CONSTRAINTS ALL IMMEDIATE',
            reverse_sql=migrations.RunSQL.noop,
        ),
        migrations.AlterField(
            model_name='topic',
            name='grade',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE, related_name='topics',
                to='catalog.grade', verbose_name='Sinf / Kitob',
            ),
        ),
        migrations.AlterField(
            model_name='topic',
            name='subject',
            field=models.ForeignKey(
                editable=False, on_delete=django.db.models.deletion.CASCADE,
                related_name='topics', to='catalog.subject', verbose_name='Fan (avtomatik)',
            ),
        ),
        migrations.AddField(
            model_name='topic',
            name='order',
            field=models.PositiveSmallIntegerField(default=0, verbose_name='Tartib'),
        ),
        migrations.AddField(
            model_name='topic',
            name='is_active',
            field=models.BooleanField(default=True, verbose_name='Faol'),
        ),
        migrations.AddField(
            model_name='topic',
            name='available_question_count',
            field=models.PositiveIntegerField(default=0, editable=False, verbose_name='Mavjud savollar soni'),
        ),
        migrations.AlterModelOptions(
            name='topic',
            options={'ordering': ['subject_id', 'order', 'name']},
        ),
        migrations.AddConstraint(
            model_name='topic',
            constraint=models.UniqueConstraint(fields=('grade', 'name'), name='uniq_topic_per_grade'),
        ),
        migrations.AddIndex(
            model_name='topic',
            index=models.Index(fields=['grade', 'order'], name='catalog_top_grade_i_0f2e96_idx'),
        ),
        migrations.AddIndex(
            model_name='topic',
            index=models.Index(fields=['subject', 'is_active'], name='catalog_top_subject_8d5b79_idx'),
        ),

        # --- Question: yechim izohi ----------------------------------------
        migrations.AddField(
            model_name='question',
            name='explanation',
            field=models.TextField(blank=True, verbose_name='Yechim izohi (UZ)'),
        ),
        migrations.AddField(
            model_name='question',
            name='explanation_ru',
            field=models.TextField(blank=True, verbose_name='Yechim izohi (RU)'),
        ),
        migrations.AddField(
            model_name='question',
            name='explanation_en',
            field=models.TextField(blank=True, verbose_name='Yechim izohi (EN)'),
        ),
        migrations.AddField(
            model_name='question',
            name='explanation_image',
            field=models.ImageField(blank=True, null=True, upload_to='explanations/%Y/%m/', verbose_name='Yechim rasmi (ixtiyoriy)'),
        ),
        migrations.AddField(
            model_name='question',
            name='hint',
            field=models.CharField(blank=True, max_length=500, verbose_name="Maslahat (javobni ochmasdan)"),
        ),

        # --- Question: hayot sikli va manba --------------------------------
        migrations.AddField(
            model_name='question',
            name='status',
            field=models.CharField(
                choices=[('draft', 'Qoralama'), ('review', 'Tekshiruvda'),
                         ('published', 'Chop etilgan'), ('archived', 'Arxivlangan')],
                default='published', max_length=10, verbose_name='Holati',
            ),
        ),
        migrations.AddField(
            model_name='question',
            name='is_active',
            field=models.BooleanField(default=True, verbose_name='Faol'),
        ),
        migrations.AddField(
            model_name='question',
            name='source',
            field=models.CharField(
                blank=True, max_length=150,
                help_text='Masalan: «DTM 2023, Matematika» yoki «Muallif savoli»',
                verbose_name='Manba',
            ),
        ),
        migrations.AddField(
            model_name='question',
            name='source_year',
            field=models.PositiveSmallIntegerField(blank=True, null=True, verbose_name='Manba yili'),
        ),
        migrations.AddField(
            model_name='question',
            name='author',
            field=models.ForeignKey(
                blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL,
                related_name='authored_questions', to=settings.AUTH_USER_MODEL,
                verbose_name='Muallif',
            ),
        ),
        migrations.AddField(
            model_name='question',
            name='reviewed_by',
            field=models.ForeignKey(
                blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL,
                related_name='reviewed_questions', to=settings.AUTH_USER_MODEL,
                verbose_name='Tekshirgan',
            ),
        ),

        # --- Question: statistika ------------------------------------------
        migrations.AddField(
            model_name='question',
            name='times_answered',
            field=models.PositiveIntegerField(default=0, editable=False, verbose_name='Javob berilgan'),
        ),
        migrations.AddField(
            model_name='question',
            name='times_correct',
            field=models.PositiveIntegerField(default=0, editable=False, verbose_name="To'g'ri javob"),
        ),
        migrations.AddField(
            model_name='question',
            name='total_time_seconds',
            field=models.PositiveIntegerField(default=0, editable=False, verbose_name='Jami sarflangan vaqt'),
        ),
        migrations.AddIndex(
            model_name='question',
            index=models.Index(fields=['topic', 'status', 'is_active'], name='catalog_que_topic_i_ab8750_idx'),
        ),

        migrations.RunPython(backfill_question_counts, migrations.RunPython.noop),
    ]
