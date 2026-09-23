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

from billing.entitlements import entitlements_for_request
from common.permissions import IsStudent, IsOwner
from common.pagination import StandardResultsPagination
from common.throttles import BurstUserRateThrottle, SustainedUserRateThrottle
from common.usage import (
    Feature, consume_if_limited, daily_limit_access, limit_payload,
)

from progress.models import ReviewCard
from progress.routes.serializers import ReviewCardSerializer, ReviewCardSubmitSerializer
from progress.filters import ReviewCardFilter
from progress.services import submit_review_card_answer


logger = logging.getLogger(__name__)


TODAY_CACHE_TTL = 60 * 5
TODAY_CACHE_KEY = 'progress:reviews:today:user:{user_id}'


REVIEW_CARD_FILTER_PARAMETERS = [
    OpenApiParameter('user', OpenApiTypes.INT),
    OpenApiParameter('question', OpenApiTypes.INT),
    OpenApiParameter('stability_days_min', OpenApiTypes.NUMBER),
    OpenApiParameter('stability_days_max', OpenApiTypes.NUMBER),
    OpenApiParameter('next_review_date', OpenApiTypes.DATE),
    OpenApiParameter('next_review_date_after', OpenApiTypes.DATE),
    OpenApiParameter('next_review_date_before', OpenApiTypes.DATE),
]


def review_card_access(request) -> dict:
    """Takrorlash kartalari bo'yicha kunlik limit holati."""
    entitlements = entitlements_for_request(request)
    return daily_limit_access(
        request.user, Feature.REVIEW_CARD,
        entitlements.review_cards_daily_limit,
        closed_detail=(
            "Takrorlash kartalari sizning tarifingizda mavjud emas."
        ),
        reached_detail=(
            "Bugun {limit} ta kartani takrorladingiz — kunlik limitingiz "
            "shuncha. Ertaga 00:00 dan keyin yangilanadi."
        ),
        code='review_card_limit_reached',
    )


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

        if cached_data is None:
            today = timezone.now().date()
            queryset = (ReviewCard.objects.filter(user=request.user, next_review_date__lte=today)
                        .select_related('question', 'question__topic', 'question__topic__subject'))

            serializer = ReviewCardSerializer(queryset, many=True)
            cached_data = {
                'count': queryset.count(),
                'results': serializer.data
            }

            cache.set(cache_key, cached_data, TODAY_CACHE_TTL)
            logger.debug('ReviewCard today: cache miss, saved user_id=%s', request.user.id)
        else:
            logger.debug('ReviewCard today: cache hit user_id=%s', request.user.id)

        # Limit keshlanmaydi: u kun davomida o'zgaradi va tarif ham
        # o'rtada almashishi mumkin.
        access = review_card_access(request)
        cards = cached_data['results']
        if access['limit'] is not None:
            cards = cards[:access['remaining']]

        return Response(
            {
                'count': len(cards),
                'results': cards,
                'due_total': cached_data['count'],
                'limit': access['limit'],
                'used_today': access['used'],
                'remaining_today': access['remaining'],
                'upgrade_required': access['upgrade_required'],
                'detail': access['detail'],
            },
            status=status.HTTP_200_OK,
        )


class ReviewCardSubmitAPIview(APIView):
    permission_classes = [IsStudent, IsOwner]
    throttle_classes = [BurstUserRateThrottle, SustainedUserRateThrottle]

    @extend_schema(request=ReviewCardSubmitSerializer, responses=ReviewCardSerializer)
    def post(self, request, pk):
        card = get_object_or_404(ReviewCard, pk=pk)
        self.check_object_permissions(request, card)

        access = review_card_access(request)
        if not access['allowed']:
            logger.info(
                'Takrorlash limiti: user_id=%s limit=%s used=%s',
                request.user.id, access['limit'], access['used'],
            )
            return Response(limit_payload(access), status=status.HTTP_403_FORBIDDEN)

        serializer = ReviewCardSubmitSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        updated_card = submit_review_card_answer(
            card=card,
            is_correct=serializer.validated_data['is_correct'],
            response_time=serializer.validated_data['response_time'],
        )

        consume_if_limited(request.user, Feature.REVIEW_CARD, access['limit'])
        cache.delete(TODAY_CACHE_KEY.format(user_id=request.user.id))

        logger.info(
            'ReviewCard submitted: user_id=%s card_id=%s is_correct=%s',
            request.user.id, card.id, serializer.validated_data['is_correct'],
        )

        return Response(
            ReviewCardSerializer(updated_card).data,
            status=status.HTTP_200_OK,
        )