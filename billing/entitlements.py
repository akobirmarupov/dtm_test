from __future__ import annotations

from dataclasses import dataclass, field
from datetime import timedelta

from django.core.cache import cache



GUEST_QUESTION_COUNT = 20

FREE_DAILY_TOPIC_LIMIT = 4
FREE_MAX_QUESTION_COUNT = 60

PLAN_CACHE_KEY = 'billing:plan:code:free'
PLAN_CACHE_TTL = 300


@dataclass(frozen=True)
class Entitlements:
    tier: str
    plan_id: int | None = None
    plan_code: str = ''
    plan_name: str = ''
    is_authenticated: bool = False
    is_pro: bool = False

    daily_topic_limit: int | None = FREE_DAILY_TOPIC_LIMIT
    max_question_count: int = FREE_MAX_QUESTION_COUNT
    can_choose_question_count: bool = True
    can_use_exam_mode: bool = True

    can_view_results: bool = True
    can_persist_progress: bool = True

    can_view_explanations: bool = False
    explanation_limit_per_day: int | None = 0

    # Bo'sh (None) = cheksiz, 0 = imkoniyat yopiq.
    mistake_test_daily_limit: int | None = None
    review_cards_daily_limit: int | None = None

    can_view_analytics: bool = True
    history_days: int | None = None
    streak_freezes_per_month: int | None = 1

    features: dict = field(default_factory=dict)

    @property
    def is_guest(self) -> bool:
        return self.tier == 'guest'

    @property
    def has_unlimited_topics(self) -> bool:
        return self.daily_topic_limit is None

    @property
    def can_build_mistake_tests(self) -> bool:
        return self.mistake_test_daily_limit != 0

    @property
    def can_use_review_cards(self) -> bool:
        return self.review_cards_daily_limit != 0

    def feature(self, name, default=None):
        return (self.features or {}).get(name, default)

    def as_dict(self) -> dict:
        """API javoblarida foydalanuvchiga ko'rsatiladigan ko'rinish."""
        return {
            'tier': self.tier,
            'plan_code': self.plan_code or None,
            'plan_name': self.plan_name or None,
            'is_pro': self.is_pro,
            'daily_topic_limit': self.daily_topic_limit,
            'max_question_count': self.max_question_count,
            'can_choose_question_count': self.can_choose_question_count,
            'can_use_exam_mode': self.can_use_exam_mode,
            'can_view_results': self.can_view_results,
            'can_view_explanations': self.can_view_explanations,
            'explanation_limit_per_day': self.explanation_limit_per_day,
            'mistake_test_daily_limit': self.mistake_test_daily_limit,
            'review_cards_daily_limit': self.review_cards_daily_limit,
            'can_view_analytics': self.can_view_analytics,
            'history_days': self.history_days,
            'streak_freezes_per_month': self.streak_freezes_per_month,
            'features': self.features or {},
        }


GUEST_ENTITLEMENTS = Entitlements(
    tier='guest',
    is_authenticated=False,
    daily_topic_limit=None,
    max_question_count=GUEST_QUESTION_COUNT,
    can_choose_question_count=False,
    can_use_exam_mode=False,
    can_view_results=False,
    can_persist_progress=False,
    can_view_explanations=False,
    explanation_limit_per_day=0,
    # Guestda hech narsa saqlanmaydi — xatolar banki ham, takrorlash ham yo'q.
    mistake_test_daily_limit=0,
    review_cards_daily_limit=0,
    can_view_analytics=False,
    history_days=0,
    streak_freezes_per_month=0,
)


def _free_plan():
    cached = cache.get(PLAN_CACHE_KEY)
    if cached is not None:
        return cached or None

    from billing.models import Plan

    plan = Plan.objects.filter(code='free', is_active=True).first()
    cache.set(PLAN_CACHE_KEY, plan or False, PLAN_CACHE_TTL)
    return plan


def entitlements_from_plan(plan, tier=None) -> Entitlements:
    """Tarif -> huquqlar.

    Cheklovlar FAQAT tarifning o'z maydonlaridan olinadi. `is_pro` bu yerda
    hech narsani bekor qilmaydi — u shunchaki "pullik tarif" degan belgi.
    Shuning uchun admin xohlagancha tarif yaratib (Basic, Pro, Premium,
    Premium Max...), har biriga o'z limitini qo'ya oladi: bo'sh qoldirilgan
    maydon — cheksiz.
    """
    return Entitlements(
        tier=tier or ('pro' if plan.is_pro else 'free'),
        plan_id=plan.id,
        plan_code=plan.code or '',
        plan_name=plan.name,
        is_authenticated=True,
        is_pro=plan.is_pro,
        daily_topic_limit=plan.daily_topic_limit,
        max_question_count=plan.max_question_count or FREE_MAX_QUESTION_COUNT,
        can_choose_question_count=plan.can_choose_question_count,
        can_use_exam_mode=plan.can_use_exam_mode,
        can_view_results=True,
        can_persist_progress=True,
        can_view_explanations=plan.can_view_explanations,
        explanation_limit_per_day=(
            None if plan.can_view_explanations and plan.explanation_limit_per_day is None
            else (plan.explanation_limit_per_day if plan.can_view_explanations else 0)
        ),
        mistake_test_daily_limit=plan.mistake_test_daily_limit,
        review_cards_daily_limit=plan.review_cards_daily_limit,
        can_view_analytics=plan.can_view_analytics,
        history_days=plan.history_days,
        streak_freezes_per_month=plan.streak_freezes_per_month,
        features=plan.features or {},
    )


def free_entitlements() -> Entitlements:
    plan = _free_plan()
    if plan is not None:
        return entitlements_from_plan(plan, tier='free')

    return Entitlements(
        tier='free',
        plan_code='free',
        plan_name='Bepul',
        is_authenticated=True,
        is_pro=False,
        daily_topic_limit=FREE_DAILY_TOPIC_LIMIT,
        max_question_count=FREE_MAX_QUESTION_COUNT,
        can_view_explanations=False,
        explanation_limit_per_day=0,
    )


def entitlements_for(user, now=None) -> Entitlements:

    if user is None or not getattr(user, 'is_authenticated', False):
        return GUEST_ENTITLEMENTS

    from billing.services import active_subscription

    subscription = active_subscription(user, now)
    if subscription is None:
        return free_entitlements()

    return entitlements_from_plan(subscription.plan)


def history_cutoff(entitlements, now=None):
    """Natijalar tarixining eng eski ko'rinadigan sanasi.

    `None` qaytsa — butun tarix ochiq. Tarif `history_days=0` bo'lsa, tarix
    umuman ko'rinmaydi (hozirgi vaqt qaytadi).
    """
    from django.utils import timezone

    days = entitlements.history_days
    if days is None:
        return None

    now = now or timezone.now()
    return now - timedelta(days=days)


def entitlements_for_request(request) -> Entitlements:
    cached = getattr(request, '_entitlements', None)
    if cached is None:
        cached = entitlements_for(getattr(request, 'user', None))
        request._entitlements = cached
    return cached


def invalidate_free_plan_cache():
    cache.delete(PLAN_CACHE_KEY)
