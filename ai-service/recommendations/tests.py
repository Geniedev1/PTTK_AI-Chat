from pathlib import Path
from io import StringIO
import json
from tempfile import TemporaryDirectory
from unittest.mock import patch

from django.core.management import call_command
from django.test import TestCase, override_settings
from django.http import HttpResponse
from django.test import RequestFactory
from django.core.management.base import CommandError
from rest_framework.test import APIRequestFactory

from ai_service.middleware import RequestContextMiddleware

from .chat_services import ChatbotService
from .deep_dataset import build_dataset_records, build_quality_report, split_samples_by_actor_time
from .deep_model_training import load_jsonl
from .chat_views import ChatViewSet
from .services import InteractionAnalyticsClient, RecommendationService
from .views import ModelStatusViewSet, ProfileViewSet, RecommendationViewSet


KNOWLEDGE_BASE_DIR = str(Path(__file__).resolve().parents[1] / "knowledge_base")


class StubProductClient:
    def fetch_products(self):
        return [
            {
                "id": 1,
                "name": "Work Keyboard",
                "slug": "work-keyboard",
                "short_description": "Quiet keyboard",
                "category_id": 10,
                "brand_id": 200,
                "base_price": "99.00",
                "stock": 12,
                "is_active": True,
                "has_stock": True,
                "tags": ["keyboard"],
            },
            {
                "id": 2,
                "name": "Silent Keyboard Pro",
                "slug": "silent-keyboard-pro",
                "short_description": "Low-noise switches",
                "category_id": 10,
                "brand_id": 201,
                "base_price": "109.00",
                "stock": 7,
                "is_active": True,
                "has_stock": True,
                "tags": ["keyboard"],
            },
            {
                "id": 3,
                "name": "Gaming Mouse",
                "slug": "gaming-mouse",
                "short_description": "Fast wireless mouse",
                "category_id": 11,
                "brand_id": 300,
                "base_price": "59.00",
                "stock": 9,
                "is_active": True,
                "has_stock": True,
                "tags": ["mouse"],
            },
            {
                "id": 4,
                "name": "Keyboard Wrist Rest",
                "slug": "keyboard-wrist-rest",
                "short_description": "Desk comfort",
                "category_id": 10,
                "brand_id": 400,
                "base_price": "25.00",
                "stock": 20,
                "is_active": True,
                "has_stock": True,
                "tags": ["accessory"],
            },
        ]

    def fetch_product(self, product_id):
        for product in self.fetch_products():
            if product["id"] == int(product_id):
                return product
        raise AssertionError("Unexpected product lookup in test.")


class StubInteractionClient:
    def fetch_product_gaps(self):
        return [
            {"product_id": 2, "viewed_count": 8, "cart_added_count": 3, "paid_count": 1},
            {"product_id": 3, "viewed_count": 6, "cart_added_count": 1, "paid_count": 0},
        ]

    def fetch_events(self, *, user_id=None, session_id=None, limit=25):
        if user_id == 77 or session_id == "sess-1":
            return [
                {"event_type": "product_clicked", "product_id": 1, "signal_weight": 2, "query_text": ""},
                {"event_type": "cart_item_added", "product_id": 1, "signal_weight": 4, "query_text": ""},
                {"event_type": "product_viewed", "product_id": 1, "signal_weight": 4, "query_text": "quiet keyboard"},
                {"event_type": "product_viewed", "product_id": 4, "signal_weight": 2, "query_text": ""},
            ]
        if user_id == 88:
            return [{"event_type": "product_viewed", "product_id": 2, "signal_weight": 3, "query_text": ""}]
        return []

    def fetch_user_interest(self, *, user_id=None, session_id=None, limit=5):
        if user_id == 77 or session_id == "sess-1":
            return [{"category_id": 10, "total_weight": 8}]
        return []

    def fetch_product_neighbors(self, *, product_id, limit=6):
        if int(product_id) == 1:
            return [{"product_id": 2, "similarity_score": 6, "shared_actor_count": 2}]
        if int(product_id) == 2:
            return [{"product_id": 4, "similarity_score": 4, "shared_actor_count": 1}]
        return []

    def fetch_similar_users(self, *, user_id=None, session_id=None, limit=3):
        if user_id == 77:
            return [{"actor_id": 88, "similarity_score": 5, "shared_products": 1}]
        return []


