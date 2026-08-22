from django.utils import timezone
from rest_framework import serializers
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from drf_spectacular.openapi import AutoSchema
from drf_spectacular.utils import extend_schema, inline_serializer

from common.pagination import StandardResultsPagination
from notifications.models import NotificationLog
from notifications.routes.serializers import NotificationLogSerializer


class MarkNotificationsReadSchema(AutoSchema):
    """`MarkNotificationsReadAPIView` ikkita URL'ga ulangan (`mark-read/` va
    `mark-read/{id}/`); ikkalasi ham bir xil operationId hosil qilar edi.
    Faqat hujjat uchun — ish mantiqiga ta'siri yo'q."""

    def get_operation_id(self) -> str:
        if '{id}' in self.path:
            return 'notifications_mark_read_one_create'
        return 'notifications_mark_read_all_create'


class MyNotificationsAPIView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(responses={200: NotificationLogSerializer(many=True)})
    def get(self, request):
        queryset = NotificationLog.objects.filter(user=request.user)
        paginator = StandardResultsPagination()
        page = paginator.paginate_queryset(queryset, request, view=self)
        serializer = NotificationLogSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)


class UnreadCountAPIView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        responses={
            200: inline_serializer(
                name='NotificationUnreadCountResponse',
                fields={'unread_count': serializers.IntegerField()},
            )
        }
    )
    def get(self, request):
        count = NotificationLog.objects.filter(user=request.user, is_read=False).count()
        return Response({'unread_count': count})


class MarkNotificationsReadAPIView(APIView):
    permission_classes = [IsAuthenticated]
    schema = MarkNotificationsReadSchema()

    @extend_schema(
        request=None,
        responses={
            200: inline_serializer(
                name='NotificationMarkReadResponse',
                fields={'marked_read': serializers.IntegerField()},
            )
        },
    )
    def post(self, request, pk=None):
        queryset = NotificationLog.objects.filter(user=request.user, is_read=False)
        if pk is not None:
            queryset = queryset.filter(pk=pk)
        updated = queryset.update(is_read=True, read_at=timezone.now())
        return Response({'marked_read': updated})
