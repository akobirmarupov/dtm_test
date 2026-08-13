from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone

from common.pagination import StandardResultsPagination
from notifications.models import NotificationLog
from .serializers import NotificationLogSerializer


class MyNotificationsAPIView(APIView):
    """Qo'ng'iroqcha bosilganda ro'yxatni shu yerdan oladi."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        qs = NotificationLog.objects.filter(user=request.user).order_by('-created_at')
        paginator = StandardResultsPagination()
        page = paginator.paginate_queryset(qs, request, view=self)
        return paginator.get_paginated_response(NotificationLogSerializer(page, many=True).data)


class UnreadCountAPIView(APIView):
    """Qo'ng'iroqcha ustidagi qizil raqamcha uchun."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        count = NotificationLog.objects.filter(user=request.user, is_read=False).count()
        return Response({'unread_count': count})


class MarkAsReadAPIView(APIView):
    """Ro'yxat ochilganda (yoki bitta xabar bosilganda) o'qilgan deb belgilash."""
    permission_classes = [IsAuthenticated]

    def post(self, request, pk=None):
        qs = NotificationLog.objects.filter(user=request.user, is_read=False)
        if pk:
            qs = qs.filter(pk=pk)
        updated = qs.update(is_read=True, read_at=timezone.now())
        return Response({'marked_read': updated})