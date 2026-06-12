import logging

from django.conf import settings
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from .knowledge_graph import ProductCatalogClient, get_graph_store
from .models import InteractionEvent


logger = logging.getLogger(__name__)


class KnowledgeGraphViewSet(viewsets.ViewSet):
    permission_classes = [AllowAny]

    def _has_admin_access(self, request):
        admin_key = getattr(settings, "INTERNAL_ADMIN_KEY", "")
        return bool(admin_key) and request.headers.get("X-Internal-Admin-Key") == admin_key

    def _actor_scope(self, request):
        user_id = request.query_params.get("user_id")
        session_id = request.query_params.get("session_id")
        if user_id not in (None, ""):
            try:
                return {"user_id": int(user_id), "session_id": None}, None
            except (TypeError, ValueError):
                return None, Response({"detail": "user_id must be an integer."}, status=status.HTTP_400_BAD_REQUEST)
        if session_id:
            return {"user_id": None, "session_id": session_id.strip()}, None
        return None, Response({"detail": "Provide user_id or session_id."}, status=status.HTTP_400_BAD_REQUEST)

    def _limit(self, request):
        try:
            requested_limit = int(request.query_params.get("limit", getattr(settings, "GRAPH_QUERY_LIMIT", 10)))
        except (TypeError, ValueError):
            requested_limit = getattr(settings, "GRAPH_QUERY_LIMIT", 10)
        return max(1, min(requested_limit, 50))

    @action(detail=False, methods=["get"])
    def status(self, request):
        return Response(get_graph_store().status())

    @action(detail=False, methods=["post"])
    def rebuild(self, request):
        if not self._has_admin_access(request):
            return Response({"detail": "Admin access required."}, status=status.HTTP_403_FORBIDDEN)

        catalog_client = ProductCatalogClient()
        try:
            categories = catalog_client.fetch_categories()
            products = catalog_client.fetch_products()
        except Exception as exc:
            logger.warning("Failed to fetch product catalog for graph rebuild: %s", exc)
            return Response(
                {"detail": "Failed to fetch product catalog for graph rebuild.", "error": str(exc)},
                status=status.HTTP_502_BAD_GATEWAY,
            )

        interactions = [
            {
                "event_type": event.event_type,
                "user_id": event.user_id,
                "session_id": event.session_id,
                "product_id": event.product_id,
                "query_text": event.query_text,
                "signal_weight": event.signal_weight,
                "timestamp": event.timestamp.isoformat(),
                "metadata": event.metadata or {},
            }
            for event in InteractionEvent.objects.all().order_by("timestamp", "id")
        ]
        result = get_graph_store().rebuild_graph(products, categories, interactions)
        return Response(result)

    @action(detail=False, methods=["get"])
    def user_interest(self, request):
        scope, error_response = self._actor_scope(request)
        if error_response:
            return error_response
        rows = get_graph_store().user_interest(limit=self._limit(request), **scope)
        return Response(rows)

    @action(detail=False, methods=["get"])
    def product_neighbors(self, request):
        product_id = request.query_params.get("product_id")
        try:
            product_id = int(product_id)
        except (TypeError, ValueError):
            return Response({"detail": "product_id must be an integer."}, status=status.HTTP_400_BAD_REQUEST)
        rows = get_graph_store().product_neighbors(product_id=product_id, limit=self._limit(request))
        return Response(rows)

    @action(detail=False, methods=["get"])
    def query_paths(self, request):
        product_id = request.query_params.get("product_id")
        query_text = request.query_params.get("query_text")
        if product_id in (None, "") and not query_text:
            return Response(
                {"detail": "Provide product_id or query_text."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if product_id not in (None, ""):
            try:
                product_id = int(product_id)
            except (TypeError, ValueError):
                return Response({"detail": "product_id must be an integer."}, status=status.HTTP_400_BAD_REQUEST)
        rows = get_graph_store().query_paths(
            product_id=product_id,
            query_text=query_text,
            limit=self._limit(request),
        )
        return Response(rows)

    @action(detail=False, methods=["get"])
    def similar_users(self, request):
        scope, error_response = self._actor_scope(request)
        if error_response:
            return error_response
        rows = get_graph_store().similar_users(limit=self._limit(request), **scope)
        return Response(rows)
