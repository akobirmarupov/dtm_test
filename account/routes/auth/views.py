"""Autentifikatsiya: Google (Android/web) va Apple ID (iPhone/iPad).

Har ikkala oqim ham bir xil natija beradi: JWT `access` + `refresh`. Shu
tufayli mobil ilova, brauzer va server-mijozlar bitta API dan foydalanadi.
"""

from __future__ import annotations

import logging

from django.db import IntegrityError, transaction
from django.utils import timezone
from drf_spectacular.utils import extend_schema, inline_serializer
from rest_framework import serializers, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import RefreshToken

from account.apple_auth import AppleAuthError, verify_apple_token
from account.google_auth import verify_google_token
from account.models import Device, User
from common.i18n import normalize_language, resolve_language
from common.throttles import AnonBurstRateThrottle, BurstUserRateThrottle
from notifications.models import NotificationLog

from .serializer import (
    AppleAuthSerializer,
    DeviceSerializer,
    GoogleAuthSerializer,
    LogoutSerializer,
    ProfileUpdateSerializer,
    UserSerializer,
)

logger = logging.getLogger('account.auth')


def auth_response_serializer(name):
    return inline_serializer(
        name=name,
        fields={
            'access': serializers.CharField(),
            'refresh': serializers.CharField(),
            'user': UserSerializer(),
            'is_new_user': serializers.BooleanField(),
        },
    )


def error_serializer(name):
    return inline_serializer(name=name, fields={'detail': serializers.CharField()})


def register_device(user, payload):
    """Login paytida yuborilgan qurilma ma'lumotini saqlaydi (ixtiyoriy).

    Qurilma yuborilmasa hech narsa qilmaydi — brauzerdan kirish uchun bu
    ma'lumot shart emas.
    """
    if not payload or not isinstance(payload, dict):
        return None

    device_id = str(payload.get('device_id') or '').strip()
    if not device_id:
        return None

    defaults = {
        'platform': payload.get('platform') or Device.Platform.OTHER,
        'push_token': str(payload.get('push_token') or '')[:512],
        'model_name': str(payload.get('model_name') or '')[:100],
        'os_version': str(payload.get('os_version') or '')[:50],
        'app_version': str(payload.get('app_version') or '')[:50],
        'language': normalize_language(payload.get('language')) or user.language,
        'is_active': True,
    }
    if defaults['platform'] not in Device.Platform.values:
        defaults['platform'] = Device.Platform.OTHER

    try:
        device, _ = Device.objects.update_or_create(
            user=user, device_id=device_id, defaults=defaults
        )
        return device
    except IntegrityError:
        logger.warning('Qurilmani saqlab bo\'lmadi: user_id=%s', user.id)
        return None


def issue_tokens(user, created, device_payload=None):
    register_device(user, device_payload)

    tokens = RefreshToken.for_user(user)
    return Response({
        'access': str(tokens.access_token),
        'refresh': str(tokens),
        'user': UserSerializer(user).data,
        'is_new_user': created,
    })


def welcome(user):
    NotificationLog.objects.create(
        user=user,
        type=NotificationLog.Type.WELCOME,
        message="Tabriklaymiz! Siz ro'yxatdan muvaffaqiyatli o'tdingiz 🎉",
    )


