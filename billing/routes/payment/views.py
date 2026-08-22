"""Obuna ARIZASI oqimi.

Foydalanuvchi tarifni tanlaydi -> "Ariza yuborish" -> ariza bazaga tushadi,
adminga Telegram xabar ketadi va mijozga "Admin bilan bog'lanish" tugmasi
uchun havola qaytadi. Admin tasdiqlagach obuna faollashadi.
"""

from __future__ import annotations

import logging

from django.db import transaction
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import status
from rest_framework.exceptions import NotFound
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from billing.filters import PaymentFilter
from billing.models import Payment, Plan
from billing.routes.serializers import (
    DetailSerializer,
    PaymentInfoSerializer,
    PaymentRejectRequestSerializer,
    PaymentSerializer,
    SubscriptionRequestResponseSerializer,
    SubscriptionRequestSerializer,
    SubscriptionSerializer,
)
from billing.services import (
    SubscriptionError,
    approve_payment,
    cancel_own_request,
    create_subscription_request,
    reject_payment,
)
from billing.telegram import admin_link, contact_payload
from common.i18n import resolve_language
from common.models import Role
from common.pagination import StandardResultsPagination
from common.permissions import IsAdmin
from common.throttles import SubscriptionRequestThrottle
from notifications.models import NotificationLog

logger = logging.getLogger('billing')


PAYMENT_FILTER_PARAMETERS = [
    OpenApiParameter('user', OpenApiTypes.INT),
    OpenApiParameter('status', OpenApiTypes.STR, enum=Payment.Status.values),
    OpenApiParameter('provider', OpenApiTypes.STR, enum=Payment.Provider.values),
    OpenApiParameter('plan', OpenApiTypes.INT),
    OpenApiParameter('amount_min', OpenApiTypes.NUMBER),
    OpenApiParameter('amount_max', OpenApiTypes.NUMBER),
    OpenApiParameter('created_at_after', OpenApiTypes.DATETIME),
    OpenApiParameter('created_at_before', OpenApiTypes.DATETIME),
]


def serializer_context(request):
    return {'request': request, 'language': resolve_language(request)}


def subscription_error_response(exc: SubscriptionError, status_code=status.HTTP_400_BAD_REQUEST):
    body = {'detail': exc.message, 'code': exc.code}
    if exc.available_at:
        body['available_at'] = exc.available_at
    return Response(body, status=status_code)


