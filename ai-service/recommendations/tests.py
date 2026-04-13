from pathlib import Path

from django.test import TestCase, override_settings
from django.http import HttpResponse
from django.test import RequestFactory
from rest_framework.test import APIRequestFactory

from ai_service.middleware import RequestContextMiddleware

from .chat_services import ChatbotService
from .chat_views import ChatViewSet
from .services import RecommendationService
from .views import RecommendationViewSet


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
            return {"items": [{"product_id": 1}, {"product_id": 4}]}
        return {"items": []}


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
                {"event_type": "product_viewed", "product_id": 2, "signal_weight": 4, "query_text": "silent keyboard"},
                {"event_type": "search_performed", "product_id": None, "signal_weight": 1, "query_text": "keyboard policy"},
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


@override_settings(RECOMMENDATION_LIMIT_DEFAULT=10, RECOMMENDATION_LIMIT_MAX=20)
class RecommendationViewTest(TestCase):
    def setUp(self):
        self.factory = APIRequestFactory()
        self.home_view = RecommendationViewSet.as_view({"get": "home"})
        self.product_detail_view = RecommendationViewSet.as_view({"get": "product_detail"})
        self.cart_view = RecommendationViewSet.as_view({"get": "cart"})
        self.profile_view = RecommendationViewSet.as_view({"get": "profile_snapshot"})

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