class StubCartClient:
    def fetch_current_cart(self, session_id):
        if session_id == "sess-1":
            return {
                "items": [{"product_id": 1}, {"product_id": 4}],
                "item_count": 2,
                "total_quantity": 3,
                "subtotal_amount": "124.00",
            }
        return {"items": [], "item_count": 0, "total_quantity": 0, "subtotal_amount": "0.00"}


class StubOrderClient:
    def fetch_order(self, *, order_id=None, customer_id=None, session_id=None):
        if order_id == 99 or session_id == "sess-1" or customer_id == 7:
            return {
                "id": 99,
                "status": "PAID",
                "total_amount": "149.99",
                "items": [{"product_id": 1}],
            }
        return None


class StubDeepModelRuntime:
    alpha = 0.5

    def __init__(self, *, enabled=True, loaded=True, scores=None, fallback_mode="deep-model"):
        self._enabled = enabled
        self._loaded = loaded
        self._scores = scores or []
        self._fallback_mode = fallback_mode

    def status(self):
        return {
            "enabled": self._enabled,
            "loaded": self._loaded,
            "model_version": "plan11b-mlp-v1",
            "artifact_dir": "/tmp/11b",
            "alpha": self.alpha,
            "score_clip": {"min": 0.0, "max": 1.0},
            "fallback_mode": self._fallback_mode,
            "error": None if self._loaded else "model unavailable",
        }

    def score_candidates(self, feature_rows):
        if not self._enabled:
            return {
                "applied": False,
                "scores": [],
                "model_version": "plan11b-mlp-v1",
                "fallback_mode": "heuristic-only-disabled",
                "error": None,
            }
        if not self._loaded:
            return {
                "applied": False,
                "scores": [],
                "model_version": "plan11b-mlp-v1",
                "fallback_mode": "heuristic-only-model-unavailable",
                "error": "model unavailable",
            }
        scores = list(self._scores[: len(feature_rows)])
        while len(scores) < len(feature_rows):
            scores.append(0.0)
        return {
            "applied": True,
            "scores": scores,
            "model_version": "plan11b-mlp-v1",
            "fallback_mode": "deep-model",
            "error": None,
        }


class StubInteractionContextClient:
    def __init__(self):
        self.emitted_events = []

    def emit_chat_event(self, **kwargs):
        self.emitted_events.append(kwargs)
        return True

    def fetch_user_interest(self, *, user_id=None, session_id=None, limit=3):
        if user_id == 77 or session_id == "sess-1":
            return [{"category_id": 10, "category_name": "Keyboards", "total_weight": 6}]
        return []

    def fetch_query_paths(self, *, query_text, limit=3):
        if "policy" in query_text.lower():
            return [{"product_id": 2, "product_name": "Silent Keyboard Pro", "total_weight": 3}]
        return []

    def fetch_events(self, *, user_id=None, session_id=None, limit=20):
        if user_id == 77 or session_id == "sess-1":
            return [
                {"event_type": "cart_item_added", "product_id": 2, "signal_weight": 4, "query_text": ""},
                {"event_type": "product_viewed", "product_id": 2, "signal_weight": 4, "query_text": "silent keyboard"},
                {"event_type": "search_performed", "product_id": None, "signal_weight": 1, "query_text": "keyboard policy"},
                {"event_type": "chat_message_sent", "product_id": None, "signal_weight": 2, "query_text": "i need a quiet keyboard"},
            ]
        return []


class StubOpenAIClient:
    enabled = False

    def generate_answer(self, *, prompt, question):
        return None

    def embed_texts(self, texts):
        return None


