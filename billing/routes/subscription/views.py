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

from billing.filters import SubscriptionFilter
from billing.models import Subscription
from billing.routes.serializers import (
    CurrentSubscriptionSerializer,
    DetailSerializer,
    EligibilityOverviewSerializer,
    SubscriptionSerializer,
)
from billing.services import active_subscription, eligibility_overview, pending_payment
from billing.telegram import contact_payload
from common.i18n import resolve_language
from common.models import Role
from common.pagination import StandardResultsPagination

logger = logging.getLogger('billing')


# `SubscriptionFilter` qo'lda qo'llaniladi (bu oddiy APIView, `queryset` atributi yo'q),
# shuning uchun drf-spectacular filtrlarni o'zi topa olmaydi — quyida qo'lda beriladi.
SUBSCRIPTION_FILTER_PARAMETERS = [
    OpenApiParameter('user', OpenApiTypes.INT),
    OpenApiParameter('plan', OpenApiTypes.INT),
    OpenApiParameter('status', OpenApiTypes.STR, enum=Subscription.Status.values),
    OpenApiParameter('starts_at_after', OpenApiTypes.DATETIME),
    OpenApiParameter('starts_at_before', OpenApiTypes.DATETIME),
    OpenApiParameter('expires_at_after', OpenApiTypes.DATETIME),
    OpenApiParameter('expires_at_before', OpenApiTypes.DATETIME),
]


def serializer_context(request):
    return {'request': request, 'language': resolve_language(request)}


class SubscriptionListAPIView(APIView):
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_class = SubscriptionFilter
    pagination_class = StandardResultsPagination

    @extend_schema(
        parameters=SUBSCRIPTION_FILTER_PARAMETERS,
        filters=False,
        responses=SubscriptionSerializer(many=True),
        tags=['Subscription'],
    )
    def get(self, request):
        if request.user.role == Role.ADMIN:
            queryset = Subscription.objects.all()
        else:
            queryset = Subscription.objects.filter(user=request.user)

        queryset = queryset.select_related('user', 'plan').order_by('-created_at')
        queryset = SubscriptionFilter(request.GET, queryset=queryset).qs

        paginator = self.pagination_class()
        page = paginator.paginate_queryset(queryset, request, view=self)
        serializer = SubscriptionSerializer(
            page, many=True, context=serializer_context(request)
        )
        return paginator.get_paginated_response(serializer.data)


class SubscriptionCurrentAPIView(APIView):
    """GET /billing/subscriptions/current/

    Javob shakli obuna bor-yo'qligiga qaramay BIR XIL bo'ladi — mobil
    mijozlar tipni bir marta e'lon qilib ishlatishi uchun.
    """

    permission_classes = [IsAuthenticated]

    @extend_schema(responses={200: CurrentSubscriptionSerializer}, tags=['Subscription'])
    def get(self, request):
        context = serializer_context(request)
        subscription = active_subscription(request.user)
        pending = pending_payment(request.user)

        payload = {
            'has_active_subscription': subscription is not None,
            'subscription': subscription,
            'pending_request': pending,
        }
        return Response(
            CurrentSubscriptionSerializer(payload, context=context).data,
            status=status.HTTP_200_OK,
        )


class SubscriptionEligibilityAPIView(APIView):
    """GET /billing/subscriptions/eligibility/

    Tarif ekrani uchun bitta so'rov: har bir tarif yonida "Ariza yuborish"
    tugmasi faolmi, faol bo'lmasa nega va qachondan boshlab mumkin.
    """

    permission_classes = [IsAuthenticated]

    @extend_schema(
        responses={200: EligibilityOverviewSerializer},
        tags=['Subscription'],
        description="Har bir tarif bo'yicha: ariza yuborish mumkinmi, "
                    "upgrade hisoblanadimi, mumkin bo'lmasa qachongacha kutiladi.",
    )
    def get(self, request):
        context = serializer_context(request)
        current, pending, rows = eligibility_overview(request.user)

        payload = {
            'has_active_subscription': current is not None,
            'current_subscription': current,
            'pending_request': pending,
            'plans': [
                {
                    'plan': plan,
                    'can_request': verdict['can_request'],
                    'is_upgrade': verdict['is_upgrade'],
                    'reason_code': verdict['reason_code'],
                    'reason': verdict['reason'],
                    'available_at': verdict['available_at'],
                }
                for plan, verdict in rows
            ],
            'contact': contact_payload(pending),
        }
        return Response(
            EligibilityOverviewSerializer(payload, context=context).data,
            status=status.HTTP_200_OK,
        )


class SubscriptionCancelAPIView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        request=None,
        responses={
            200: SubscriptionSerializer,
            400: DetailSerializer,
            403: DetailSerializer,
        },
        tags=['Subscription'],
    )
    def patch(self, request, pk):
        try:
            subscription = Subscription.objects.select_related('user', 'plan').get(pk=pk)
        except Subscription.DoesNotExist:
            raise NotFound("Obuna topilmadi")

        if subscription.user != request.user and request.user.role != Role.ADMIN:
            return Response(
                {"detail": "Bu obunani bekor qila olmaysiz"},
                status=status.HTTP_403_FORBIDDEN,
            )

        if subscription.status in (
            Subscription.Status.CANCELLED, Subscription.Status.EXPIRED
        ):
            return Response(
                {"detail": "Bu obuna allaqachon yopilgan."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        with transaction.atomic():
            subscription.status = Subscription.Status.CANCELLED
            subscription.save(update_fields=['status', 'updated_at'])

            logger.info(
                f"Subscription cancelled: user_id={subscription.user_id}, "
                f"subscription_id={subscription.id}, cancelled_by={request.user.id}"
            )

        return Response(
            SubscriptionSerializer(subscription, context=serializer_context(request)).data,
            status=status.HTTP_200_OK,
        )
