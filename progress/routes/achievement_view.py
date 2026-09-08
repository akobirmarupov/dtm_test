from drf_spectacular.utils import extend_schema, inline_serializer
from rest_framework import serializers
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from common.i18n import resolve_language, translated
from common.throttles import BurstUserRateThrottle
from progress.achievements import progress_for


class AchievementListAPIView(APIView):
    permission_classes = [IsAuthenticated]
    throttle_classes = [BurstUserRateThrottle]

    @extend_schema(
        responses=inline_serializer(name='AchievementListResponse', fields={
            'unlocked_count': serializers.IntegerField(),
            'total_count': serializers.IntegerField(),
            'results': serializers.ListField(child=serializers.DictField()),
        }),
        tags=['Progress'],
        description="Barcha yutuqlar: qo'lga kiritilganlari va qolganlariga "
                    "qancha qolgani.",
    )
    def get(self, request):
        language = resolve_language(request)
        rows = progress_for(request.user)

        results = []
        for row in rows:
            achievement = row['achievement']
            results.append({
                'code': achievement.code,
                'name': translated(achievement, 'name', language),
                'description': translated(achievement, 'description', language),
                'icon': achievement.icon,
                'metric': achievement.metric,
                'threshold': row['threshold'],
                'current_value': row['current_value'],
                'progress_percent': row['progress_percent'],
                'xp_reward': achievement.xp_reward,
                'is_unlocked': row['is_unlocked'],
                'unlocked_at': row['unlocked_at'],
            })

        results.sort(key=lambda item: (not item['is_unlocked'], -item['progress_percent']))

        return Response({
            'unlocked_count': sum(1 for item in results if item['is_unlocked']),
            'total_count': len(results),
            'results': results,
        })
