import logging

from django.core.cache import cache
from django.utils import timezone
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.generics import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, extend_schema

from common.permissions import IsStudent, IsOwner
from common.pagination import StandardResultsPagination
from common.throttles import BurstUserRateThrottle, SustainedUserRateThrottle

from progress.models import ReviewCard
from progress.routes.serializers import ReviewCardSerializer, ReviewCardSubmitSerializer
from progress.filters import ReviewCardFilter
from progress.services import submit_review_card_answer


logger = logging.getLogger(__name__)


TODAY_CACHE_TTL = 60 * 5
TODAY_CACHE_KEY = 'progress:reviews:today:user:{user_id}'


# `ReviewCardFilter` qo'lda qo'llaniladi (bu oddiy APIView, `queryset` atributi yo'q),
# shuning uchun drf-spectacular filtrlarni o'zi topa olmaydi — quyida qo'lda beriladi.
REVIEW_CARD_FILTER_PARAMETERS = [
    OpenApiParameter('user', OpenApiTypes.INT),
    OpenApiParameter('question', OpenApiTypes.INT),
    OpenApiParameter('stability_days_min', OpenApiTypes.NUMBER),
    OpenApiParameter('stability_days_max', OpenApiTypes.NUMBER),
    OpenApiParameter('next_review_date', OpenApiTypes.DATE),
    OpenApiParameter('next_review_date_after', OpenApiTypes.DATE),
    OpenApiParameter('next_review_date_before', OpenApiTypes.DATE),
]


class  ReviewCardListAPIView(APIView):
    permission_classes = [IsStudent]
    filter_backends = [DjangoFilterBackend]
    filterset_class = ReviewCardFilter
    pagination_class = StandardResultsPagination

    @extend_schema(
        parameters=REVIEW_CARD_FILTER_PARAMETERS,
        filters=False,
        responses=ReviewCardSerializer(many=True),
    )
    def get(self, request):
        queryset = (ReviewCard.objects.filter(user=request.user)
                     .select_related('question', 'question__topic', 'question__topic__subject').order_by('next_review_date'))
        queryset = ReviewCardFilter(request.GET, queryset=queryset).qs
        paginator = self.pagination_class()
        page = paginator.paginate_queryset(queryset, request, view=self)
        serializer = ReviewCardSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)



class ReviewCardTodayAPIView(APIView):
    permission_classes = [IsStudent]

    @extend_schema(responses=ReviewCardSerializer(many=True))
    def get(self, request):
        cache_key = TODAY_CACHE_KEY.format(user_id=request.user.id)
        cached_data = cache.get(cache_key)

        if cached_data is not None:
            logger.debug('ReviewCard today: cache hit user_id=%s', request.user.id)
            return Response(cached_data, status=status.HTTP_200_OK)

        today = timezone.now().date()
        queryset = (ReviewCard.objects.filter(user=request.user, next_review_date__lte=today)
                    .select_related('question', 'question__topic', 'question__topic__subject'))

        serializer = ReviewCardSerializer(queryset, many=True)
        response_data = {
            'count': queryset.count(),
            'results': serializer.data
        }

        cache.set(cache_key, response_data, TODAY_CACHE_TTL)
        logger.debug('ReviewCard today: cache miss, saved user_id=%s', request.user.id)

        return Response(response_data, status=status.HTTP_200_OK)


class ReviewCardSubmitAPIview(APIView):
    permission_classes = [IsStudent, IsOwner]
    throttle_classes = [BurstUserRateThrottle, SustainedUserRateThrottle]

    @extend_schema(request=ReviewCardSubmitSerializer, responses=ReviewCardSerializer)
    def post(self, request, pk):
        card = get_object_or_404(ReviewCard, pk=pk)
        self.check_object_permissions(request, card)

        serializer = ReviewCardSubmitSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        updated_card = submit_review_card_answer(
            card=card,
            is_correct=serializer.validated_data['is_correct'],
            response_time=serializer.validated_data['response_time'],
        )

        cache.delete(TODAY_CACHE_KEY.format(user_id=request.user.id))

        logger.info(
            'ReviewCard submitted: user_id=%s card_id=%s is_correct=%s',
            request.user.id, card.id, serializer.validated_data['is_correct'],
        )

        return Response(
            ReviewCardSerializer(updated_card).data,
            status=status.HTTP_200_OK,
        )