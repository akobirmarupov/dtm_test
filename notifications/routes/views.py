from django.utils import timezone
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from common.pagination import StandardResultsPagination
from notifications.models import NotificationLog
from notifications.routes.serializers import NotificationLogSerializer


class MyNotificationsAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        queryset = NotificationLog.objects.filter(user=request.user)
        paginator = StandardResultsPagination()
        page = paginator.paginate_queryset(queryset, request, view=self)
        serializer = NotificationLogSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)


class UnreadCountAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        count = NotificationLog.objects.filter(user=request.user, is_read=False).count()
        return Response({'unread_count': count})


class MarkNotificationsReadAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk=None):
        queryset = NotificationLog.objects.filter(user=request.user, is_read=False)
        if pk is not None:
            queryset = queryset.filter(pk=pk)
        updated = queryset.update(is_read=True, read_at=timezone.now())
        return Response({'marked_read': updated})