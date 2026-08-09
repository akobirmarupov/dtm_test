from __future__ import annotations

from rest_framework.parsers import JSONParser, MultiPartParser, FormParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status

from drf_spectacular.utils import extend_schema

from django.db import IntegrityError, transaction
from django.core.cache import cache
import logging

from rest_framework.exceptions import NotFound

from billing.models import Plan
from billing.filters import PlanFilter
from common.permissions import IsMentorOrAdmin
from common.pagination import StandardResultsPagination
from common.throttles import BurstUserRateThrottle
from common.permissions import IsAdmin, IsMentorOrAdmin
from billing.routes.serializers import PlanSerializer

logger = logging.getLogger('plan')



class PlanCreateListAPIView(APIView):
    parser_classes = [JSONParser, MultiPartParser, FormParser]
    throttle_classes = [BurstUserRateThrottle]


    def get_permissions(self):
        if self.request.method == "POST":
            return [IsAdmin()]
        return [IsAuthenticated()]


    @extend_schema(responses={200: PlanSerializer}, tags=['Plan'])
    def get(self, request):
        has_filters = bool(request.query_params)
        cache_key = "billing:plans:active"

        if not has_filters:
            cache_data = cache.get(cache_key)
            if cache_data is not None:
                logger.info("Plan list keshdan qaytarildi")
                return Response(cache_data, status=status.HTTP_200_OK)

        queryset = Plan.objects.filter(is_active=True).order_by('price')
        queryset = PlanFilter(request.query_params, queryset=queryset).qs

        serializer = PlanSerializer(queryset, many=True)
        data = serializer.data

        if not has_filters:
            cache.set(cache_key, data, timeout=3600)
        return Response(data, status=status.HTTP_200_OK)


    @extend_schema(request=PlanSerializer, responses={201: PlanSerializer}, tags=['Plan'])
    def post(self, request):
        serializer = PlanSerializer(data=request.data)
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

        cache.delete("billing:plans:active")

        logger.info(
            f"Yangi plan yaratildi: id={plan.id}, name={plan.name},"
            f"price={plan.price}, admin={request.user.id}"
        )
        return Response(PlanSerializer(plan).data, status=status.HTTP_201_CREATED)


class PlanDetailAPIView(APIView):

    throttle_classes = [BurstUserRateThrottle]

    def get_permissions(self):
        if self.request.method == "GET":
            return [IsAuthenticated()]
        return [IsAdmin()]

    def get_object(self, pk):
        try:
            return Plan.objects.get(pk=pk)
        except Plan.DoesNotExist:
            raise NotFound(f"{pk} ID'li Plan topilmadi.")

    @extend_schema(responses={200: PlanSerializer}, tags=['Plan'])
    def get(self, request, pk):
        plan = self.get_object(pk)
        return Response(PlanSerializer(plan).data, status=status.HTTP_200_OK)

    @extend_schema(request=PlanSerializer, responses={200: PlanSerializer}, tags=['Plan'])
    def put(self, request, pk):
        return self._update(request, pk, partial=False)

    @extend_schema(request=PlanSerializer, responses={200: PlanSerializer}, tags=['Plan'])
    def patch(self, request, pk):
        return self._update(request, pk, partial=True)

    def _update(self, request, pk, partial):
        plan = self.get_object(pk)
        serializer = PlanSerializer(plan, data=request.data, partial=partial)
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

        cache.delete("billing:plans:active")

        logger.info(f"Plan yangilandi: id={plan.id}, admin={request.user.id}")

        return Response(PlanSerializer(plan).data, status=status.HTTP_200_OK)

    @extend_schema(responses={200: dict}, tags=['Plan'])
    def delete(self, request, pk):
        plan = self.get_object(pk)

        with transaction.atomic():
            plan.is_active = False
            plan.save(update_fields=["is_active"])

        cache.delete("billing:plans:active")

        logger.info(f"Plan faolsizlantirildi (soft delete): id={plan.id}, admin={request.user.id}")

        return Response(
            {"detail": f"«{plan.name}» plani muvaffaqiyatli faolsizlantirildi."},
            status=status.HTTP_200_OK,
        )