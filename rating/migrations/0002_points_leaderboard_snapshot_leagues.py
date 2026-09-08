"""Reyting tizimini tuzatish: ball hisobi, snapshot leaderboard va ligalar.

Uchta xato tuzatiladi:

1. `all_time` davri chegarasi har kuni o'zgarardi (`today.replace(year=2000)`)
   va shu sababli "umumiy reyting" har kuni noldan boshlanardi. Endi davr
   qat'iy: 2000-01-01 .. 2100-01-01. Eski, kunlarga bo'linib ketgan
   `all_time` qatorlari bittaga BIRLASHTIRILADI.
2. `Leaderboard` modeli hech qachon to'ldirilmasdi. Jadval bo'sh, shuning
   uchun uni xavfsiz qayta yaratamiz — endi u tayyor kesim (snapshot)
   bo'ladi.
3. ⭐ faqat to'g'ri/xato nisbatidan hisoblanardi: javobsiz savol "bepul"
   edi va qiyinlik hisobga olinmasdi. `earned_points` / `possible_points`
   shu ikkalasini ham qamrab oladi.
"""

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


def merge_all_time_ratings(apps, schema_editor):
    """Kunlarga bo'linib ketgan `all_time` qatorlarini bittaga yig'adi."""
    Rating = apps.get_model('rating', 'Rating')
    RatingHistory = apps.get_model('rating', 'RatingHistory')

    from datetime import date
    start, end = date(2000, 1, 1), date(2100, 1, 1)

    by_user = {}
    for row in Rating.objects.filter(period='all_time').order_by('id'):
        by_user.setdefault(row.user_id, []).append(row)

    for user_id, rows in by_user.items():
        keeper = rows[0]
        for extra in rows[1:]:
            keeper.tests_completed += extra.tests_completed
            keeper.correct_answers += extra.correct_answers
            keeper.incorrect_answers += extra.incorrect_answers
            # Tarixni yo'qotmaymiz — birlashtirilgan qatorga ko'chiramiz.
            RatingHistory.objects.filter(rating_id=extra.id).update(rating_id=keeper.id)
            extra.delete()

        keeper.period_start_date = start
        keeper.period_end_date = end
        # Yangi maydonlar: eski `correct/incorrect` dan taxminiy ball.
        keeper.earned_points = float(keeper.correct_answers)
        keeper.possible_points = float(
            keeper.correct_answers + keeper.incorrect_answers
        )
        keeper.save()


def backfill_points(apps, schema_editor):
    """Mavjud reytinglarga ball maydonlarini to'ldiradi.

    Aniq qiyinlik og'irligini orqaga qarab tiklab bo'lmaydi, shuning uchun
    og'irlik 1.0 deb olinadi — bu eski ma'lumot uchun to'g'ri taxmin.
    """
    for model_name in ('Rating', 'TopicRating', 'SubjectRating'):
        Model = apps.get_model('rating', model_name)
        for row in Model.objects.filter(possible_points=0):
            answered = row.correct_answers + row.incorrect_answers
            if not answered:
                continue
            row.earned_points = float(row.correct_answers)
            row.possible_points = float(answered)
            row.save(update_fields=['earned_points', 'possible_points'])