class RecommendationServiceTest(TestCase):
    def setUp(self):
        self.service = RecommendationService(
            product_client=StubProductClient(),
            interaction_client=StubInteractionClient(),
            cart_client=StubCartClient(),
        )

    def test_home_recommendation_uses_interest_and_graph_signals(self):
        payload = self.service.recommend_home(user_id=77, session_id="sess-1", limit=3)

        self.assertEqual(payload["context"]["strategy"], "home")
        self.assertEqual(payload["items"][0]["product"]["id"], 2)
        self.assertIn("graph_neighbor", payload["items"][0]["reason_codes"])
        self.assertIn("recent_interest_category", payload["items"][0]["reason_codes"])
        self.assertEqual(payload["context"]["profile_snapshot"]["top_categories"][0]["category_id"], 10)

    def test_profile_snapshot_returns_recent_queries_and_viewed_products(self):
        payload = self.service.get_profile_snapshot(user_id=77)

        snapshot = payload["profile_snapshot"]
        self.assertEqual(snapshot["recent_viewed_product_ids"], [1, 4])
        self.assertEqual(snapshot["recent_queries"], ["quiet keyboard"])
        self.assertEqual(snapshot["recent_clicked_product_ids"], [1])
        self.assertEqual(snapshot["recent_carted_product_ids"], [1])
        self.assertEqual(snapshot["funnel_stage"], "interested")
        self.assertGreater(snapshot["purchase_intent_score"], 0)

    def test_product_detail_excludes_current_product_and_keeps_related_items(self):
        payload = self.service.recommend_product_detail(product_id=1, user_id=77, limit=3)

        returned_ids = [item["product"]["id"] for item in payload["items"]]
        self.assertNotIn(1, returned_ids)
        self.assertEqual(returned_ids[0], 2)
        self.assertIn("same_category", payload["items"][0]["reason_codes"])

    def test_cart_recommendation_excludes_cart_products_and_falls_back_when_empty(self):
        cart_payload = self.service.recommend_cart(session_id="sess-1", user_id=77, limit=3)
        fallback_payload = self.service.recommend_cart(session_id="empty", limit=2)

        cart_ids = [item["product"]["id"] for item in cart_payload["items"]]
        self.assertNotIn(1, cart_ids)
        self.assertNotIn(4, cart_ids)
        self.assertEqual(cart_payload["items"][0]["product"]["id"], 2)
        self.assertEqual(fallback_payload["context"]["strategy"], "cart-fallback-home")

    def test_home_recommendation_applies_deep_model_score_when_loaded(self):
        service = RecommendationService(
            product_client=StubProductClient(),
            interaction_client=StubInteractionClient(),
            cart_client=StubCartClient(),
            deep_model_runtime=StubDeepModelRuntime(scores=[0.1, 0.95, 0.2, 0.05]),
        )

        payload = service.recommend_home(user_id=77, session_id="sess-1", limit=3)

        self.assertEqual(payload["context"]["deep_model"]["fallback_mode"], "deep-model")
        self.assertTrue(payload["context"]["deep_model"]["applied"])
        self.assertEqual(payload["items"][0]["product"]["id"], 2)
        self.assertIn("deep_model", payload["items"][0]["reason_codes"])
        self.assertIsNotNone(payload["items"][0]["deep_model_score"])
        self.assertIn("deep_model_bonus", payload["items"][0]["source_signals"])

    def test_home_recommendation_falls_back_when_deep_model_unavailable(self):
        service = RecommendationService(
            product_client=StubProductClient(),
            interaction_client=StubInteractionClient(),
            cart_client=StubCartClient(),
            deep_model_runtime=StubDeepModelRuntime(enabled=True, loaded=False),
        )

        payload = service.recommend_home(user_id=77, session_id="sess-1", limit=2)

        self.assertFalse(payload["context"]["deep_model"]["applied"])
        self.assertEqual(payload["context"]["deep_model"]["fallback_mode"], "heuristic-only-model-unavailable")
        self.assertNotIn("deep_model", payload["items"][0]["reason_codes"])