class PaymentCreateListAPIView(APIView):
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_class = PaymentFilter
    pagination_class = StandardResultsPagination
    throttle_classes = [SubscriptionRequestThrottle]

    @extend_schema(
        parameters=PAYMENT_FILTER_PARAMETERS,
        filters=False,
        responses=PaymentSerializer(many=True),
        tags=['Payment'],
        description="Arizalar ro'yxati. Oddiy foydalanuvchi faqat o'zinikini, "
                    "admin hammasini ko'radi (`?status=pending` — ko'rib "
                    "chiqilishi kerak bo'lganlari).",
    )
    def get(self, request):
        if request.user.role == Role.ADMIN:
            queryset = Payment.objects.all()
        else:
            queryset = Payment.objects.filter(user=request.user)

        queryset = queryset.select_related(
            'user', 'plan', 'subscription', 'subscription__plan'
        ).order_by('-created_at')
        queryset = PaymentFilter(request.GET, queryset=queryset).qs

        paginator = self.pagination_class()
        page = paginator.paginate_queryset(queryset, request, view=self)
        serializer = PaymentSerializer(page, many=True, context=serializer_context(request))
        return paginator.get_paginated_response(serializer.data)

    @extend_schema(
        request=SubscriptionRequestSerializer,
        responses={
            201: SubscriptionRequestResponseSerializer,
            400: DetailSerializer,
            404: DetailSerializer,
        },
        tags=['Payment'],
        description=(
            "Tarifga ARIZA yuborish.\n\n"
            "* Bepul (0 so'm) tarif — darhol faollashadi, admin kutilmaydi.\n"
            "* Pullik tarif — ariza `pending` bo'lib qoladi, adminga Telegram "
            "xabar ketadi, javobda \"Admin bilan bog'lanish\" havolasi keladi.\n"
            "* Aktiv obuna davomida ayni yoki arzonroq tarifni qayta olib "
            "bo'lmaydi (400, `code=already_active`/`downgrade_blocked`), "
            "qimmatroq tarifga esa o'tish mumkin."
        ),
    )
    def post(self, request):
        serializer = SubscriptionRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        try:
            plan = Plan.objects.get(pk=data['plan_id'])
        except (Plan.DoesNotExist, ValueError, TypeError):
            return Response({"detail": "Tarif topilmadi"}, status=status.HTTP_404_NOT_FOUND)

        try:
            payment, subscription, auto_activated = create_subscription_request(
                user=request.user,
                plan=plan,
                contact_phone=data.get('contact_phone', ''),
                contact_telegram=data.get('contact_telegram', ''),
                note=data.get('note', ''),
            )
        except SubscriptionError as exc:
            return subscription_error_response(exc)

        if auto_activated:
            message = (
                f"«{plan.name}» tarifi faollashtirildi. Yaxshi natijalar tilaymiz!"
            )
        else:
            message = (
                "Arizangiz qabul qilindi! Quyidagi Telegram havola orqali "
                "adminlarimiz bilan bog'laning va to'lovni amalga oshiring — "
                "admin tasdiqlagach obunangiz faollashadi."
            )
            self._notify_admin(payment.id)

        context = serializer_context(request)
        payload = {
            'ariza': payment,
            'subscription': subscription,
            'auto_activated': auto_activated,
            'message': message,
            'admin_telegram': admin_link(),
            'contact': contact_payload(None if auto_activated else payment),
        }
        return Response(
            SubscriptionRequestResponseSerializer(payload, context=context).data,
            status=status.HTTP_201_CREATED,
        )

    @staticmethod
    def _notify_admin(payment_id):
        """Telegram xabarini tranzaksiya yopilgandan keyin navbatga qo'yamiz."""
        from billing.tasks import notify_admin_about_request_task

        def _dispatch():
            try:
                notify_admin_about_request_task.delay(payment_id)
            except Exception:
                # Broker ishlamasa ham ariza bazada qoladi va admin panelda
                # ko'rinadi — foydalanuvchiga xato qaytarmaymiz.
                logger.exception(
                    "Arizani Telegram navbatiga qo'yib bo'lmadi: payment_id=%s", payment_id
                )

        transaction.on_commit(_dispatch)


class PaymentDetailAPIView(APIView):
    """GET /billing/payments/<id>/ — bitta ariza."""

    permission_classes = [IsAuthenticated]

    def get_object(self, pk, user):
        try:
            payment = Payment.objects.select_related(
                'user', 'plan', 'subscription__plan'
            ).get(pk=pk)
        except Payment.DoesNotExist:
            raise NotFound("Ariza topilmadi")

        if payment.user_id != user.id and user.role != Role.ADMIN:
            raise NotFound("Ariza topilmadi")
        return payment

    @extend_schema(responses={200: PaymentSerializer}, tags=['Payment'])
    def get(self, request, pk):
        payment = self.get_object(pk, request.user)
        return Response(
            PaymentSerializer(payment, context=serializer_context(request)).data
        )


class PaymentCancelAPIView(APIView):
    """PATCH /billing/payments/<id>/cancel/ — foydalanuvchi o'z arizasini
    qaytarib oladi (fikridan qaytdi yoki boshqa tarif tanlamoqchi)."""

    permission_classes = [IsAuthenticated]

    @extend_schema(
        request=None,
        responses={200: PaymentSerializer, 400: DetailSerializer},
        tags=['Payment'],
    )
    def patch(self, request, pk):
        try:
            payment = Payment.objects.get(pk=pk, user=request.user)
        except Payment.DoesNotExist:
            raise NotFound("Ariza topilmadi")

        try:
            payment = cancel_own_request(payment)
        except SubscriptionError as exc:
            return subscription_error_response(exc)

        return Response(
            PaymentSerializer(payment, context=serializer_context(request)).data
        )