class GoogleAuthView(APIView):
    """POST /api/auth/google/ — Android va web mijozlar uchun."""

    permission_classes = []
    throttle_classes = [AnonBurstRateThrottle]

    @extend_schema(
        request=GoogleAuthSerializer,
        responses={
            200: auth_response_serializer('GoogleAuthResponse'),
            400: error_serializer('GoogleAuthErrorResponse'),
        },
        tags=['Auth'],
    )
    def post(self, request):
        serializer = GoogleAuthSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            g = verify_google_token(serializer.validated_data['id_token'])
        except ValueError:
            return Response(
                {"detail": "Google tokeni noto'g'ri yoki eskirgan"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        language = resolve_language(request)

        with transaction.atomic():
            user, created = User.objects.get_or_create(
                email=g['email'],
                defaults={
                    'google_id': g['google_id'],
                    'full_name': g['full_name'],
                    'avatar_url': g['avatar_url'],
                    'language': language,
                },
            )

            updates = []
            if not user.google_id:
                # Avval Apple orqali kirgan foydalanuvchi endi Google bilan
                # kirdi — ikkala hisobni bitta profilga bog'laymiz.
                user.google_id = g['google_id']
                updates.append('google_id')
            if g['full_name'] and g['full_name'] != user.full_name:
                user.full_name = g['full_name']
                updates.append('full_name')
            if g['avatar_url'] and g['avatar_url'] != user.avatar_url:
                user.avatar_url = g['avatar_url']
                updates.append('avatar_url')
            if updates:
                user.save(update_fields=updates + ['updated_at'])

            if created:
                welcome(user)

        logger.info('Google login: user_id=%s yangi=%s', user.id, created)
        return issue_tokens(user, created, serializer.validated_data.get('device'))


class AppleAuthView(APIView):
    """POST /api/auth/apple/ — iPhone/iPad ("Sign in with Apple")."""

    permission_classes = []
    throttle_classes = [AnonBurstRateThrottle]

    @extend_schema(
        request=AppleAuthSerializer,
        responses={
            200: auth_response_serializer('AppleAuthResponse'),
            400: error_serializer('AppleAuthErrorResponse'),
        },
        tags=['Auth'],
        description="Apple ID orqali kirish. `identity_token` — Apple bergan JWT. "
                    "`full_name` faqat birinchi kirishda keladi, shuning uchun "
                    "mijoz uni alohida yuboradi.",
    )
    def post(self, request):
        serializer = AppleAuthSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            apple = verify_apple_token(
                serializer.validated_data['identity_token'],
                expected_nonce=serializer.validated_data.get('nonce') or None,
            )
        except AppleAuthError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        full_name = (serializer.validated_data.get('full_name') or '').strip()
        language = resolve_language(request)
        created = False

        with transaction.atomic():
            user = User.objects.filter(apple_id=apple['apple_id']).first()

            if user is None and apple['email']:
                # Ayni email bilan Google orqali kirgan bo'lsa — o'sha profil.
                user = User.objects.filter(email__iexact=apple['email']).first()

            if user is None:
                if not apple['email']:
                    # Apple email ulashmagan va bu birinchi kirish — profil
                    # yaratib bo'lmaydi, chunki email USERNAME_FIELD.
                    return Response(
                        {"detail": "Apple hisobingizda email ulashilmagan. "
                                   "Apple ID sozlamalarida emailni ulashishga ruxsat "
                                   "bering yoki Google orqali kiring."},
                        status=status.HTTP_400_BAD_REQUEST,
                    )
                user = User.objects.create_user(
                    email=apple['email'],
                    apple_id=apple['apple_id'],
                    full_name=full_name,
                    language=language,
                )
                created = True
                welcome(user)
            else:
                updates = []
                if not user.apple_id:
                    user.apple_id = apple['apple_id']
                    updates.append('apple_id')
                if full_name and not user.full_name:
                    user.full_name = full_name
                    updates.append('full_name')
                if updates:
                    user.save(update_fields=updates + ['updated_at'])

        logger.info('Apple login: user_id=%s yangi=%s', user.id, created)
        return issue_tokens(user, created, serializer.validated_data.get('device'))


class MeView(APIView):
    """GET/PATCH /api/auth/me/ — profil va sozlamalar (til shu yerda)."""

    permission_classes = [IsAuthenticated]
    throttle_classes = [BurstUserRateThrottle]

    @extend_schema(responses={200: UserSerializer}, tags=['Auth'])
    def get(self, request):
        return Response(UserSerializer(request.user).data)

    @extend_schema(
        request=ProfileUpdateSerializer, responses={200: UserSerializer}, tags=['Auth'],
        description="Profilni tahrirlash. Interfeys tilini shu yerda "
                    "`language: uz|ru|en` bilan o'zgartiriladi.",
    )
    def patch(self, request):
        serializer = ProfileUpdateSerializer(request.user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(UserSerializer(request.user).data)


class DeviceListCreateAPIView(APIView):
    """GET/POST /api/auth/devices/ — qurilmani ro'yxatdan o'tkazish.

    iPhone, Samsung yoki boshqa Android qurilma push xabarnoma olishi uchun
    o'z tokenini shu yerda qoldiradi.
    """

    permission_classes = [IsAuthenticated]
    throttle_classes = [BurstUserRateThrottle]

    @extend_schema(responses=DeviceSerializer(many=True), tags=['Auth'])
    def get(self, request):
        devices = Device.objects.filter(user=request.user, is_active=True)
        return Response(DeviceSerializer(devices, many=True).data)

    @extend_schema(request=DeviceSerializer, responses={200: DeviceSerializer}, tags=['Auth'])
    def post(self, request):
        serializer = DeviceSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data
        device_id = data.pop('device_id')
        data['is_active'] = True

        device, created = Device.objects.update_or_create(
            user=request.user, device_id=device_id, defaults=data
        )

        logger.info(
            'Qurilma %s: user_id=%s platform=%s',
            'ro\'yxatdan o\'tdi' if created else 'yangilandi',
            request.user.id, device.platform,
        )
        return Response(
            DeviceSerializer(device).data,
            status=status.HTTP_201_CREATED if created else status.HTTP_200_OK,
        )


class DeviceDetailAPIView(APIView):
    """DELETE /api/auth/devices/<device_id>/ — qurilmani o'chirish."""

    permission_classes = [IsAuthenticated]
    throttle_classes = [BurstUserRateThrottle]

    @extend_schema(responses={204: None}, tags=['Auth'])
    def delete(self, request, device_id):
        deleted, _ = Device.objects.filter(
            user=request.user, device_id=device_id
        ).delete()
        if not deleted:
            return Response(
                {"detail": "Qurilma topilmadi"}, status=status.HTTP_404_NOT_FOUND
            )
        return Response(status=status.HTTP_204_NO_CONTENT)


class LogoutView(APIView):
    permission_classes = [IsAuthenticated]
    throttle_classes = [BurstUserRateThrottle]

    @extend_schema(
        request=LogoutSerializer,
        responses={
            200: inline_serializer(
                name='LogoutResponse', fields={'detail': serializers.CharField()}
            ),
            400: error_serializer('LogoutErrorResponse'),
        },
        tags=['Auth'],
        description="Chiqish. `device_id` yuborilsa o'sha qurilmaning push "
                    "tokeni ham o'chiriladi — boshqa hisobga kirilganda eski "
                    "foydalanuvchiga xabar bormasligi uchun.",
    )
    def post(self, request):
        serializer = LogoutSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            token = RefreshToken(serializer.validated_data['refresh'])
            token.blacklist()
        except TokenError:
            return Response(
                {"detail": "Token yaroqsiz yoki allaqachon bekor qilingan"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        device_id = (serializer.validated_data.get('device_id') or '').strip()
        if device_id:
            Device.objects.filter(user=request.user, device_id=device_id).update(
                push_token='', is_active=False, last_seen_at=timezone.now()
            )

        return Response({"detail": "Tizimdan muvaffaqiyatli chiqdingiz"})