@override_settings(RECOMMENDATION_LIMIT_DEFAULT=10, RECOMMENDATION_LIMIT_MAX=20)
class RecommendationViewTest(TestCase):
    def setUp(self):
        self.factory = APIRequestFactory()
        self.home_view = RecommendationViewSet.as_view({"get": "home"})
        self.product_detail_view = RecommendationViewSet.as_view({"get": "product_detail"})
        self.cart_view = RecommendationViewSet.as_view({"get": "cart"})
        self.profile_view = RecommendationViewSet.as_view({"get": "profile_snapshot"})
        self.profile_snapshot_view = ProfileViewSet.as_view({"get": "snapshot"})
        self.model_status_view = ModelStatusViewSet.as_view({"get": "status"})

    def _service(self):
        return RecommendationService(
            product_client=StubProductClient(),
            interaction_client=StubInteractionClient(),
            cart_client=StubCartClient(),
        )

    def test_home_endpoint_returns_ranked_items(self):
        service = self._service()

        class StubbedRecommendationViewSet(RecommendationViewSet):
            service_class = lambda self: service  # type: ignore[assignment]

        request = self.factory.get("/api/ai/recommend/home", {"user_id": 77, "limit": 2})
        view = StubbedRecommendationViewSet.as_view({"get": "home"})
        response = view(request)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data["items"]), 2)

    def test_product_detail_requires_product_id(self):
        request = self.factory.get("/api/ai/recommend/product-detail")
        response = self.product_detail_view(request)

        self.assertEqual(response.status_code, 400)

    def test_cart_endpoint_requires_session(self):
        request = self.factory.get("/api/ai/recommend/cart")
        response = self.cart_view(request)

        self.assertEqual(response.status_code, 400)

    def test_viewset_uses_configured_service_class(self):
        class DummyService:
            def recommend_home(self, **kwargs):
                return {"context": kwargs, "items": []}

        class StubbedRecommendationViewSet(RecommendationViewSet):
            service_class = DummyService

        view = StubbedRecommendationViewSet.as_view({"get": "home"})
        request = self.factory.get("/api/ai/recommend/home", {"session_id": "sess-1"})
        response = view(request)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["context"]["session_id"], "sess-1")

    def test_profile_snapshot_endpoint_returns_snapshot(self):
        service = self._service()

        class StubbedRecommendationViewSet(RecommendationViewSet):
            service_class = lambda self: service  # type: ignore[assignment]

        request = self.factory.get("/api/ai/recommend/profile/snapshot", {"user_id": 77}, HTTP_X_REQUEST_ID="req-123")
        view = StubbedRecommendationViewSet.as_view({"get": "profile_snapshot"})
        response = view(request)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["profile_snapshot"]["top_categories"][0]["category_id"], 10)
        self.assertIn("funnel_stage", response.data["profile_snapshot"])

    def test_standalone_profile_snapshot_endpoint_returns_behavioral_profile(self):
        service = self._service()

        class StubbedProfileViewSet(ProfileViewSet):
            service_class = lambda self: service  # type: ignore[assignment]

        request = self.factory.get("/api/ai/profile/snapshot", {"session_id": "sess-1"})
        view = StubbedProfileViewSet.as_view({"get": "snapshot"})
        response = view(request)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["profile_snapshot"]["scope_type"], "session")
        self.assertGreater(response.data["profile_snapshot"]["purchase_intent_score"], 0)

    def test_model_status_endpoint_reports_behavioral_profile_runtime(self):
        service = RecommendationService(
            product_client=StubProductClient(),
            interaction_client=StubInteractionClient(),
            cart_client=StubCartClient(),
            deep_model_runtime=StubDeepModelRuntime(),
        )

        class StubbedModelStatusViewSet(ModelStatusViewSet):
            service_class = lambda self: service  # type: ignore[assignment]

        request = self.factory.get("/api/ai/models/status")
        view = StubbedModelStatusViewSet.as_view({"get": "status"})
        response = view(request)

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.data["behavioral_profile_enabled"])
        self.assertEqual(response.data["scoring_mode"], "hybrid-deep-heuristic")
        self.assertTrue(response.data["deep_model"]["loaded"])
        self.assertEqual(response.data["deep_model"]["model_version"], "plan11b-mlp-v1")
        self.assertTrue(response.data["integrations"]["chat"]["prompt_context"])
        self.assertIn("purchase_intent_score", response.data["profile_fields"])


