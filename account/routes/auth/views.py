from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError

from account.models import User
from account.google_auth import verify_google_token
from common.throttles import AnonBurstRateThrottle, BurstUserRateThrottle

from .serializer import GoogleAuthSerializer, UserSerializer, LogoutSerializer

import logging
logger = logging.getLogger(__name__)


class GoogleAuthView(APIView):
    permission_classes = []
    throttle_classes = [AnonBurstRateThrottle]

    def post(self, request):
        serializer = GoogleAuthSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        
        try:
            g = verify_google_token(serializer.validated_data["id_token"])
        except Exception as e:
            logger.exception("Google token tekshirishda xato")
            return Response({"detail": f"Xato: {type(e).__name__}: {str(e)}"}, status=400)

        user, created = User.objects.get_or_create(
            email=g["email"],
            defaults={
                "google_id": g["google_id"],
                "full_name": g["full_name"],
                "avatar_url": g["avatar_url"],
            },
        )

        if not created:
            user.full_name = g["full_name"] or user.full_name
            user.avatar_url = g["avatar_url"] or user.avatar_url
            user.save(update_fields=["full_name", "avatar_url"])

        tokens = RefreshToken.for_user(user)
        return Response({
            "access": str(tokens.access_token),
            "refresh": str(tokens),
            "user": UserSerializer(user).data,
            "is_new_user": created,
        })


class MeView(APIView):
    permission_classes = [IsAuthenticated]
    throttle_classes = [BurstUserRateThrottle]

    def get(self, request):
        return Response(UserSerializer(request.user).data)


class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = LogoutSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            token = RefreshToken(serializer.validated_data["refresh"])
            token.blacklist()
        except TokenError:
            return Response({"detail": "Token yaroqsiz yoki allaqachon bekor qilingan"}, status=400)

        return Response({"detail": "Tizimdan muvaffaqiyatli chiqdingiz"})