class Migration(migrations.Migration):

    dependencies = [
        ('rating', '0001_initial'),
        ('testengine', '0003_dailytopicusage_explanationusage_and_more'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        # --- Rating: ball, XP, javobsizlar ------------------------------
        migrations.AddField(
            model_name='rating', name='unanswered_answers',
            field=models.PositiveIntegerField(default=0, verbose_name='Javobsiz savollar soni'),
        ),
        migrations.AddField(
            model_name='rating', name='earned_points',
            field=models.FloatField(default=0.0, verbose_name='Olingan ball'),
        ),
        migrations.AddField(
            model_name='rating', name='possible_points',
            field=models.FloatField(default=0.0, verbose_name="Mumkin bo'lgan ball"),
        ),
        migrations.AddField(
            model_name='rating', name='xp',
            field=models.PositiveIntegerField(default=0, verbose_name='Davr XP si'),
        ),
        migrations.AlterField(
            model_name='rating', name='stars',
            field=models.FloatField(default=0.0, verbose_name='⭐ Daraja'),
        ),
        migrations.AlterModelOptions(
            name='rating', options={'ordering': ['-xp', '-stars']},
        ),
        migrations.AddIndex(
            model_name='rating',
            index=models.Index(fields=['period', '-xp'], name='rating_rati_period_670d2b_idx'),
        ),

        # --- TopicRating / SubjectRating --------------------------------
        migrations.AddField(
            model_name='topicrating', name='unanswered_answers',
            field=models.PositiveIntegerField(default=0, verbose_name='Javobsiz savollar'),
        ),
        migrations.AddField(
            model_name='topicrating', name='earned_points',
            field=models.FloatField(default=0.0, verbose_name='Olingan ball'),
        ),
        migrations.AddField(
            model_name='topicrating', name='possible_points',
            field=models.FloatField(default=0.0, verbose_name="Mumkin bo'lgan ball"),
        ),
        migrations.AddField(
            model_name='subjectrating', name='unanswered_answers',
            field=models.PositiveIntegerField(default=0, verbose_name='Javobsiz savollar'),
        ),
        migrations.AddField(
            model_name='subjectrating', name='earned_points',
            field=models.FloatField(default=0.0, verbose_name='Olingan ball'),
        ),
        migrations.AddField(
            model_name='subjectrating', name='possible_points',
            field=models.FloatField(default=0.0, verbose_name="Mumkin bo'lgan ball"),
        ),

        migrations.RunPython(merge_all_time_ratings, migrations.RunPython.noop),
        migrations.RunPython(backfill_points, migrations.RunPython.noop),

        # --- Leaderboard: o'lik model -> snapshot ------------------------
        # Jadval hech qachon to'ldirilmagan (hech bir kod unga yozmasdi),
        # shuning uchun qayta yaratish ma'lumot yo'qotmaydi.
        migrations.DeleteModel(name='Leaderboard'),
        migrations.CreateModel(
            name='Leaderboard',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Yaratilgan sana')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='Yangilangan sana')),
                ('period', models.CharField(choices=[('daily', 'Bugungi kun'), ('weekly', 'Bu hafta'), ('all_time', 'Umumiy')], max_length=20, verbose_name='Davr')),
                ('period_start_date', models.DateField(verbose_name='Davr boshlanishi')),
                ('period_end_date', models.DateField(verbose_name='Davr tugashi')),
                ('rank', models.PositiveIntegerField(verbose_name="O'rni")),
                ('xp', models.PositiveIntegerField(default=0, verbose_name='XP')),
                ('stars', models.FloatField(default=0.0, verbose_name='⭐ Daraja')),
                ('tests_completed', models.PositiveIntegerField(default=0, verbose_name='Tugagan testlar')),
                ('generated_at', models.DateTimeField(auto_now=True, verbose_name='Hisoblangan vaqti')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='leaderboard_entries', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Leaderboard qatori',
                'verbose_name_plural': 'Leaderboard',
                'ordering': ['period', 'rank'],
            },
        ),
        migrations.AddConstraint(
            model_name='leaderboard',
            constraint=models.UniqueConstraint(
                fields=('period', 'period_start_date', 'rank'), name='uniq_leaderboard_rank'
            ),
        ),
        migrations.AddIndex(
            model_name='leaderboard',
            index=models.Index(fields=['period', 'period_start_date', 'rank'], name='rating_lead_period_440c5d_idx'),
        ),
        migrations.AddIndex(
            model_name='leaderboard',
            index=models.Index(fields=['user', 'period'], name='rating_lead_user_id_12cb78_idx'),
        ),

        # --- Ligalar -----------------------------------------------------
        migrations.CreateModel(
            name='League',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Yaratilgan sana')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='Yangilangan sana')),
                ('tier', models.PositiveSmallIntegerField(choices=[(1, 'Bronza'), (2, 'Kumush'), (3, 'Oltin'), (4, 'Platina'), (5, 'Olmos')], default=1, verbose_name='Daraja')),
                ('group_number', models.PositiveIntegerField(default=1, verbose_name='Guruh raqami')),
                ('period_start_date', models.DateField(verbose_name='Hafta boshlanishi')),
                ('period_end_date', models.DateField(verbose_name='Hafta tugashi')),
                ('is_closed', models.BooleanField(default=False, verbose_name='Yakunlangan')),
            ],
            options={
                'verbose_name': 'Liga',
                'verbose_name_plural': 'Ligalar',
                'ordering': ['-period_start_date', '-tier', 'group_number'],
            },
        ),
        migrations.AddConstraint(
            model_name='league',
            constraint=models.UniqueConstraint(
                fields=('tier', 'group_number', 'period_start_date'),
                name='uniq_league_group_per_week',
            ),
        ),
        migrations.AddIndex(
            model_name='league',
            index=models.Index(fields=['period_start_date', 'tier'], name='rating_leag_period__8fcaf2_idx'),
        ),
        migrations.CreateModel(
            name='LeagueMembership',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Yaratilgan sana')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='Yangilangan sana')),
                ('xp', models.PositiveIntegerField(default=0, verbose_name='Haftalik XP')),
                ('rank', models.PositiveIntegerField(blank=True, null=True, verbose_name="O'rni")),
                ('outcome', models.CharField(blank=True, choices=[('promoted', "Ko'tarildi"), ('stayed', 'Qoldi'), ('demoted', 'Tushdi')], max_length=10, verbose_name='Natija')),
                ('league', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='memberships', to='rating.league')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='league_memberships', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': "Liga a'zoligi",
                'verbose_name_plural': "Liga a'zoliklari",
                'ordering': ['-xp', 'id'],
            },
        ),
        migrations.AddConstraint(
            model_name='leaguemembership',
            constraint=models.UniqueConstraint(fields=('league', 'user'), name='uniq_league_membership'),
        ),
        migrations.AddIndex(
            model_name='leaguemembership',
            index=models.Index(fields=['user', '-created_at'], name='rating_leag_user_id_e54974_idx'),
        ),
        migrations.AddIndex(
            model_name='leaguemembership',
            index=models.Index(fields=['league', '-xp'], name='rating_leag_league__40eeac_idx'),
        ),
    ]