@override_settings(KNOWLEDGE_BASE_DIR=KNOWLEDGE_BASE_DIR)
class ChatbotServiceTest(TestCase):
    def setUp(self):
        self.interaction_client = StubInteractionContextClient()
        self.service = ChatbotService(
            product_client=StubProductClient(),
            order_client=StubOrderClient(),
            cart_client=StubCartClient(),
            interaction_client=self.interaction_client,
            openai_client=StubOpenAIClient(),
        )

    def test_chat_routes_order_status_to_realtime_api(self):
        payload = self.service.chat(
            message="What is my order status?",
            session_id="sess-1",
        )

        self.assertTrue(payload["used_realtime_api"])
        self.assertEqual(payload["retrieval_mode"], "realtime-order")
        self.assertIn("Order #99", payload["answer"])

    def test_chat_routes_price_and_stock_to_product_runtime(self):
        payload = self.service.chat(
            message="What is the current price and stock of Silent Keyboard Pro?",
        )

        self.assertTrue(payload["used_realtime_api"])
        self.assertEqual(payload["retrieval_mode"], "realtime-product")
        self.assertIn("109.00", payload["answer"])
        self.assertIn("in stock", payload["answer"])

    def test_retrieve_returns_sources_and_graph_context(self):
        payload = self.service.retrieve(
            message="Tell me the return policy for keyboards",
            user_id=77,
            limit=3,
        )

        self.assertEqual(payload["retrieval_mode"], "lexical")
        self.assertTrue(payload["sources"])
        self.assertTrue(payload["used_graph_context"])
        self.assertEqual(payload["graph_context"][0]["type"], "user_interest")
        self.assertEqual(payload["profile_snapshot"]["recent_viewed_product_ids"], [2])
        self.assertEqual(payload["profile_snapshot"]["recent_carted_product_ids"], [2])
        self.assertEqual(payload["profile_snapshot"]["recent_chat_cues"], ["i need a quiet keyboard"])
        self.assertGreater(payload["profile_snapshot"]["purchase_intent_score"], 0)

    def test_chat_emits_chat_started_for_new_scope(self):
        self.service.chat(message="Need keyboard recommendations", user_id=999)

        event_types = [event["event_type"] for event in self.interaction_client.emitted_events]
        self.assertEqual(event_types[:2], ["chat_started", "chat_message_sent"])

    def test_chat_does_not_emit_events_without_scope(self):
        self.service.chat(message="Need keyboard recommendations")

        self.assertEqual(self.interaction_client.emitted_events, [])


@override_settings(KNOWLEDGE_BASE_DIR=KNOWLEDGE_BASE_DIR)
class ChatViewTest(TestCase):
    def setUp(self):
        self.factory = APIRequestFactory()
        self.chat_view = ChatViewSet.as_view({"post": "create"})
        self.retrieve_view = ChatViewSet.as_view({"post": "retrieve_context"})

    def _service(self):
        return ChatbotService(
            product_client=StubProductClient(),
            order_client=StubOrderClient(),
            cart_client=StubCartClient(),
            interaction_client=StubInteractionContextClient(),
            openai_client=StubOpenAIClient(),
        )

    def test_chat_endpoint_returns_answer(self):
        service = self._service()

        class StubbedChatViewSet(ChatViewSet):
            service_class = lambda self: service  # type: ignore[assignment]

        request = self.factory.post(
            "/api/ai/chat",
            {"message": "What is my order status?", "session_id": "sess-1"},
            format="json",
        )
        view = StubbedChatViewSet.as_view({"post": "create"})
        response = view(request)

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.data["used_realtime_api"])

    def test_retrieve_endpoint_returns_grounded_context(self):
        service = self._service()

        class StubbedChatViewSet(ChatViewSet):
            service_class = lambda self: service  # type: ignore[assignment]

        request = self.factory.post(
            "/api/ai/chat/retrieve",
            {"message": "Explain the payment policy", "user_id": 77},
            format="json",
        )
        view = StubbedChatViewSet.as_view({"post": "retrieve_context"})
        response = view(request)

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.data["sources"])
        self.assertEqual(response.data["profile_snapshot"]["top_categories"][0]["category_id"], 10)


class RequestContextMiddlewareTest(TestCase):
    def test_assigns_request_id_and_response_header(self):
        factory = RequestFactory()
        request = factory.get("/api/ai/recommend/home", HTTP_X_REQUEST_ID="req-abc")

        middleware = RequestContextMiddleware(lambda req: HttpResponse("ok"))
        response = middleware(request)

        self.assertEqual(request.request_id, "req-abc")
        self.assertEqual(response["X-Request-ID"], "req-abc")


class BuildBehaviorProfileCommandTest(TestCase):
    def test_command_requires_actor_scope(self):
        with self.assertRaises(CommandError):
            call_command("build_behavior_profile")

    def test_command_outputs_profile_snapshot_json(self):
        class StubService:
            def get_profile_snapshot(self, *, user_id=None, session_id=None):
                return {
                    "user_id": user_id,
                    "session_id": session_id,
                    "profile_snapshot": {
                        "scope_type": "session" if session_id else "user",
                        "purchase_intent_score": 0.42,
                    },
                }

        output = StringIO()
        with patch(
            "recommendations.management.commands.build_behavior_profile.Command.service_class",
            StubService,
        ):
            call_command(
                "build_behavior_profile",
                "--session-id",
                "sess-command",
                "--pretty",
                stdout=output,
            )

        payload = json.loads(output.getvalue())
        self.assertEqual(payload["session_id"], "sess-command")
        self.assertEqual(payload["profile_snapshot"]["scope_type"], "session")


