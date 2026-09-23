"""`GET /rating/weak-topics/` — «qaysi mavzuda qiynalyapman».

`TopicRating` allaqachon har bir mavzu bo'yicha daraja saqlaydi, lekin
undan foydalanuvchiga hech qanday tavsiya chiqmasdi. Bu endpoint aynan
shu bo'shliqni yopadi: front «Zaif mavzularingiz» bo'limini shundan quradi
va har bir qator yonida «Mashq qilish» tugmasi turadi.
"""

from drf_spectacular.utils import extend_schema
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from common.permissions import CanViewAnalytics
from common.throttles import BurstUserRateThrottle
from rating.routes.serializers import WeakTopicSerializer
from rating.services import weak_topics


class WeakTopicListAPIView(APIView):
    permission_classes = [IsAuthenticated, CanViewAnalytics]
    throttle_classes = [BurstUserRateThrottle]

    @extend_schema(
        responses=WeakTopicSerializer(many=True),
        tags=['Rating'],
        description="Daraja eng past mavzular. Faqat yetarli ma'lumot to'plangan "
                    "(kamida 10 ta javob) mavzular chiqadi — bitta testdagi "
                    "omadsizlik «zaif mavzu» degani emas.",
    )
    def get(self, request):
        try:
            limit = min(int(request.query_params.get('limit', 10)), 50)
        except (TypeError, ValueError):
            limit = 10

        rows = weak_topics(request.user, limit=limit)
        return Response(WeakTopicSerializer(rows, many=True).data)
