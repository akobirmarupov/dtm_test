from decimal import Decimal

from django.core.management.base import BaseCommand

from billing.entitlements import FREE_DAILY_TOPIC_LIMIT, invalidate_free_plan_cache
from billing.models import Plan

PLANS = [
    {
        'code': 'free',
        'name': 'Bepul',
        'name_ru': 'Бесплатный',
        'name_en': 'Free',
        'description': "Kuniga 4 ta mavzuda test. Natija va reyting ochiq.",
        'price': Decimal('0'),
        'duration_days': 3650,
        'is_pro': False,
        'daily_topic_limit': FREE_DAILY_TOPIC_LIMIT,
        'max_question_count': 60,
        'can_view_explanations': False,
        'explanation_limit_per_day': None,
        'features': {'ai_tutor': False, 'mock_exam': False},
    },
    {
        'code': 'pro_basic',
        'name': 'Pro-Basic',
        'name_ru': 'Pro-Basic',
        'name_en': 'Pro-Basic',
        'description': "Cheksiz mavzu. Kuniga 3 ta testning yechim izohlari.",
        'price': Decimal('35000'),
        'duration_days': 30,
        'is_pro': True,
        'daily_topic_limit': None,
        'max_question_count': 60,
        'can_view_explanations': True,
        # TZ da Pro-Basic cheklovi "keyin belgilanadi" deyilgan. Shu yerda
        # boshlang'ich qiymat qo'yildi; admin uni bir bosishda o'zgartiradi.
        'explanation_limit_per_day': 3,
        'features': {'ai_tutor': False, 'mock_exam': True},
    },
    {
        'code': 'pro_full',
        'name': 'Pro-Full',
        'name_ru': 'Pro-Full',
        'name_en': 'Pro-Full',
        'description': "Cheksiz mavzu va cheksiz yechim izohlari.",
        'price': Decimal('59000'),
        'duration_days': 30,
        'is_pro': True,
        'daily_topic_limit': None,
        'max_question_count': 60,
        'can_view_explanations': True,
        'explanation_limit_per_day': None,
        'features': {'ai_tutor': True, 'mock_exam': True},
    },
]


class Command(BaseCommand):
    help = "Free / Pro-Basic / Pro-Full tariflarini yaratadi (mavjudini tegmaydi)."

    def add_arguments(self, parser):
        parser.add_argument(
            '--reset',
            action='store_true',
            help="Mavjud tariflarni ham standart qiymatlarga QAYTARADI. "
                 "Admin qo'lda kiritgan narx va cheklovlar yo'qoladi.",
        )

    def handle(self, *args, **options):
        created, updated, skipped = 0, 0, 0

        for spec in PLANS:
            code = spec['code']
            plan = Plan.objects.filter(code=code).first()

            if plan is None:
                Plan.objects.create(**spec)
                created += 1
                self.stdout.write(self.style.SUCCESS(f"  + {spec['name']} yaratildi"))
            elif options['reset']:
                for field, value in spec.items():
                    setattr(plan, field, value)
                plan.save()
                updated += 1
                self.stdout.write(self.style.WARNING(f"  ~ {spec['name']} qayta yozildi"))
            else:
                skipped += 1
                self.stdout.write(f"  = {spec['name']} allaqachon mavjud (tegilmadi)")

        invalidate_free_plan_cache()
        self.stdout.write(self.style.SUCCESS(
            f"Tayyor. Yaratildi: {created}, yangilandi: {updated}, tegilmadi: {skipped}."
        ))
