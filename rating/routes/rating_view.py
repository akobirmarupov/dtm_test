import logging

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from drf_spectacular.utils import extend_schema

from common.permissions import IsStudent

from rating.models import Rating
from rating.services import get_period_dates
from rating.routes.serializers import RatingSerializer

logger = logging.getLogger(__name__)

VALID_PERIODS = ('daily', 'weekly', 'all_time')


class MyRatingAPIView(APIView):
    permission_classes = [IsStudent]

    @extend_schema(responses=RatingSerializer)
    def get(self, request):
        period = request.query_params.get('period', 'all_time')
        if period not in VALID_PERIODS:
            return Response(
                {'detail': "period 'daily', 'weekly' yoki 'all_time' bo'lishi kerak."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        start_date, end_date = get_period_dates(period)
        rating = Rating.objects.filter(
            user=request.user,
            period=period,
            period_start_date=start_date,
            period_end_date=end_date,
        ).first()

        if rating is None:
            logger.debug('Rating topilmadi: user_id=%s period=%s', request.user.id, period)
            return Response(
                {
                    'period': period,
                    'period_display': dict(Rating.PeriodChoices.choices).get(period),
                    'stars': 0.0,
                    'rank': None,
                    'tests_completed': 0,
                    'correct_answers': 0,
                    'incorrect_answers': 0,
                    'accuracy_percentage': 0,
                    'period_start_date': start_date,
                    'period_end_date': end_date,
                    'last_updated': None,
                },
                status=status.HTTP_200_OK,
            )

        return Response(RatingSerializer(rating).data, status=status.HTTP_200_OK)
