from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView

from .views import (
    AppleAuthView,
    DeviceDetailAPIView,
    DeviceListCreateAPIView,
    GoogleAuthView,
    LogoutView,
    MeView,
)

urlpatterns = [
    # Kirish: Android/web -> google, iPhone/iPad -> apple
    path("google/", GoogleAuthView.as_view(), name="google-auth"),
    path("apple/", AppleAuthView.as_view(), name="apple-auth"),

    path("refresh/", TokenRefreshView.as_view(), name="token-refresh"),
    path("logout/", LogoutView.as_view(), name="logout"),

    # Profil va til
    path("me/", MeView.as_view(), name="me"),

    # Qurilmalar (push xabarnoma uchun)
    path("devices/", DeviceListCreateAPIView.as_view(), name="device-list-create"),
    path("devices/<str:device_id>/", DeviceDetailAPIView.as_view(), name="device-detail"),
]
