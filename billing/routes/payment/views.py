import logging
from datetime import timedelta

from django.utils import timezone
from django.db import transaction, IntegrityError
from django.conf import settings
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.exceptions import NotFound
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema
from rest_framework.permissions import IsAuthenticated

from common.permissions import IsAdmin
from common.pagination import StandardResultsPagination
from common.throttles import SubscriptionRequestThrottle
from billing.models import Payment, Subscription, Plan
from billing.filters import PaymentFilter
from billing.routes.serializers import PaymentSerializer, SubscriptionSerializer


logger = logging.getLogger(__name__)


class PaymentCreateListAPIView(APIView):
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_class = PaymentFilter
    pagination_class = StandardResultsPagination
    throttle_classes = [SubscriptionRequestThrottle]


    @extend_schema(responses=PaymentSerializer(many=True))
    def get(self, request):
        if request.user.role == 'admin':
            queryset = Payment.objects.all()
        else:
            queryset = Payment.objects.filter(user=request.user)

        queryset = queryset.select_related('user', 'subscription', 'subscription__plan').order_by('-created_at')
        queryset = PaymentFilter(request.GET, queryset=queryset).qs

        paginator = self.pagination_class()
        page = paginator.paginate_queryset(queryset, request, view=self)
        serializer = PaymentSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)


    @extend_schema(request={"application/json": {"type": "object", "properties": {"plan_id": {"type": "integer"}}}})
    def post(self, request):
        plan_id = request.data.get('plan_id') or request.data.get('plan')
        
        if not plan_id:
            return Response(
                {"detail": "plan_id kerak"},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            plan = Plan.objects.get(pk=plan_id)
        except Plan.DoesNotExist:
            return Response(
                {"detail": "Tarif topilmadi"},
                status=status.HTTP_404_NOT_FOUND
            )

        pending_payment = Payment.objects.filter(
            user=request.user,
            status='pending'
        ).first()
        if pending_payment:
            return Response(
                {"detail": "Sizning arizangiz allaqachon ko'rib chiqilmoqda. "
                          "Iltimos admin javobini kuting."},
                status=status.HTTP_400_BAD_REQUEST
            )

        now = timezone.now()
        active_subscription = Subscription.objects.filter(
            user=request.user,
            status='active',
            expires_at__gt=now
        ).first()
        if active_subscription:
            return Response(
                {"detail": "Sizda allaqachon aktiv obuna mavjud"},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            with transaction.atomic():
                subscription = Subscription.objects.create(
                    user=request.user,
                    plan=plan,
                    status='pending',
                    starts_at=timezone.now(),
                    expires_at=timezone.now()
                )

                payment = Payment.objects.create(
                    user=request.user,
                    subscription=subscription,
                    provider=Payment.Provider.MANUAL,
                    provider_transaction_id=f"ariza_{request.user.id}_{timezone.now().timestamp()}",
                    amount=plan.price,
                    status=Payment.Status.PENDING,
                )

                logger.info(
                    f"Subscription request created: user_id={request.user.id}, "
                    f"plan_id={plan.id}, plan_name={plan.name}, "
                    f"payment_id={payment.id}, subscription_id={subscription.id}"
                )

            serializer = PaymentSerializer(payment)
            return Response(
                {
                    "ariza": serializer.data,
                    "message": "Arizangiz qabul qilindi! Quyidagi Telegram havola orqali "
                              "adminlarimiz bilan bog'laning va to'lovni amalga oshiring — "
                              "admin tasdiqlagach obunangiz avtomatik faollashadi.",
                    "admin_telegram": settings.ADMIN_TELEGRAM_LINK
                },
                status=status.HTTP_201_CREATED
            )

        except IntegrityError:
            logger.error(f"IntegrityError while creating payment for user_id={request.user.id}")
            return Response(
                {"detail": "Arizani yaratishda xatolik yuz berdi"},
                status=status.HTTP_400_BAD_REQUEST
            )


class PaymentApproveAPIView(APIView):
    permission_classes = [IsAdmin]


    @extend_schema(responses=SubscriptionSerializer)
    def patch(self, request, pk):
        try:
            payment = Payment.objects.select_related('user', 'subscription__plan').get(pk=pk)
        except Payment.DoesNotExist:
            raise NotFound("Ariza topilmadi")

        if payment.status != Payment.Status.PENDING:
            return Response(
                {"detail": "Bu ariza allaqachon ko'rib chiqilgan"},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            with transaction.atomic():
                payment.status = Payment.Status.SUCCESS
                payment.save(update_fields=['status'])

                now = timezone.now()

                subscription = payment.subscription
                if not subscription:
                    return Response(
                        {"detail": "Subscription topilmadi"},
                        status=status.HTTP_500_INTERNAL_SERVER_ERROR
                    )

                subscription.status = 'active'
                subscription.starts_at = now
                subscription.expires_at = now + timedelta(days=subscription.plan.duration_days)
                subscription.save(update_fields=['status', 'starts_at', 'expires_at'])

                logger.info(
                    f"Payment approved: payment_id={payment.id}, user_id={payment.user.id}, "
                    f"subscription_id={subscription.id}, approved_by={request.user.id}"
                )

                from billing.routes.serializers import SubscriptionSerializer
                serializer = SubscriptionSerializer(subscription)
                return Response(serializer.data, status=status.HTTP_200_OK)

        except IntegrityError:
            logger.error(f"IntegrityError while approving payment_id={pk}")
            return Response(
                {"detail": "Arizani tasdiqlashda xatolik yuz berdi"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class PaymentRejectAPIView(APIView):
    permission_classes = [IsAdmin]

    @extend_schema()
    def patch(self, request, pk):
        try:
            payment = Payment.objects.select_related('user', 'subscription').get(pk=pk)
        except Payment.DoesNotExist:
            raise NotFound("Ariza topilmadi")

        if payment.status != Payment.Status.PENDING:
            return Response(
                {"detail": "Bu ariza allaqachon ko'rib chiqilgan"},
                status=status.HTTP_400_BAD_REQUEST
            )

        reason = request.data.get('reason', '') if request.data else ''

        try:
            with transaction.atomic():
                payment.status = Payment.Status.FAILED
                payment.save(update_fields=['status'])

                logger.info(
                    f"Payment rejected: payment_id={payment.id}, user_id={payment.user.id}, "
                    f"reason={reason}, rejected_by={request.user.id}"
                )

            return Response(
                {"detail": "Ariza rad etildi"},
                status=status.HTTP_200_OK
            )

        except IntegrityError:
            logger.error(f"IntegrityError while rejecting payment_id={pk}")
            return Response(
                {"detail": "Arizani rad etishda xatolik yuz berdi"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class PaymentInfoAPIView(APIView):
    """
    GET /billing/payments/info/

    Foydalanuvchi biror tarifda "Obuna" tugmasini bosganda, "Ariza berish"
    tugmasidan oldin ko'rsatiladigan tushuntirish matni va admin Telegram
    havolasi. Hozircha banklar bilan integratsiya yo'q — to'lov qo'lda,
    admin bilan Telegram orqali kelishilgan holda amalga oshiriladi.
    """
    permission_classes = [IsAuthenticated]

    @extend_schema(responses={200: dict}, tags=['Payment'])
    def get(self, request):
        return Response(
            {
                "message": "Obunani faollashtirmoqchi bo'lsangiz, adminlarimiz bilan "
                           "Telegram orqali bog'laning va obunani faollashtiring. "
                           "\"Ariza berish\" tugmasini bosing — Telegram havolasi chiqadi.",
                "admin_telegram": settings.ADMIN_TELEGRAM_LINK,
            },
            status=status.HTTP_200_OK,
        )
