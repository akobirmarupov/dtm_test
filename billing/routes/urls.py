from django.urls import path

from billing.routes.payment.views import (
    PaymentApproveAPIView,
    PaymentCancelAPIView,
    PaymentCreateListAPIView,
    PaymentDetailAPIView,
    PaymentInfoAPIView,
    PaymentRejectAPIView,
)
from billing.routes.plan.views import PlanCreateListAPIView, PlanDetailAPIView
from billing.routes.subscription.views import (
    SubscriptionCancelAPIView,
    SubscriptionCurrentAPIView,
    SubscriptionEligibilityAPIView,
    SubscriptionListAPIView,
)

urlpatterns = [
    # Tariflar (0 so'm / 50 000 so'm / 70 000 so'm ...)
    path('plan/', PlanCreateListAPIView.as_view(), name='plan-list'),
    path('plan/<int:pk>/', PlanDetailAPIView.as_view(), name='plan-detail'),

    # Obunalar
    path('subscriptions/', SubscriptionListAPIView.as_view(), name='subscription-list'),
    path('subscriptions/current/', SubscriptionCurrentAPIView.as_view(), name='subscription-current'),
    path(
        'subscriptions/eligibility/',
        SubscriptionEligibilityAPIView.as_view(),
        name='subscription-eligibility',
    ),
    path('subscriptions/<int:pk>/cancel/', SubscriptionCancelAPIView.as_view(), name='subscription-cancel'),

    # Arizalar — hozircha Telegram orqali qo'lda tasdiqlanadi
    path('payments/info/', PaymentInfoAPIView.as_view(), name='payment-info'),
    path('payments/', PaymentCreateListAPIView.as_view(), name='payment-list-create'),
    path('payments/<int:pk>/', PaymentDetailAPIView.as_view(), name='payment-detail'),
    path('payments/<int:pk>/cancel/', PaymentCancelAPIView.as_view(), name='payment-cancel'),
    path('payments/<int:pk>/approve/', PaymentApproveAPIView.as_view(), name='payment-approve'),
    path('payments/<int:pk>/reject/', PaymentRejectAPIView.as_view(), name='payment-reject'),
]
