"""`Topic.available_question_count` ni noldan qayta hisoblaydi.

Signal `Question.save()` / `delete()` ga ulangan, lekin bulk operatsiyalar
(`bulk_create`, `queryset.update()`, `loaddata`, SQL import) signal
chaqirmaydi. Katta import qilingandan keyin shu buyruq ishga tushirilsin.
"""

from django.core.management.base import BaseCommand
from django.db.models import Count, Q

from catalog.models import Question, Topic


class Command(BaseCommand):
    help = "Mavzulardagi mavjud savollar sonini qayta hisoblaydi."

    def handle(self, *args, **options):
        counts = dict(
            Topic.objects.annotate(
                total=Count(
                    'questions',
                    filter=Q(
                        questions__status=Question.Status.PUBLISHED,
                        questions__is_active=True,
                    ),
                )
            ).values_list('id', 'total')
        )

        changed = []
        for topic in Topic.objects.only('id', 'available_question_count'):
            expected = counts.get(topic.id, 0)
            if topic.available_question_count != expected:
                topic.available_question_count = expected
                changed.append(topic)

        if changed:
            Topic.objects.bulk_update(changed, ['available_question_count'], batch_size=500)

        self.stdout.write(self.style.SUCCESS(
            f"Tekshirildi: {len(counts)} ta mavzu, yangilandi: {len(changed)} ta."
        ))
