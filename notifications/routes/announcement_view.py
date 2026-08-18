import logging

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from drf_spectacular.utils import extend_schema

from common.permissions import IsAdmin
from common.pagination import StandardResultsPagination

from notifications.models import Announcement
from notifications.routes.serializers import AnnouncementSerializer

logger = logging.getLogger(__name__)


class AnnouncementListCreateAPIView(APIView):
    """
    Hozircha bizda real SMS/Push integratsiyasi yo'q — bu "oddiy xabarnoma":
    admin matn yozadi (POST), va Announcement yaratilishi bilanoq
    notifications/signals.py'dagi broadcast_announcement signali ishga tushib,
    barcha faol foydalanuvchilarga NotificationLog (in-app xabar) yaratadi
    (is_sent/sent_at/recipients_count ham o'sha signal orqali to'ldiriladi).
    Shu sababli bu yerda tarqatish logikasi qaytarilmaydi.
    """
    permission_classes = [IsAdmin]
    pagination_class = StandardResultsPagination

    @extend_schema(responses=AnnouncementSerializer(many=True))
    def get(self, request):
        queryset = Announcement.objects.all().order_by('-created_at')
        paginator = self.pagination_class()
        page = paginator.paginate_queryset(queryset, request, view=self)
        serializer = AnnouncementSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)

    @extend_schema(request=AnnouncementSerializer, responses={201: AnnouncementSerializer})
    def post(self, request):
        serializer = AnnouncementSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        announcement = serializer.save(created_by=request.user)

        logger.info(
            'Announcement yaratildi: id=%s admin=%s recipients=%s',
            announcement.id, request.user.id, announcement.recipients_count,
        )

        return Response(AnnouncementSerializer(announcement).data, status=status.HTTP_201_CREATED)