class DeepDatasetBuilderTest(TestCase):
    def _products(self):
        return [
            {
                "id": 1,
                "category_id": 10,
                "brand_id": 200,
                "product_type_id": 100,
                "base_price": "99.00",
                "has_stock": True,
                "is_active": True,
            },
            {
                "id": 2,
                "category_id": 11,
                "brand_id": 201,
                "product_type_id": 101,
                "base_price": "59.00",
                "has_stock": True,
                "is_active": True,
            },
        ]

    def _events(self):
        return [
            {
                "event_type": "product_viewed",
                "user_id": 7,
                "product_id": 1,
                "timestamp": "2026-04-01T10:00:00Z",
                "signal_weight": 1,
            },
            {
                "event_type": "cart_item_added",
                "user_id": 7,
                "product_id": 1,
                "timestamp": "2026-04-02T10:00:00Z",
                "signal_weight": 4,
            },
            {
                "event_type": "product_viewed",
                "user_id": 7,
                "product_id": 2,
                "timestamp": "2026-04-03T10:00:00Z",
                "signal_weight": 1,
            },
            {
                "event_type": "product_clicked",
                "user_id": 7,
                "product_id": 2,
                "timestamp": "2026-04-03T12:00:00Z",
                "signal_weight": 2,
            },
            {
                "event_type": "product_viewed",
                "session_id": "sess-a",
                "product_id": 2,
                "timestamp": "2026-04-04T09:00:00Z",
                "signal_weight": 1,
            },
            {
                "event_type": "product_clicked",
                "session_id": "sess-a",
                "product_id": 2,
                "timestamp": "2026-04-05T09:00:00Z",
                "signal_weight": 2,
            },
        ]

    def test_build_dataset_records_generates_labels(self):
        records = build_dataset_records(self._events(), self._products(), label_window_days=14)

        self.assertEqual(len(records), 3)
        pair_map = {(row["actor_key"], row["product_id"]): row for row in records}

        converted = pair_map[("user:7", 1)]
        weak_negative = pair_map[("user:7", 2)]

        self.assertEqual(converted["binary_label"], 1)
        self.assertGreaterEqual(converted["weighted_label"], 0.7)
        self.assertEqual(weak_negative["binary_label"], 0)
        self.assertEqual(weak_negative["weak_negative"], 1)
        self.assertIn("actor_purchase_intent_pre", converted)
        self.assertIn("item_popularity_pre", converted)

    def test_split_and_quality_report(self):
        records = build_dataset_records(self._events(), self._products(), label_window_days=14)
        splits, _ = split_samples_by_actor_time(records, train_ratio=0.6, valid_ratio=0.2)
        report = build_quality_report(records, splits)

        self.assertEqual(sum(len(rows) for rows in splits.values()), len(records))
        self.assertTrue(report["leakage_check"]["passed"])
        self.assertGreaterEqual(report["record_count"], 3)


class BuildRankingDatasetCommandTest(TestCase):
    def test_command_writes_dataset_outputs(self):
        events = [
            {
                "event_type": "product_viewed",
                "user_id": 7,
                "product_id": 1,
                "timestamp": "2026-04-01T10:00:00Z",
                "signal_weight": 1,
            },
            {
                "event_type": "cart_item_added",
                "user_id": 7,
                "product_id": 1,
                "timestamp": "2026-04-02T10:00:00Z",
                "signal_weight": 4,
            },
            {
                "event_type": "product_viewed",
                "session_id": "sess-a",
                "product_id": 2,
                "timestamp": "2026-04-04T09:00:00Z",
                "signal_weight": 1,
            },
        ]
        products = [
            {"id": 1, "category_id": 10, "brand_id": 200, "product_type_id": 100, "base_price": "99.00", "has_stock": True, "is_active": True},
            {"id": 2, "category_id": 11, "brand_id": 201, "product_type_id": 101, "base_price": "59.00", "has_stock": True, "is_active": True},
        ]

        class StubProductClient:
            def fetch_products(self):
                return products

        class StubInteractionClient:
            def fetch_all_events(self, *, limit=200, date_from=None, date_to=None):
                return events

        with TemporaryDirectory() as tmp_dir:
            with patch(
                "recommendations.management.commands.build_ranking_dataset.Command.product_client_class",
                StubProductClient,
            ), patch(
                "recommendations.management.commands.build_ranking_dataset.Command.interaction_client_class",
                StubInteractionClient,
            ):
                call_command("build_ranking_dataset", "--output-dir", tmp_dir)

            self.assertTrue((Path(tmp_dir) / "dataset_train.jsonl").exists())
            self.assertTrue((Path(tmp_dir) / "dataset_valid.jsonl").exists())
            self.assertTrue((Path(tmp_dir) / "dataset_test.jsonl").exists())
            self.assertTrue((Path(tmp_dir) / "protocol.json").exists())
            self.assertTrue((Path(tmp_dir) / "quality_report.json").exists())


