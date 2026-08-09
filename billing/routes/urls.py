from django.urls import path

from billing.routes.plan.views import PlanCreateListAPIView, PlanDetailAPIView
from billing.routes.subscription.views import SubscriptionListAPIView, SubscriptionCurrentAPIView, SubscriptionCancelAPIView
from billing.routes.payment.views import PaymentCreateListAPIView,PaymentApproveAPIView, PaymentRejectAPIView


urlpatterns = [
    # Plan
    path('plan/', PlanCreateListAPIView.as_view(), name='plan-list'),
    path('plan/<int:pk>/', PlanDetailAPIView.as_view(), name='plam-detail'),

    # Subscription
    path('subscriptions/', SubscriptionListAPIView.as_view(), name='subscription-list'),
    path('subscriptions/current/', SubscriptionCurrentAPIView.as_view(), name='subscription-current'),
    path('subscriptions/<int:pk>/cancel/', SubscriptionCancelAPIView.as_view(), name='subscription-cancel'),

    # Payment (Ariza)
    path('payments/', PaymentCreateListAPIView.as_view(), name='payment-list-create'),
    path('payments/<int:pk>/approve/', PaymentApproveAPIView.as_view(), name='payment-approve'),
    path('payments/<int:pk>/reject/', PaymentRejectAPIView.as_view(), name='payment-reject'),
]
