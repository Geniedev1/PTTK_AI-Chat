from unittest.mock import Mock, patch

from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIRequestFactory

from .graph_views import KnowledgeGraphViewSet
from .models import InteractionEvent
from .views import InteractionEventViewSet


class InteractionEventFlowTest(TestCase):
    def setUp(self):
        self.factory = APIRequestFactory()
        self.create_view = InteractionEventViewSet.as_view({"post": "create"})
        self.list_view = InteractionEventViewSet.as_view({"get": "list"})
        self.quality_view = InteractionEventViewSet.as_view({"get": "data_quality"})
        self.query_view = InteractionEventViewSet.as_view({"get": "top_queries"})
        self.gaps_view = InteractionEventViewSet.as_view({"get": "product_gaps"})
        self.abandoned_view = InteractionEventViewSet.as_view({"get": "abandoned_carts"})
        self.weights_view = InteractionEventViewSet.as_view({"get": "signal_weights"})
        self.graph_status_view = KnowledgeGraphViewSet.as_view({"get": "status"})
        self.graph_interest_view = KnowledgeGraphViewSet.as_view({"get": "user_interest"})
        self.graph_rebuild_view = KnowledgeGraphViewSet.as_view({"post": "rebuild"})

    def test_create_event_assigns_signal_weight(self):
        request = self.factory.post(
            "/api/interactions/events",
            {
                "event_type": "cart_item_added",
                "session_id": "sess-1",
                "product_id": 10,
                "source": "backend",
                "metadata": {"quantity": 2, "price_snapshot": "25.50"},
            },
            format="json",
        )
        response = self.create_view(request)

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["signal_weight"], 4)

    def test_data_quality_report_counts_missing_context(self):
        InteractionEvent.objects.create(event_type="search_performed", session_id="sess-1", query_text="", source="backend")
        InteractionEvent.objects.create(event_type="product_viewed", session_id="sess-2", source="backend")

        request = self.factory.get("/api/interactions/events/data_quality")
        response = self.quality_view(request)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["total_events"], 2)
        self.assertEqual(response.data["missing_product_context_count"], 1)
        self.assertEqual(response.data["missing_query_on_search_count"], 1)

    def test_query_and_gap_reports(self):
        InteractionEvent.objects.create(
            event_type="search_performed",
            session_id="sess-1",
            query_text="gaming headset",
            source="web",
            metadata={"result_count": 12},
        )
        InteractionEvent.objects.create(
            event_type="product_viewed",
            session_id="sess-1",
            product_id=101,
            source="web",
            metadata={"category_id": 5},
        )
        InteractionEvent.objects.create(
            event_type="product_viewed",
            session_id="sess-2",
            product_id=101,
            source="web",
            metadata={"category_id": 5},
        )
        InteractionEvent.objects.create(
            event_type="cart_item_added",
            session_id="sess-2",
            product_id=101,
            source="backend",
            metadata={"quantity": 1},
        )

        query_response = self.query_view(self.factory.get("/api/interactions/events/top_queries"))
        gap_response = self.gaps_view(self.factory.get("/api/interactions/events/product_gaps"))

        self.assertEqual(query_response.status_code, 200)
        self.assertEqual(query_response.data[0]["query_text"], "gaming headset")
        self.assertEqual(gap_response.status_code, 200)
        self.assertEqual(gap_response.data[0]["product_id"], 101)
        self.assertEqual(gap_response.data[0]["viewed_count"], 2)

    def test_abandoned_carts_and_signal_weights(self):
        InteractionEvent.objects.create(event_type="cart_item_added", session_id="sess-1", product_id=10, source="backend")
        InteractionEvent.objects.create(event_type="cart_item_added", session_id="sess-2", product_id=11, source="backend")
        InteractionEvent.objects.create(event_type="order_paid", session_id="sess-2", product_id=11, source="backend")

        abandoned_response = self.abandoned_view(self.factory.get("/api/interactions/events/abandoned_carts"))
        weights_response = self.weights_view(self.factory.get("/api/interactions/events/signal_weights"))

        self.assertEqual(abandoned_response.status_code, 200)
        self.assertEqual(abandoned_response.data[0]["session_id"], "sess-1")
        self.assertEqual(weights_response.status_code, 200)
        order_paid_row = next(row for row in weights_response.data if row["event_type"] == "order_paid")
        self.assertEqual(order_paid_row["weight"], 6)
        self.assertEqual(order_paid_row["recorded_count"], 1)

    @patch("interactions.graph_views.get_graph_store")
    def test_graph_status_and_user_interest_views(self, mock_get_graph_store):
        mock_store = Mock()
        mock_store.status.return_value = {"enabled": True, "connected": True, "node_counts": {"Product": 3}}
        mock_store.user_interest.return_value = [
            {"category_id": 5, "category_name": "Keyboards", "total_weight": 12, "distinct_products": 2}
        ]
        mock_get_graph_store.return_value = mock_store

        status_response = self.graph_status_view(self.factory.get("/api/interactions/graph/status"))
        interest_response = self.graph_interest_view(self.factory.get("/api/interactions/graph/user_interest", {"session_id": "sess-1"}))

        self.assertEqual(status_response.status_code, 200)
        self.assertTrue(status_response.data["enabled"])
        self.assertEqual(interest_response.status_code, 200)
        self.assertEqual(interest_response.data[0]["category_id"], 5)
        mock_store.user_interest.assert_called_once()

    @patch("interactions.graph_views.ProductCatalogClient")
    @patch("interactions.graph_views.get_graph_store")
    def test_graph_rebuild_requires_admin_and_returns_summary(self, mock_get_graph_store, mock_catalog_client):
        mock_store = Mock()
        mock_store.rebuild_graph.return_value = {
            "enabled": True,
            "synced_products": 2,
            "synced_categories": 1,
            "synced_interactions": 1,
            "updated_pairs": 0,
        }
        mock_get_graph_store.return_value = mock_store
        mock_catalog_client.return_value.fetch_categories.return_value = [{"id": 1, "name": "Keyboards", "slug": "keyboards", "parent": None}]
        mock_catalog_client.return_value.fetch_products.return_value = [{"id": 10, "name": "Keyboard", "slug": "keyboard"}]

        InteractionEvent.objects.create(event_type="product_viewed", session_id="sess-1", product_id=10, source="web")

        forbidden_response = self.graph_rebuild_view(self.factory.post("/api/interactions/graph/rebuild"))
        allowed_request = self.factory.post(
            "/api/interactions/graph/rebuild",
            HTTP_X_INTERNAL_ADMIN_KEY="change-this-in-dev",
        )
        with self.settings(INTERNAL_ADMIN_KEY="change-this-in-dev"):
            allowed_response = self.graph_rebuild_view(allowed_request)

        self.assertEqual(forbidden_response.status_code, 403)
        self.assertEqual(allowed_response.status_code, 200)
        self.assertEqual(allowed_response.data["synced_products"], 2)
