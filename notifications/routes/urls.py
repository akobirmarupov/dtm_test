from django.urls import path

from .views import MyNotificationsAPIView, UnreadCountAPIView, MarkNotificationsReadAPIView

app_name = "notifications"

urlpatterns = [
    path('my/', MyNotificationsAPIView.as_view(), name='my-notifications'),
    path('unread-count/', UnreadCountAPIView.as_view(), name='unread-count'),
    path('mark-read/', MarkNotificationsReadAPIView.as_view(), name='mark-all-read'),
    path('mark-read/<int:pk>/', MarkNotificationsReadAPIView.as_view(), name='mark-one-read'),
]