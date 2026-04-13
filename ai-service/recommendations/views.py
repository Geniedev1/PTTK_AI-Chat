import logging

from django.conf import settings
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from .serializers import (
    CartRecommendationQuerySerializer,
    HomeRecommendationQuerySerializer,
    ProfileSnapshotQuerySerializer,
    ProductDetailRecommendationQuerySerializer,
)
from .services import RecommendationService, ServiceClientError


logger = logging.getLogger(__name__)


class RecommendationViewSet(viewsets.ViewSet):
    permission_classes = [AllowAny]
    service_class = RecommendationService

    def _limit(self, validated_data):
        requested_limit = validated_data.get("limit", getattr(settings, "RECOMMENDATION_LIMIT_DEFAULT", 10))
        return max(1, min(int(requested_limit), getattr(settings, "RECOMMENDATION_LIMIT_MAX", 20)))

    def _handle_service_error(self, exc):
        return Response({"detail": str(exc)}, status=exc.status_code or status.HTTP_502_BAD_GATEWAY)

    def _log_payload(self, request, endpoint, payload):
        items = payload.get("items", [])
        logger.info(
            "ai_recommendation_result request_id=%s endpoint=%s user_id=%s session_id=%s item_count=%s top_product_ids=%s top_reason_codes=%s",
            getattr(request, "request_id", "-"),
            endpoint,
            request.query_params.get("user_id"),
            request.query_params.get("session_id"),
            len(items),
            [item["product"]["id"] for item in items[:3]],
            [item["reason_codes"] for item in items[:3]],
        )

    @action(detail=False, methods=["get"], url_path="home")
    def home(self, request):
        serializer = HomeRecommendationQuerySerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        validated = serializer.validated_data

        try:
            payload = self.service_class().recommend_home(
                user_id=validated.get("user_id"),
                session_id=validated.get("session_id"),
                limit=self._limit(validated),
            )
        except ServiceClientError as exc:
            return self._handle_service_error(exc)
        self._log_payload(request, "recommend.home", payload)
        return Response(payload)

    @action(detail=False, methods=["get"], url_path="product-detail")
    def product_detail(self, request):
        serializer = ProductDetailRecommendationQuerySerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        validated = serializer.validated_data

        try:
            payload = self.service_class().recommend_product_detail(
                product_id=validated["product_id"],
                user_id=validated.get("user_id"),
                session_id=validated.get("session_id"),
                limit=self._limit(validated),
            )
        except ServiceClientError as exc:
            return self._handle_service_error(exc)
        self._log_payload(request, "recommend.product_detail", payload)
        return Response(payload)

    @action(detail=False, methods=["get"], url_path="cart")
    def cart(self, request):
        serializer = CartRecommendationQuerySerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        validated = serializer.validated_data

        try:
            payload = self.service_class().recommend_cart(
                session_id=validated["session_id"],
                user_id=validated.get("user_id"),
                limit=self._limit(validated),
            )
        except ServiceClientError as exc:
            return self._handle_service_error(exc)
        self._log_payload(request, "recommend.cart", payload)
        return Response(payload)

    @action(detail=False, methods=["get"], url_path="profile/snapshot")
    def profile_snapshot(self, request):
        serializer = ProfileSnapshotQuerySerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        validated = serializer.validated_data
        if validated.get("user_id") is None and not validated.get("session_id"):
            return Response({"detail": "Provide user_id or session_id."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            payload = self.service_class().get_profile_snapshot(
                user_id=validated.get("user_id"),
                session_id=validated.get("session_id"),
            )
        except ServiceClientError as exc:
            return self._handle_service_error(exc)
        logger.info(
            "ai_profile_snapshot request_id=%s user_id=%s session_id=%s snapshot=%s",
            getattr(request, "request_id", "-"),
            validated.get("user_id"),
            validated.get("session_id"),
            payload["profile_snapshot"],
        )
        return Response(payload)
