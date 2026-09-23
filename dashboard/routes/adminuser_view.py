"""Admin uchun foydalanuvchilarni ko'rish va bloklash.

Django admin panelida bu ishlar allaqachon mumkin edi, lekin loyihaning o'z
admin paneli (frontend) uchun API kerak: kim ro'yxatdan o'tgan, nechta odam
bor, qaysi tarifda va kim qoidabuzarlik qilgan.

Bloklash = `is_active=False`. JWT autentifikatsiyasi bunday foydalanuvchini
o'tkazmaydi, shuning uchun tokeni qo'lida bo'lsa ham API yopiladi.
"""

from __future__ import annotations

import logging

from django.db.models import Count, Q
from django.shortcuts import get_object_or_404
from django.utils import timezone
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, extend_schema, inline_serializer
from rest_framework import serializers, status
from rest_framework.response import Response
from rest_framework.views import APIView

from account.models import User
from billing.entitlements import entitlements_for
from billing.services import active_subscription
from common.models import Role
from common.pagination import StandardResultsPagination
from common.permissions import IsAdmin
from common.throttles import BurstUserRateThrottle
from dashboard.routes.serializers import AdminUserDetailSerializer, AdminUserSerializer
from testengine.models import TestSession

logger = logging.getLogger('dashboard.admin')


TRUE_VALUES = {'1', 'true', 'ha', 'yes'}


class AdminUserListAPIView(APIView):
    """`GET /dashboard/admin/users/` — qidiruv va filtrlar bilan ro'yxat."""

    permission_classes = [IsAdmin]
    throttle_classes = [BurstUserRateThrottle]
    pagination_class = StandardResultsPagination

    @extend_schema(
        parameters=[
            OpenApiParameter('search', OpenApiTypes.STR,
                             description='Email, ism, telefon yoki Telegram username.'),
            OpenApiParameter('role', OpenApiTypes.STR,
                             description='student / mentor / admin / support'),
            OpenApiParameter('is_active', OpenApiTypes.BOOL,
                             description='false — faqat bloklanganlar.'),
            OpenApiParameter('tier', OpenApiTypes.STR,
                             description='free yoki pro — obunasi bo\'yicha.'),
            OpenApiParameter('ordering', OpenApiTypes.STR,
                             description='-created_at (standart), created_at, '
                                         '-xp_total, -last_login'),
        ],
        responses=AdminUserSerializer(many=True),
        tags=['Admin users'],
        description="Foydalanuvchilar ro'yxati: kim, qaysi tarifda, bloklanganmi. "
                    "Javobda umumiy statistika ham keladi.",
    )
    def get(self, request):
        queryset = User.objects.all()

        search = (request.query_params.get('search') or '').strip()
        if search:
            queryset = queryset.filter(
                Q(email__icontains=search)
                | Q(full_name__icontains=search)
                | Q(phone_number__icontains=search)
                | Q(telegram_username__icontains=search)
            )

        role = request.query_params.get('role')
        if role:
            queryset = queryset.filter(role=role)

        is_active = request.query_params.get('is_active')
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() in TRUE_VALUES)

        tier = request.query_params.get('tier')
        if tier in ('free', 'pro'):
            now = timezone.now()
            pro_ids = User.objects.filter(
                subscriptions__status='active',
                subscriptions__expires_at__gt=now,
                subscriptions__plan__is_pro=True,
            ).values('id')
            queryset = (
                queryset.filter(id__in=pro_ids) if tier == 'pro'
                else queryset.exclude(id__in=pro_ids)
            )

        ordering = request.query_params.get('ordering') or '-created_at'
        if ordering.lstrip('-') not in ('created_at', 'xp_total', 'last_login', 'email'):
            ordering = '-created_at'
        queryset = queryset.order_by(ordering)

        paginator = self.pagination_class()
        page = paginator.paginate_queryset(queryset, request, view=self)
        response = paginator.get_paginated_response(
            AdminUserSerializer(page, many=True).data
        )
        response.data['stats'] = self.stats()
        return response

    def stats(self) -> dict:
        """Ro'yxat tepasidagi raqamlar."""
        totals = User.objects.aggregate(
            total=Count('id'),
            blocked=Count('id', filter=Q(is_active=False)),
            students=Count('id', filter=Q(role=Role.STUDENT)),
            mentors=Count('id', filter=Q(role=Role.MENTOR)),
        )
        now = timezone.now()
        totals['pro'] = User.objects.filter(
            subscriptions__status='active',
            subscriptions__expires_at__gt=now,
            subscriptions__plan__is_pro=True,
        ).distinct().count()
        return totals


