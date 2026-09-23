"""Kunlik limitlarni tekshirish — barcha bo'limlar uchun yagona qoida.

Qoida hamma joyda bir xil:

* limit ``None``  -> cheksiz;
* limit ``0``     -> imkoniyat yopiq (tarifda umuman yo'q);
* limit ``N``     -> kuniga N marta, ertasi kuni 00:00 da yangilanadi.

Shuning uchun tarifda maydonni bo'sh qoldirish «cheksiz», 0 qo'yish esa
«bu tarifda yo'q» degani bo'ladi — admin panelda ham shunday yozilgan.
"""

from __future__ import annotations

from django.db import IntegrityError, transaction
from django.db.models import F, Sum
from django.utils import timezone

from common.models import DailyFeatureUsage

Feature = DailyFeatureUsage.Feature


def used_today(user, feature, date=None) -> int:
    if user is None or not getattr(user, 'is_authenticated', False):
        return 0
    row = DailyFeatureUsage.objects.filter(
        user=user, feature=feature, date=date or timezone.localdate()
    ).values_list('count', flat=True).first()
    return row or 0


def used_this_month(user, feature, today=None) -> int:
    if user is None or not getattr(user, 'is_authenticated', False):
        return 0
    today = today or timezone.localdate()
    total = DailyFeatureUsage.objects.filter(
        user=user, feature=feature,
        date__year=today.year, date__month=today.month,
    ).aggregate(total=Sum('count'))['total']
    return total or 0


def consume(user, feature, amount=1, date=None) -> int:
    """Hisoblagichni oshiradi va yangi qiymatni qaytaradi.

    `get_or_create` + `F()` — ikkita parallel so'rov bitta qiymatni bosib
    ketmasligi uchun.
    """
    if user is None or not getattr(user, 'is_authenticated', False):
        return 0

    date = date or timezone.localdate()
    try:
        with transaction.atomic():
            usage, created = DailyFeatureUsage.objects.get_or_create(
                user=user, feature=feature, date=date, defaults={'count': amount}
            )
    except IntegrityError:
        created, usage = False, DailyFeatureUsage.objects.get(
            user=user, feature=feature, date=date
        )

    if created:
        return usage.count

    DailyFeatureUsage.objects.filter(pk=usage.pk).update(count=F('count') + amount)
    usage.refresh_from_db(fields=['count'])
    return usage.count


def consume_if_limited(user, feature, limit, amount=1) -> int:
    """Faqat limit qo'yilgan tarifda sanaydi.

    Cheksiz tarifda hisoblagich hech narsaga ta'sir qilmaydi — har so'rovda
    bazaga yozish esa behuda yuk.
    """
    if limit is None:
        return 0
    return consume(user, feature, amount)


def daily_limit_access(user, feature, limit, *, closed_detail, reached_detail,
                       code, used=None) -> dict:
    """Limit holatini API javobiga tayyor shaklda qaytaradi.

    `closed_detail` — tarifda umuman yo'q (limit 0);
    `reached_detail` — bor, lekin bugungi hisob tugagan. Ikkalasi ham
    `{limit}` va `{used}` o'rniga qiymat qo'yadigan format satri bo'lishi mumkin.
    """
    from testengine.access import next_reset_at

    reset_at = next_reset_at()

    if limit is None:
        return {
            'allowed': True, 'code': 'ok', 'detail': '',
            'limit': None, 'used': 0, 'remaining': None,
            'reset_at': reset_at, 'upgrade_required': False,
        }

    used = used_today(user, feature) if used is None else used

    if limit == 0:
        return {
            'allowed': False, 'code': 'upgrade_required',
            'detail': closed_detail,
            'limit': 0, 'used': used, 'remaining': 0,
            'reset_at': reset_at, 'upgrade_required': True,
        }

    remaining = max(limit - used, 0)
    allowed = used < limit

    return {
        'allowed': allowed,
        'code': 'ok' if allowed else code,
        'detail': '' if allowed else reached_detail.format(limit=limit, used=used),
        'limit': limit, 'used': used, 'remaining': remaining,
        'reset_at': reset_at, 'upgrade_required': not allowed,
    }


def limit_payload(access: dict) -> dict:
    """403 javobining tanasi."""
    return {
        'detail': access['detail'],
        'code': access['code'],
        'limit': access['limit'],
        'used_today': access['used'],
        'remaining_today': access['remaining'],
        'reset_at': access['reset_at'],
        'upgrade_required': access['upgrade_required'],
    }
