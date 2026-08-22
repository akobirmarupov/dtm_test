from __future__ import annotations

import logging

from django.core.cache import cache
from django.db import IntegrityError, transaction
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.exceptions import NotFound
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from billing.filters import PlanFilter
from billing.models import Plan
from billing.routes.serializers import (
    DetailSerializer,
    PlanSerializer,
    PlanWriteSerializer,
)
from common.i18n import resolve_language
from common.permissions import IsAdmin
from common.throttles import BurstUserRateThrottle

logger = logging.getLogger('plan')

PLAN_CACHE_PREFIX = 'billing:plans'


def plan_cache_key(language) -> str:
    return f'{PLAN_CACHE_PREFIX}:active:{language}'


def clear_plan_cache():
    """Barcha tillardagi keshni tozalaydi."""
    cache.delete_pattern(f'{PLAN_CACHE_PREFIX}:*')


class PlanCreateListAPIView(APIView):
    parser_classes = [JSONParser, MultiPartParser, FormParser]
    throttle_classes = [BurstUserRateThrottle]

    def get_permissions(self):
        if self.request.method == "POST":
            return [IsAdmin()]
        return [IsAuthenticated()]

    def get_serializer_context(self, request):
        return {'request': request, 'language': resolve_language(request)}

    @extend_schema(
        operation_id='billing_plan_list',
        responses={200: PlanSerializer(many=True)},
        tags=['Plan'],
        description="Barcha faol tariflar (masalan: Bepul 0 so'm, Standart "
                    "50 000 so'm, Premium 70 000 so'm). Til `?lang=` orqali.",
    )
    def get(self, request):
        language = resolve_language(request)
        has_filters = bool(request.query_params)
        cache_key = plan_cache_key(language)

        if not has_filters:
            cached = cache.get(cache_key)
            if cached is not None:
                return Response(cached, status=status.HTTP_200_OK)

        queryset = Plan.objects.filter(is_active=True).order_by('price', 'id')
        queryset = PlanFilter(request.query_params, queryset=queryset).qs

        data = PlanSerializer(
            queryset, many=True, context=self.get_serializer_context(request)
        ).data

        if not has_filters:
            cache.set(cache_key, data, timeout=3600)
        return Response(data, status=status.HTTP_200_OK)

    @extend_schema(
        request=PlanWriteSerializer,
        responses={201: PlanSerializer, 400: DetailSerializer},
        tags=['Plan'],
    )
    def post(self, request):
        serializer = PlanWriteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            with transaction.atomic():
                plan = serializer.save()
        except IntegrityError as e:
            logger.error(
                f"Plan yaratishda IntegrityError: admin={request.user.id}, error={e}"
            )
            return Response(
                {"detail": "Bu ma'lumotlar bilan Plan allaqachon mavjud."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        clear_plan_cache()

        logger.info(
            f"Yangi plan yaratildi: id={plan.id}, name={plan.name}, "
            f"price={plan.price}, admin={request.user.id}"
        )
        return Response(
            PlanSerializer(plan, context=self.get_serializer_context(request)).data,
            status=status.HTTP_201_CREATED,
        )


class PlanDetailAPIView(APIView):
    throttle_classes = [BurstUserRateThrottle]

    def get_permissions(self):
        if self.request.method == "GET":
            return [IsAuthenticated()]
        return [IsAdmin()]

    def get_serializer_context(self, request):
        return {'request': request, 'language': resolve_language(request)}

    def get_object(self, pk):
        try:
            return Plan.objects.get(pk=pk)
        except Plan.DoesNotExist:
            raise NotFound(f"{pk} ID'li Plan topilmadi.")

    @extend_schema(
        operation_id='billing_plan_retrieve',
        responses={200: PlanSerializer},
        tags=['Plan'],
    )
    def get(self, request, pk):
        plan = self.get_object(pk)
        return Response(
            PlanSerializer(plan, context=self.get_serializer_context(request)).data,
            status=status.HTTP_200_OK,
        )

    @extend_schema(request=PlanWriteSerializer, responses={200: PlanSerializer}, tags=['Plan'])
    def put(self, request, pk):
        return self._update(request, pk, partial=False)

    @extend_schema(request=PlanWriteSerializer, responses={200: PlanSerializer}, tags=['Plan'])
    def patch(self, request, pk):
        return self._update(request, pk, partial=True)

    def _update(self, request, pk, partial):
        plan = self.get_object(pk)
        serializer = PlanWriteSerializer(plan, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)

        try:
            with transaction.atomic():
                plan = serializer.save()
        except IntegrityError as e:
            logger.error(
                f"Plan yangilashda IntegrityError: id={pk}, admin={request.user.id}, error={e}"
            )
            return Response(
                {"detail": "Bu ma'lumotlar bilan ziddiyat yuz berdi."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        clear_plan_cache()

        logger.info(f"Plan yangilandi: id={plan.id}, admin={request.user.id}")
        return Response(
            PlanSerializer(plan, context=self.get_serializer_context(request)).data,
            status=status.HTTP_200_OK,
        )

    @extend_schema(responses={200: DetailSerializer}, tags=['Plan'])
    def delete(self, request, pk):
        """Tarif o'chirilmaydi, faqat faolsizlantiriladi — unga bog'langan
        obunalar tarixi saqlanib qolishi kerak."""
        plan = self.get_object(pk)

        with transaction.atomic():
            plan.is_active = False
            plan.save(update_fields=["is_active", "updated_at"])

        clear_plan_cache()

        logger.info(f"Plan faolsizlantirildi (soft delete): id={plan.id}, admin={request.user.id}")

        return Response(
            {"detail": f"«{plan.name}» plani muvaffaqiyatli faolsizlantirildi."},
            status=status.HTTP_200_OK,
        )
