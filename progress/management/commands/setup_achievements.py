from django.core.management.base import BaseCommand

from progress.models import Achievement

M = Achievement.Metric

ACHIEVEMENTS = [
    # --- Hajm ---
    ('first-test', '🎯', 'Birinchi qadam', 'Birinchi testni yakunladingiz', M.TESTS_COMPLETED, 1, 10),
    ('ten-tests', '📚', "O'nlik", '10 ta test yakunlandi', M.TESTS_COMPLETED, 10, 25),
    ('fifty-tests', '🏋️', 'Mehnatkash', '50 ta test yakunlandi', M.TESTS_COMPLETED, 50, 75),
    ('hundred-tests', '🎓', 'Tajribali', '100 ta test yakunlandi', M.TESTS_COMPLETED, 100, 150),

    ('hundred-questions', '💯', '100 savol', '100 ta savolga javob berdingiz', M.QUESTIONS_ANSWERED, 100, 25),
    ('thousand-questions', '🚀', 'Ming savol', '1000 ta savolga javob berdingiz', M.QUESTIONS_ANSWERED, 1000, 200),
    ('five-thousand-questions', '🌟', 'Besh ming', '5000 ta savolga javob berdingiz', M.QUESTIONS_ANSWERED, 5000, 500),

    # --- Sifat ---
    ('hundred-correct', '✅', "100 to'g'ri", "100 ta to'g'ri javob", M.CORRECT_ANSWERS, 100, 30),
    ('thousand-correct', '🥇', "1000 to'g'ri", "1000 ta to'g'ri javob", M.CORRECT_ANSWERS, 1000, 250),
    ('first-perfect', '🎖️', 'Benuqson', 'Testni xatosiz yakunladingiz', M.PERFECT_TESTS, 1, 50),
    ('ten-perfect', '👑', "O'n benuqson", '10 ta test xatosiz yakunlandi', M.PERFECT_TESTS, 10, 200),

    # --- Muntazamlik ---
    ('streak-3', '🔥', '3 kun', '3 kun ketma-ket mashq qildingiz', M.CURRENT_STREAK, 3, 20),
    ('streak-7', '🔥', 'Bir hafta', '7 kun ketma-ket mashq qildingiz', M.CURRENT_STREAK, 7, 50),
    ('streak-30', '🔥', 'Bir oy', '30 kun ketma-ket mashq qildingiz', M.CURRENT_STREAK, 30, 300),
    ('streak-100', '💎', '100 kun', '100 kun ketma-ket mashq qildingiz', M.CURRENT_STREAK, 100, 1000),

    # --- XP ---
    ('xp-1000', '⚡', '1000 XP', '1000 XP to\'pladingiz', M.TOTAL_XP, 1000, 0),
    ('xp-10000', '⚡', '10 000 XP', '10 000 XP to\'pladingiz', M.TOTAL_XP, 10000, 0),

    # --- Daraja (⭐ x10) ---
    ('subject-4-stars', '⭐', 'Fan ustasi', 'Biror fanda 4.0 ⭐ darajaga yetdingiz', M.SUBJECT_STARS, 40, 150),
    ('subject-45-stars', '🌠', 'Fan bilimdoni', 'Biror fanda 4.5 ⭐ darajaga yetdingiz', M.SUBJECT_STARS, 45, 400),
]


class Command(BaseCommand):
    help = 'Boshlang\'ich yutuqlar to\'plamini yaratadi (mavjudini tegmaydi).'

    def add_arguments(self, parser):
        parser.add_argument(
            '--reset', action='store_true',
            help='Mavjud yutuqlarni ham standart qiymatlarga qaytaradi.',
        )

    def handle(self, *args, **options):
        created = updated = skipped = 0

        for order, (code, icon, name, description, metric, threshold, reward) in enumerate(
            ACHIEVEMENTS, start=1
        ):
            defaults = {
                'icon': icon, 'name': name, 'description': description,
                'metric': metric, 'threshold': threshold,
                'xp_reward': reward, 'order': order, 'is_active': True,
            }
            achievement = Achievement.objects.filter(code=code).first()

            if achievement is None:
                Achievement.objects.create(code=code, **defaults)
                created += 1
            elif options['reset']:
                for field, value in defaults.items():
                    setattr(achievement, field, value)
                achievement.save()
                updated += 1
            else:
                skipped += 1

        self.stdout.write(self.style.SUCCESS(
            f"Yutuqlar: yaratildi {created}, yangilandi {updated}, tegilmadi {skipped}."
        ))
