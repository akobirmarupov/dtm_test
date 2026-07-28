from django.urls import path, include

urlpatterns = [
    path("auth/", include("account.routes.auth.urls")),
]