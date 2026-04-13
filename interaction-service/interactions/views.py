from django.conf import settings
from django.db.models import Count, Q
from django.db.models.functions import TruncDate
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from .constants import EVENT_SIGNAL_WEIGHTS, PRODUCT_INTEREST_EVENTS
from .knowledge_graph import get_graph_store
from .models import InteractionEvent
from .serializers import InteractionEventCreateSerializer, InteractionEventSerializer


class InteractionEventViewSet(viewsets.GenericViewSet):
    permission_classes = [AllowAny]
    queryset = InteractionEvent.objects.all()

    def get_serializer_class(self):
        if self.action == "create":
            return InteractionEventCreateSerializer
        return InteractionEventSerializer

    def _filtered_queryset(self, request):
        queryset = self.get_queryset().order_by("-timestamp", "-id")

        event_type = request.query_params.get("event_type")
        user_id = request.query_params.get("user_id")
        session_id = request.query_params.get("session_id")
        product_id = request.query_params.get("product_id")
        query_text = request.query_params.get("query_text")
        source = request.query_params.get("source")
        date_from = request.query_params.get("date_from")
        date_to = request.query_params.get("date_to")

        if event_type:
            queryset = queryset.filter(event_type=event_type)
        if user_id:
            queryset = queryset.filter(user_id=user_id)
        if session_id:
            queryset = queryset.filter(session_id=session_id)
        if product_id:
            queryset = queryset.filter(product_id=product_id)
        if query_text:
            queryset = queryset.filter(query_text__icontains=query_text)
        if source:
            queryset = queryset.filter(source=source)
        if date_from:
            queryset = queryset.filter(timestamp__date__gte=date_from)
        if date_to:
            queryset = queryset.filter(timestamp__date__lte=date_to)

        return queryset

    def list(self, request):
        queryset = self._filtered_queryset(request)
        limit = min(int(request.query_params.get("limit", 50)), 200)
        serializer = InteractionEventSerializer(queryset[:limit], many=True)
        return Response(serializer.data)

    def create(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        event = serializer.save()
        if getattr(settings, "GRAPH_SYNC_ON_WRITE", True):
            get_graph_store().sync_interaction_event(
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
            )
        return Response(InteractionEventSerializer(event).data, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=["get"])
    def data_quality(self, request):
        queryset = self._filtered_queryset(request)
        total_events = queryset.count()
        missing_identity = queryset.filter(user_id__isnull=True, session_id__isnull=True).count()
        missing_product_context = queryset.filter(
            event_type__in=list(PRODUCT_INTEREST_EVENTS | {"cart_item_removed", "cart_item_quantity_updated"}),
            product_id__isnull=True,
        ).count()
        missing_query_on_search = queryset.filter(event_type="search_performed").filter(
            Q(query_text__isnull=True) | Q(query_text="")
        ).count()

        per_event_counts = {
            row["event_type"]: row["count"]
            for row in queryset.values("event_type").annotate(count=Count("id")).order_by("event_type")
        }

        return Response(
            {
                "total_events": total_events,
                "missing_identity_count": missing_identity,
                "missing_product_context_count": missing_product_context,
                "missing_query_on_search_count": missing_query_on_search,
                "event_type_counts": per_event_counts,
            }
        )

    @action(detail=False, methods=["get"])
    def top_queries(self, request):
        queryset = self._filtered_queryset(request).filter(event_type="search_performed").exclude(
            Q(query_text__isnull=True) | Q(query_text="")
        )
        rows = queryset.values("query_text").annotate(search_count=Count("id")).order_by("-search_count", "query_text")[:10]
        return Response(list(rows))

    @action(detail=False, methods=["get"])
    def product_gaps(self, request):
        base_queryset = self._filtered_queryset(request)
        product_ids = base_queryset.exclude(product_id__isnull=True).values("product_id").distinct()
        rows = []
        for row in product_ids:
            product_id = row["product_id"]
            product_events = base_queryset.filter(product_id=product_id)
            viewed_count = product_events.filter(event_type="product_viewed").count()
            cart_count = product_events.filter(event_type="cart_item_added").count()
            paid_count = product_events.filter(event_type__in=["order_paid", "order_completed"]).count()
            rows.append(
                {
                    "product_id": product_id,
                    "viewed_count": viewed_count,
                    "cart_added_count": cart_count,
                    "paid_count": paid_count,
                }
            )
        rows.sort(key=lambda item: (-item["viewed_count"], item["cart_added_count"], item["product_id"]))
        return Response(rows[:10])

    @action(detail=False, methods=["get"])
    def abandoned_carts(self, request):
        base_queryset = self._filtered_queryset(request)
        cart_sessions = (
            base_queryset.filter(event_type="cart_item_added")
            .exclude(session_id__isnull=True)
            .exclude(session_id="")
            .values("session_id", "user_id")
            .annotate(cart_event_count=Count("id"))
            .order_by("-cart_event_count", "session_id")
        )

        rows = []
        for row in cart_sessions:
            paid_exists = base_queryset.filter(
                Q(event_type="order_paid") | Q(event_type="order_completed"),
                session_id=row["session_id"],
            ).exists()
            if not paid_exists:
                rows.append(row)

        return Response(rows[:20])

    @action(detail=False, methods=["get"])
    def category_interest(self, request):
        queryset = self._filtered_queryset(request).exclude(metadata__category_id__isnull=True)
        grouped = (
            queryset.annotate(day=TruncDate("timestamp"))
            .values("day", "metadata__category_id")
            .annotate(event_count=Count("id"))
            .order_by("-day", "metadata__category_id")
        )
        return Response(list(grouped[:50]))

    @action(detail=False, methods=["get"])
    def signal_weights(self, request):
        counts = {
            row["event_type"]: row["count"]
            for row in self._filtered_queryset(request).values("event_type").annotate(count=Count("id"))
        }
        rows = []
        for event_type, weight in EVENT_SIGNAL_WEIGHTS.items():
            rows.append(
                {
                    "event_type": event_type,
                    "weight": weight,
                    "recorded_count": counts.get(event_type, 0),
                }
            )
        return Response(rows)