class InteractionAnalyticsClientPaginationTest(TestCase):
    def test_fetch_all_events_pages_until_limit(self):
        first_page = [
            {
                "id": 1000 - idx,
                "timestamp": "2026-04-03T10:00:00Z",
                "event_type": "product_viewed",
            }
            for idx in range(200)
        ]
        second_page = [
            {"id": 777, "timestamp": "2026-04-01T10:00:00Z", "event_type": "cart_item_added"},
        ]
        pages = [first_page, second_page]

        class FakeClient(InteractionAnalyticsClient):
            def __init__(self):
                self.calls = []

            def _get_optional(self, path, params=None, default=None):
                self.calls.append({"path": path, "params": dict(params or {})})
                index = len(self.calls) - 1
                if index < len(pages):
                    return pages[index]
                return []

        client = FakeClient()
        rows = client.fetch_all_events(limit=201)

        self.assertEqual(len(rows), 201)
        self.assertEqual(rows[0]["id"], 1000)
        self.assertEqual(rows[-1]["id"], 777)
        self.assertEqual(len(client.calls), 2)
        self.assertEqual(client.calls[0]["params"]["limit"], 200)
        self.assertIn("date_to", client.calls[1]["params"])

    def test_fetch_all_events_respects_requested_limit(self):
        class FakeClient(InteractionAnalyticsClient):
            def __init__(self):
                self.calls = []

            def _get_optional(self, path, params=None, default=None):
                self.calls.append({"path": path, "params": dict(params or {})})
                return [
                    {"id": 10, "timestamp": "2026-04-03T10:00:00Z", "event_type": "product_viewed"},
                    {"id": 9, "timestamp": "2026-04-02T10:00:00Z", "event_type": "product_clicked"},
                ]

        client = FakeClient()
        rows = client.fetch_all_events(limit=1)

        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["id"], 10)
        self.assertEqual(client.calls[0]["params"]["limit"], 1)


