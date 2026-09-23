from django.urls import path

from intro.routes.views import (
    IntroQuestionAdminDetailAPIView,
    IntroQuestionAdminListCreateAPIView,
    IntroStartAPIView,
    IntroSubmitAPIView,
)

app_name = 'intro'

urlpatterns = [
    # Ro'yxatdan o'tmagan foydalanuvchi uchun
    path('start/', IntroStartAPIView.as_view(), name='intro-start'),
    path('submit/', IntroSubmitAPIView.as_view(), name='intro-submit'),

    # Admin: savollarni boshqarish (rasm/video yuklash shu yerda)
    path('admin/questions/', IntroQuestionAdminListCreateAPIView.as_view(),
         name='intro-question-list-create'),
    path('admin/questions/<int:pk>/', IntroQuestionAdminDetailAPIView.as_view(),
         name='intro-question-detail'),
]
