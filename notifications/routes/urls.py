from django.urls import path

from .views import MyNotificationsAPIView, UnreadCountAPIView, MarkNotificationsReadAPIView
from .announcement_view import AnnouncementListCreateAPIView

app_name = "notifications"

urlpatterns = [
    path('my/', MyNotificationsAPIView.as_view(), name='my-notifications'),
    path('unread-count/', UnreadCountAPIView.as_view(), name='unread-count'),
    path('mark-read/', MarkNotificationsReadAPIView.as_view(), name='mark-all-read'),
    path('mark-read/<int:pk>/', MarkNotificationsReadAPIView.as_view(), name='mark-one-read'),

    # Admin: oddiy xabarnoma yozish -> barcha faol talabalarga yuboriladi
    path('announcements/', AnnouncementListCreateAPIView.as_view(), name='announcement-list-create'),
]