class TrainRankingModelCommandTest(TestCase):
    def _row(self, *, actor_key, scope_type, product_id, snapshot_time, binary_label, weighted_label):
        return {
            "sample_id": "%s|%s|%s" % (actor_key, product_id, snapshot_time),
            "actor_key": actor_key,
            "scope_type": scope_type,
            "product_id": product_id,
            "snapshot_time": snapshot_time,
            "feature_cutoff_time": snapshot_time,
            "item_category_id": 10 if product_id % 2 else 11,
            "item_brand_id": 200 if product_id % 2 else 201,
            "item_product_type_id": 100,
            "item_price_band": "mid" if product_id % 2 else "budget",
            "item_has_stock": 1,
            "item_is_active": 1,
            "actor_top_category_id": 10,
            "actor_top_brand_id": 200,
            "actor_purchase_intent_pre": 0.6 if binary_label else 0.2,
            "actor_event_count_1d": 1,
            "actor_event_count_7d": 3,
            "actor_event_count_30d": 6,
            "actor_view_count_7d": 2,
            "actor_click_count_7d": 1,
            "actor_cart_count_7d": 1 if binary_label else 0,
            "actor_purchase_count_30d": 1 if binary_label else 0,
            "actor_item_event_count_30d": 2,
            "item_popularity_pre": 1.5,
            "interaction_overlap_pre": 1.0,
            "graph_neighbor_score_pre": 0.0,
            "binary_label": binary_label,
            "weighted_label": weighted_label,
            "weak_negative": 0 if binary_label else 1,
            "label_event_type": "order_paid" if binary_label else "product_clicked",
            "label_timestamp": snapshot_time,
            "label_window_end": "2026-04-20T00:00:00Z",
            "split": "train",
        }

    def _write_jsonl(self, path, rows):
        with path.open("w", encoding="utf-8") as handle:
            for row in rows:
                handle.write(json.dumps(row, ensure_ascii=True, sort_keys=True))
                handle.write("\n")

    def test_train_ranking_model_writes_artifacts(self):
        with TemporaryDirectory() as tmp_dir:
            dataset_dir = Path(tmp_dir) / "11a"
            output_dir = Path(tmp_dir) / "11b"
            dataset_dir.mkdir(parents=True, exist_ok=True)

            train_rows = [
                self._row(
                    actor_key="user:1",
                    scope_type="user",
                    product_id=1,
                    snapshot_time="2026-04-01T10:00:00Z",
                    binary_label=1,
                    weighted_label=1.0,
                ),
                self._row(
                    actor_key="user:2",
                    scope_type="user",
                    product_id=2,
                    snapshot_time="2026-04-01T11:00:00Z",
                    binary_label=0,
                    weighted_label=0.4,
                ),
                self._row(
                    actor_key="session:s-3",
                    scope_type="session",
                    product_id=3,
                    snapshot_time="2026-04-02T09:00:00Z",
                    binary_label=1,
                    weighted_label=1.0,
                ),
                self._row(
                    actor_key="session:s-4",
                    scope_type="session",
                    product_id=4,
                    snapshot_time="2026-04-02T10:00:00Z",
                    binary_label=0,
                    weighted_label=0.2,
                ),
            ]
            valid_rows = [
                self._row(
                    actor_key="user:5",
                    scope_type="user",
                    product_id=5,
                    snapshot_time="2026-04-03T10:00:00Z",
                    binary_label=1,
                    weighted_label=1.0,
                )
            ]
            test_rows = [
                self._row(
                    actor_key="session:s-6",
                    scope_type="session",
                    product_id=6,
                    snapshot_time="2026-04-03T11:00:00Z",
                    binary_label=0,
                    weighted_label=0.4,
                )
            ]

            self._write_jsonl(dataset_dir / "dataset_train.jsonl", train_rows)
            self._write_jsonl(dataset_dir / "dataset_valid.jsonl", valid_rows)
            self._write_jsonl(dataset_dir / "dataset_test.jsonl", test_rows)
            (dataset_dir / "protocol.json").write_text(
                json.dumps(
                    {
                        "plan": "11A",
                        "feature_version": "plan11a-v1",
                        "record_count": len(train_rows) + len(valid_rows) + len(test_rows),
                    },
                    ensure_ascii=True,
                    indent=2,
                    sort_keys=True,
                ),
                encoding="utf-8",
            )

            call_command(
                "train_ranking_model",
                "--dataset-dir",
                str(dataset_dir),
                "--output-dir",
                str(output_dir),
                "--epochs",
                "8",
                "--patience",
                "4",
                "--batch-size",
                "2",
                "--hidden-dims",
                "8,4",
            )

            self.assertTrue((output_dir / "model_weights.npz").exists())
            self.assertTrue((output_dir / "preprocessing_config.json").exists())
            self.assertTrue((output_dir / "training_config.json").exists())
            self.assertTrue((output_dir / "metrics_report.json").exists())
            self.assertTrue((output_dir / "model_metadata.json").exists())
            self.assertTrue((output_dir / "artifact_checksum.sha256").exists())

            metrics = json.loads((output_dir / "metrics_report.json").read_text(encoding="utf-8"))
            self.assertIn("auc", metrics["test"])
            self.assertIn("f1", metrics["test"])
            self.assertIn("recall_at_10", metrics["test"])

    def test_train_ranking_model_requires_non_empty_split_files(self):
        with TemporaryDirectory() as tmp_dir:
            dataset_dir = Path(tmp_dir) / "11a"
            dataset_dir.mkdir(parents=True, exist_ok=True)
            (dataset_dir / "dataset_train.jsonl").write_text("", encoding="utf-8")
            (dataset_dir / "dataset_valid.jsonl").write_text("", encoding="utf-8")
            (dataset_dir / "dataset_test.jsonl").write_text("", encoding="utf-8")

            with self.assertRaises(CommandError):
                call_command("train_ranking_model", "--dataset-dir", str(dataset_dir))

            self.assertEqual(load_jsonl(dataset_dir / "dataset_train.jsonl"), [])
