import logging

from django.utils import timezone
from django.db import transaction
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.exceptions import NotFound
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema
from rest_framework.permissions import IsAuthenticated

from common.pagination import StandardResultsPagination
from billing.models import Subscription
from billing.filters import SubscriptionFilter
from billing.routes.serializers import SubscriptionSerializer


logger = logging.getLogger(__name__)


class SubscriptionListAPIView(APIView):
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_class = SubscriptionFilter
    pagination_class = StandardResultsPagination

    @extend_schema(responses=SubscriptionSerializer(many=True))
    def get(self, request):
        if request.user.role == 'admin':
            queryset = Subscription.objects.all()
        else:
            queryset = Subscription.objects.filter(user=request.user)

        queryset = queryset.select_related('user', 'plan').order_by('-created_at')
        queryset = SubscriptionFilter(request.GET, queryset=queryset).qs

        paginator = self.pagination_class()
        page = paginator.paginate_queryset(queryset, request, view=self)
        serializer = SubscriptionSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)


class SubscriptionCurrentAPIView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(responses=SubscriptionSerializer)
    def get(self, request):
        now = timezone.now()
        subscription = Subscription.objects.filter(
            user=request.user,
            status='active',
            expires_at__gt=now
        ).select_related('plan').first()

        if subscription:
            serializer = SubscriptionSerializer(subscription)
            return Response(serializer.data, status=status.HTTP_200_OK)
        else:
            return Response(
                {"has_active_subscription": False},
                status=status.HTTP_200_OK
            )


class SubscriptionCancelAPIView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(responses=SubscriptionSerializer)
    def patch(self, request, pk):
        try:
            subscription = Subscription.objects.select_related('user', 'plan').get(pk=pk)
        except Subscription.DoesNotExist:
            raise NotFound("Obuna topilmadi")

        # Permission check
        if subscription.user != request.user and request.user.role != 'admin':
            return Response(
                {"detail": "Bu obunani bekor qila olmaysiz"},
                status=status.HTTP_403_FORBIDDEN
            )

        with transaction.atomic():
            subscription.status = 'cancelled'
            subscription.save(update_fields=['status'])

            logger.info(
                f"Subscription cancelled: user_id={subscription.user.id}, "
                f"subscription_id={subscription.id}, cancelled_by={request.user.id}"
            )

        serializer = SubscriptionSerializer(subscription)
        return Response(serializer.data, status=status.HTTP_200_OK)