class AdminUserDetailAPIView(APIView):
    """`GET /dashboard/admin/users/<id>/` — bitta foydalanuvchi kartasi."""

    permission_classes = [IsAdmin]
    throttle_classes = [BurstUserRateThrottle]

    @extend_schema(
        responses=AdminUserDetailSerializer, tags=['Admin users'],
        description="Foydalanuvchi haqida to'liq ma'lumot: obunasi, tarifdagi "
                    "imkoniyatlari, faolligi va qurilmalari.",
    )
    def get(self, request, pk):
        user = get_object_or_404(User, pk=pk)
        subscription = active_subscription(user)

        sessions = TestSession.objects.filter(user=user).aggregate(
            total=Count('id'),
            finished=Count('id', filter=Q(finished_at__isnull=False)),
        )
        last_session = (
            TestSession.objects.filter(user=user).order_by('-created_at')
            .values_list('created_at', flat=True).first()
        )

        data = AdminUserSerializer(user).data
        data.update({
            'phone_number': user.phone_number,
            'telegram_username': user.telegram_username,
            'region': user.region,
            'target_major': user.target_major,
            'language': user.language,
            'subscription': {
                'plan': subscription.plan.name if subscription else None,
                'plan_id': subscription.plan_id if subscription else None,
                'expires_at': subscription.expires_at if subscription else None,
                'days_left': subscription.days_left if subscription else 0,
            } if subscription else None,
            'entitlements': entitlements_for(user).as_dict(),
            'sessions_total': sessions['total'],
            'sessions_finished': sessions['finished'],
            'last_test_at': last_session,
            'devices_count': user.devices.filter(is_active=True).count(),
        })
        return Response(AdminUserDetailSerializer(data).data)


class AdminUserBlockAPIView(APIView):
    """`POST /dashboard/admin/users/<id>/block/` va `.../unblock/`."""

    permission_classes = [IsAdmin]
    throttle_classes = [BurstUserRateThrottle]

    block = True

    @extend_schema(
        request=inline_serializer(name='AdminUserBlockRequest', fields={
            'reason': serializers.CharField(required=False, allow_blank=True),
        }),
        responses={
            200: AdminUserSerializer,
            400: inline_serializer(name='AdminUserBlockError', fields={
                'detail': serializers.CharField(),
                'code': serializers.CharField(),
            }),
        },
        tags=['Admin users'],
        description="Bloklangan foydalanuvchi API'ga kira olmaydi — tokeni "
                    "qo'lida bo'lsa ham rad etiladi.",
    )
    def post(self, request, pk):
        user = get_object_or_404(User, pk=pk)

        if self.block:
            error = self.guard(request, user)
            if error is not None:
                return error

            reason = (request.data.get('reason') or '').strip()[:255]
            user.is_active = False
            user.blocked_at = timezone.now()
            user.blocked_by = request.user
            user.block_reason = reason
            user.save(update_fields=[
                'is_active', 'blocked_at', 'blocked_by', 'block_reason', 'updated_at'
            ])
            logger.info(
                'Foydalanuvchi bloklandi: user_id=%s admin_id=%s sabab="%s"',
                user.id, request.user.id, reason,
            )
        else:
            user.is_active = True
            user.blocked_at = None
            user.blocked_by = None
            user.block_reason = ''
            user.save(update_fields=[
                'is_active', 'blocked_at', 'blocked_by', 'block_reason', 'updated_at'
            ])
            logger.info(
                'Foydalanuvchi blokdan chiqarildi: user_id=%s admin_id=%s',
                user.id, request.user.id,
            )

        return Response(AdminUserSerializer(user).data, status=status.HTTP_200_OK)

    def guard(self, request, user):
        """O'zini va boshqa adminlarni bloklashdan saqlaydi.

        Aks holda bitta xato bosish bilan panelga kirish yo'li yopilib qolishi
        mumkin.
        """
        if user.id == request.user.id:
            return Response(
                {'detail': "O'zingizni bloklay olmaysiz.", 'code': 'self_block'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if user.is_superuser or user.role == Role.ADMIN:
            return Response(
                {
                    'detail': "Administratorni bloklash mumkin emas. Avval uning "
                              "rolini o'zgartiring.",
                    'code': 'admin_block',
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
        return None


class AdminUserUnblockAPIView(AdminUserBlockAPIView):
    block = False