class PaymentApproveAPIView(APIView):
    """PATCH /billing/payments/<id>/approve/ — admin tasdiqlaydi."""

    permission_classes = [IsAdmin]

    @extend_schema(
        request=None,
        responses={200: SubscriptionSerializer, 400: DetailSerializer},
        tags=['Payment'],
    )
    def patch(self, request, pk):
        try:
            payment = Payment.objects.get(pk=pk)
        except Payment.DoesNotExist:
            raise NotFound("Ariza topilmadi")

        try:
            payment, subscription = approve_payment(payment, request.user)
        except SubscriptionError as exc:
            return subscription_error_response(exc)

        self._notify_user(payment, subscription)

        return Response(
            SubscriptionSerializer(subscription, context=serializer_context(request)).data,
            status=status.HTTP_200_OK,
        )

    @staticmethod
    def _notify_user(payment, subscription):
        NotificationLog.objects.create(
            user_id=payment.user_id,
            type=NotificationLog.Type.SUBSCRIPTION_APPROVED,
            message=(
                f"«{subscription.plan.name}» obunangiz faollashtirildi! "
                f"Amal qilish muddati: {subscription.expires_at:%d.%m.%Y}."
            ),
        )


class PaymentRejectAPIView(APIView):
    """PATCH /billing/payments/<id>/reject/ — admin rad etadi."""

    permission_classes = [IsAdmin]

    @extend_schema(
        request=PaymentRejectRequestSerializer,
        responses={200: PaymentSerializer, 400: DetailSerializer},
        tags=['Payment'],
        description="Rad etish sababi `reason` maydonida yuboriladi va "
                    "foydalanuvchiga bildirishnoma sifatida yetkaziladi.",
    )
    def patch(self, request, pk):
        try:
            payment = Payment.objects.get(pk=pk)
        except Payment.DoesNotExist:
            raise NotFound("Ariza topilmadi")

        reason = ''
        if isinstance(request.data, dict):
            reason = str(request.data.get('reason') or '').strip()

        try:
            payment = reject_payment(payment, request.user, reason)
        except SubscriptionError as exc:
            return subscription_error_response(exc)

        NotificationLog.objects.create(
            user_id=payment.user_id,
            type=NotificationLog.Type.SUBSCRIPTION_REJECTED,
            message=(
                f"Obuna arizangiz rad etildi. {reason}".strip()
                or "Obuna arizangiz rad etildi. Admin bilan bog'laning."
            ),
        )

        return Response(
            PaymentSerializer(payment, context=serializer_context(request)).data,
            status=status.HTTP_200_OK,
        )


class PaymentInfoAPIView(APIView):
    """GET /billing/payments/info/

    "Obuna" tugmasidan keyin, "Ariza yuborish" dan oldin ko'rsatiladigan
    tushuntirish va admin Telegram havolasi.
    """

    permission_classes = [IsAuthenticated]

    @extend_schema(responses={200: PaymentInfoSerializer}, tags=['Payment'])
    def get(self, request):
        return Response(
            {
                "message": "Obunani faollashtirmoqchi bo'lsangiz, tarifni tanlab "
                           "\"Ariza yuborish\" tugmasini bosing. So'ng adminlarimiz "
                           "bilan Telegram orqali bog'lanib to'lovni amalga oshiring — "
                           "admin tasdiqlagach obuna faollashadi.",
                "admin_telegram": admin_link(),
                "contact": contact_payload(),
            },
            status=status.HTTP_200_OK,
        )
