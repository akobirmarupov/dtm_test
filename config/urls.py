from django.conf import settings
from django.contrib import admin
from django.urls import include, path, re_path
from django.views.static import serve
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularRedocView,
    SpectacularSwaggerView,
)
from rest_framework import permissions

from config.views import GoogleTestView

# Prodda API sxemasi hammaga ochiq bo'lmasligi kerak — faqat admin ko'radi.
SCHEMA_PERMISSIONS = [permissions.AllowAny] if settings.DEBUG else [permissions.IsAdminUser]


urlpatterns = [
    path('admin/', admin.site.urls),

    path('i18n/', include('django.conf.urls.i18n')),

    path('schema/', SpectacularAPIView.as_view(permission_classes=SCHEMA_PERMISSIONS), name='schema'),
    path('swagger/', SpectacularSwaggerView.as_view(
        url_name='schema', permission_classes=SCHEMA_PERMISSIONS), name='schema-swagger-ui'),
    path('redoc/', SpectacularRedocView.as_view(
        url_name='schema', permission_classes=SCHEMA_PERMISSIONS), name='schema-redoc'),

    path("api/", include("account.urls")),
    path("catalog/", include("catalog.routes.urls")),
    path("testengine/", include("testengine.routes.urls")),
    path("progress/", include("progress.routes.urls")),
    path("billing/", include("billing.routes.urls")),
    path("notifications/", include("notifications.routes.urls")),
    path("rating/", include("rating.routes.urls")),
    path("dashboard/", include("dashboard.routes.urls")),

    path("google-test/", GoogleTestView.as_view(), name="google-test"),
]


# Savol rasmlari (`Question.image`) prodda ham ochilishi kerak. `static()`
# yordamchisi faqat DEBUG=True da ishlaydi, shuning uchun `serve` to'g'ridan
# to'g'ri ulanadi.
#
# ESLATMA: bu vaqtinchalik yechim. Render kabi platformalarda disk
# vaqtinchalik — redeploy'da yuklangan rasmlar yo'qoladi. Doimiy saqlash
# uchun S3 yoki Cloudinary'ga o'tish kerak (README ga qarang).
urlpatterns += [
    re_path(
        r'^media/(?P<path>.*)$', serve, {'document_root': settings.MEDIA_ROOT}
    ),
]
