import logging
from collections import Counter
from copy import deepcopy
from decimal import Decimal, InvalidOperation

import requests
from django.conf import settings

from .profile_utils import build_profile_snapshot

logger = logging.getLogger(__name__)


class ServiceClientError(Exception):
    def __init__(self, message, status_code=502):
        super().__init__(message)
        self.status_code = status_code


class ProductCatalogClient:
    def __init__(self):
        self.base_url = getattr(settings, "PRODUCT_SERVICE_URL", "").rstrip("/")
        self.timeout = getattr(settings, "REQUEST_TIMEOUT_SECONDS", 10)

    def _get(self, path, params=None):
        if not self.base_url:
            raise ServiceClientError("PRODUCT_SERVICE_URL is not configured.")
        try:
            response = requests.get(
                f"{self.base_url}{path}",
                params=params or {},
                timeout=self.timeout,
            )
        except requests.RequestException as exc:
            raise ServiceClientError(f"Product service request failed: {exc}") from exc
        if response.status_code >= 400:
            raise ServiceClientError("Product service returned an error.", status_code=response.status_code)
        return response.json()

    def fetch_products(self):
        return self._get("/api/products/")

    def fetch_product(self, product_id):
        return self._get(f"/api/products/{int(product_id)}/")


class InteractionAnalyticsClient:
    def __init__(self):
        self.base_url = getattr(settings, "INTERACTION_SERVICE_URL", "").rstrip("/")
        self.timeout = getattr(settings, "REQUEST_TIMEOUT_SECONDS", 10)

    def _get_optional(self, path, params=None, default=None):
        if not self.base_url:
            return [] if default is None else default
        try:
            response = requests.get(
                f"{self.base_url}{path}",
                params=params or {},
                timeout=self.timeout,
            )
            response.raise_for_status()
        except requests.RequestException as exc:
            logger.warning("Interaction service request failed for %s: %s", path, exc)
            return [] if default is None else default
        return response.json()

    def fetch_events(self, *, user_id=None, session_id=None, limit=25):
        params = {"limit": limit}
        if user_id is not None:
            params["user_id"] = int(user_id)
        if session_id:
            params["session_id"] = session_id
        return self._get_optional("/api/interactions/events", params=params, default=[])

    def fetch_product_gaps(self):
        return self._get_optional("/api/interactions/events/product_gaps", default=[])

    def fetch_user_interest(self, *, user_id=None, session_id=None, limit=5):
        params = {"limit": limit}
        if user_id is not None:
            params["user_id"] = int(user_id)
        elif session_id:
            params["session_id"] = session_id
        else:
            return []
        return self._get_optional("/api/interactions/graph/user_interest", params=params, default=[])

    def fetch_product_neighbors(self, *, product_id, limit=6):
        return self._get_optional(
            "/api/interactions/graph/product_neighbors",
            params={"product_id": int(product_id), "limit": limit},
            default=[],
        )

    def fetch_similar_users(self, *, user_id=None, session_id=None, limit=3):
        params = {"limit": limit}
        if user_id is not None:
            params["user_id"] = int(user_id)
        elif session_id:
            params["session_id"] = session_id
        else:
            return []
        return self._get_optional("/api/interactions/graph/similar_users", params=params, default=[])


class CartClient:
    def __init__(self):
        self.base_url = getattr(settings, "CART_SERVICE_URL", "").rstrip("/")
        self.timeout = getattr(settings, "REQUEST_TIMEOUT_SECONDS", 10)

    def fetch_current_cart(self, session_id):
        if not self.base_url:
            raise ServiceClientError("CART_SERVICE_URL is not configured.")
        try:
            response = requests.get(
                f"{self.base_url}/api/cart/current",
                headers={"X-Cart-Session-Key": str(session_id)},
                timeout=self.timeout,
            )
        except requests.RequestException as exc:
            raise ServiceClientError(f"Cart service request failed: {exc}") from exc
        if response.status_code >= 400:
            raise ServiceClientError("Cart service returned an error.", status_code=response.status_code)
        return response.json()


class RecommendationService:
    def __init__(self, product_client=None, interaction_client=None, cart_client=None):
        self.product_client = product_client or ProductCatalogClient()
        self.interaction_client = interaction_client or InteractionAnalyticsClient()
        self.cart_client = cart_client or CartClient()

    def recommend_home(self, *, user_id=None, session_id=None, limit=10):
        products = self._load_products()
        score_cards = self._empty_score_cards(products)
        self._apply_popularity(score_cards, self.interaction_client.fetch_product_gaps())

        actor_context = self._build_actor_context(products, user_id=user_id, session_id=session_id)
        self._apply_actor_context(score_cards, products, actor_context)

        items = self._rank(products, score_cards, limit=limit)
        return {
            "context": {
                "strategy": "home",
                "user_id": user_id,
                "session_id": session_id,
                "recent_product_ids": actor_context["recent_product_ids"],
                "profile_snapshot": actor_context["profile_snapshot"],
            },
            "items": items,
        }

    def recommend_product_detail(self, *, product_id, user_id=None, session_id=None, limit=10):
        products = self._load_products()
        if product_id not in products:
            current_product = self.product_client.fetch_product(product_id)
            if not current_product.get("is_active", False):
                raise ServiceClientError("Product is not available.", status_code=404)
            products[int(product_id)] = current_product

        current_product = products[int(product_id)]
        score_cards = self._empty_score_cards(products)
        self._apply_popularity(score_cards, self.interaction_client.fetch_product_gaps())
        self._apply_product_context(score_cards, products, current_product)
        self._apply_graph_neighbors(score_cards, [int(product_id)])

        actor_context = self._build_actor_context(products, user_id=user_id, session_id=session_id)
        self._apply_actor_context(score_cards, products, actor_context)

        items = self._rank(products, score_cards, limit=limit, exclude_ids={int(product_id)})
        return {
            "context": {
                "strategy": "product-detail",
                "product_id": int(product_id),
                "user_id": user_id,
                "session_id": session_id,
                "profile_snapshot": actor_context["profile_snapshot"],
            },
            "items": items,
        }

    def recommend_cart(self, *, session_id, user_id=None, limit=10):
        cart_payload = self.cart_client.fetch_current_cart(session_id)
        cart_items = cart_payload.get("items", [])
        cart_product_ids = [int(item["product_id"]) for item in cart_items if item.get("product_id") is not None]
        if not cart_product_ids:
            response = self.recommend_home(user_id=user_id, session_id=session_id, limit=limit)
            response["context"]["strategy"] = "cart-fallback-home"
            response["context"]["cart_product_ids"] = []
            return response

        products = self._load_products()
        score_cards = self._empty_score_cards(products)
        self._apply_popularity(score_cards, self.interaction_client.fetch_product_gaps())

        for cart_product_id in cart_product_ids:
            product = products.get(cart_product_id)
            if product:
                self._apply_product_context(score_cards, products, product)
        self._apply_graph_neighbors(score_cards, cart_product_ids, reason_code="cart_graph_neighbor", source_key="cart_graph")

        actor_context = self._build_actor_context(products, user_id=user_id, session_id=session_id)
        self._apply_actor_context(score_cards, products, actor_context)

        items = self._rank(products, score_cards, limit=limit, exclude_ids=set(cart_product_ids))
        return {
            "context": {
                "strategy": "cart",
                "session_id": session_id,
                "user_id": user_id,
                "cart_product_ids": cart_product_ids,
                "profile_snapshot": actor_context["profile_snapshot"],
            },
            "items": items,
        }

    def get_profile_snapshot(self, *, user_id=None, session_id=None):
        products = self._load_products()
        actor_context = self._build_actor_context(products, user_id=user_id, session_id=session_id)
        return {
            "user_id": user_id,
            "session_id": session_id,
            "profile_snapshot": actor_context["profile_snapshot"],
        }

    def _load_products(self):
        raw_products = self.product_client.fetch_products()
        products = {}
        for product in raw_products:
            if not product.get("is_active", False):
                continue
            products[int(product["id"])] = deepcopy(product)
        return products

    def _empty_score_cards(self, products):
        return {
            product_id: {
                "score": 0.0,
                "reason_codes": set(),
                "source_signals": {},
            }
            for product_id in products
        }

    def _build_actor_context(self, products, *, user_id=None, session_id=None):
        if user_id is None and not session_id:
            return {
                "interest_rows": [],
                "similar_users": [],
                "category_counter": Counter(),
                "brand_counter": Counter(),
                "price_points": [],
                "recent_product_ids": [],
                "profile_snapshot": build_profile_snapshot({}, [], []),
                "scope_is_user": False,
            }

        events = self.interaction_client.fetch_events(user_id=user_id, session_id=session_id, limit=20)
        recent_product_ids = []
        seen_product_ids = set()
        category_counter = Counter()
        brand_counter = Counter()
        price_points = []

        for event in events:
            product_id = event.get("product_id")
            if product_id in products:
                product = products[product_id]
                signal_weight = max(float(event.get("signal_weight", 1) or 1), 1.0)
                category_id = product.get("category_id")
                brand_id = product.get("brand_id")
                if category_id is not None:
                    category_counter[int(category_id)] += signal_weight
                if brand_id is not None:
                    brand_counter[int(brand_id)] += signal_weight
                price = self._to_decimal(product.get("base_price"))
                if price is not None:
                    price_points.append(price)
                if product_id not in seen_product_ids:
                    recent_product_ids.append(int(product_id))
                    seen_product_ids.add(int(product_id))

        interest_rows = self.interaction_client.fetch_user_interest(user_id=user_id, session_id=session_id, limit=5)
        profile_snapshot = build_profile_snapshot(products, events, interest_rows)
        return {
            "interest_rows": interest_rows,
            "similar_users": self.interaction_client.fetch_similar_users(user_id=user_id, session_id=session_id, limit=3),
            "category_counter": category_counter,
            "brand_counter": brand_counter,
            "price_points": price_points,
            "recent_product_ids": recent_product_ids,
            "profile_snapshot": profile_snapshot,
            "scope_is_user": user_id is not None,
        }

    def _apply_actor_context(self, score_cards, products, actor_context):
        self._apply_interest_rows(score_cards, products, actor_context["interest_rows"])
        self._apply_recent_affinity(
            score_cards,
            products,
            category_counter=actor_context["category_counter"],
            brand_counter=actor_context["brand_counter"],
            price_points=actor_context["price_points"],
        )
        self._apply_graph_neighbors(score_cards, actor_context["recent_product_ids"])
        self._apply_similar_user_products(
            score_cards,
            products,
            actor_context["similar_users"],
            scope_is_user=actor_context["scope_is_user"],
        )
        self._apply_recent_product_bias(score_cards, products, actor_context["profile_snapshot"])

    def _apply_popularity(self, score_cards, product_gaps):
        for row in product_gaps:
            product_id = row.get("product_id")
            if product_id not in score_cards:
                continue
            score = (
                float(row.get("viewed_count", 0)) * 0.4
                + float(row.get("cart_added_count", 0)) * 1.2
                + float(row.get("paid_count", 0)) * 2.4
            )
            self._add_score(score_cards, product_id, score, "popular", "popularity")

    def _apply_interest_rows(self, score_cards, products, interest_rows):
        for row in interest_rows:
            category_id = row.get("category_id")
            if category_id is None:
                continue
            bonus = min(float(row.get("total_weight", 0)) * 0.35, 5.0)
            for product_id, product in products.items():
                if product.get("category_id") == category_id:
                    self._add_score(
                        score_cards,
                        product_id,
                        bonus,
                        "recent_interest_category",
                        "category_interest",
                    )

    def _apply_recent_affinity(self, score_cards, products, *, category_counter, brand_counter, price_points):
        median_price = None
        if price_points:
            sorted_prices = sorted(price_points)
            median_price = sorted_prices[len(sorted_prices) // 2]

        for product_id, product in products.items():
            category_id = product.get("category_id")
            brand_id = product.get("brand_id")
            if category_id in category_counter:
                self._add_score(
                    score_cards,
                    product_id,
                    min(category_counter[category_id] * 0.25, 3.5),
                    "recent_interest_category",
                    "recent_category",
                )
            if brand_id in brand_counter:
                self._add_score(
                    score_cards,
                    product_id,
                    min(brand_counter[brand_id] * 0.2, 2.0),
                    "recent_interest_brand",
                    "recent_brand",
                )
            if median_price is not None:
                price = self._to_decimal(product.get("base_price"))
                if price is not None and self._is_within_band(price, median_price, 0.25):
                    self._add_score(
                        score_cards,
                        product_id,
                        0.9,
                        "price_band_match",
                        "price_affinity",
                    )

    def _apply_product_context(self, score_cards, products, seed_product):
        seed_id = int(seed_product["id"])
        seed_category = seed_product.get("category_id")
        seed_brand = seed_product.get("brand_id")
        seed_price = self._to_decimal(seed_product.get("base_price"))

        for product_id, product in products.items():
            if product_id == seed_id:
                continue
            if seed_category is not None and product.get("category_id") == seed_category:
                self._add_score(score_cards, product_id, 3.0, "same_category", "product_context")
            if seed_brand is not None and product.get("brand_id") == seed_brand:
                self._add_score(score_cards, product_id, 1.5, "same_brand", "product_context")
            price = self._to_decimal(product.get("base_price"))
            if seed_price is not None and price is not None and self._is_within_band(price, seed_price, 0.2):
                self._add_score(score_cards, product_id, 1.2, "price_band_match", "product_context")

    def _apply_graph_neighbors(self, score_cards, seed_product_ids, reason_code="graph_neighbor", source_key="graph_neighbor"):
        for seed_product_id in seed_product_ids[:5]:
            for row in self.interaction_client.fetch_product_neighbors(product_id=seed_product_id, limit=6):
                product_id = row.get("product_id")
                if product_id not in score_cards:
                    continue
                similarity_score = min(float(row.get("similarity_score", 0)) * 0.5, 6.0)
                shared_bonus = min(float(row.get("shared_actor_count", 0)) * 0.3, 1.5)
                self._add_score(
                    score_cards,
                    product_id,
                    similarity_score + shared_bonus,
                    reason_code,
                    source_key,
                )

    def _apply_similar_user_products(self, score_cards, products, similar_users, *, scope_is_user):
        for row in similar_users[:3]:
            actor_id = row.get("actor_id")
            similarity_score = min(float(row.get("similarity_score", 0)) * 0.15, 2.0)
            if actor_id in (None, "") or similarity_score <= 0:
                continue
            if scope_is_user:
                events = self.interaction_client.fetch_events(user_id=actor_id, limit=10)
            else:
                events = self.interaction_client.fetch_events(session_id=actor_id, limit=10)
            for event in events:
                product_id = event.get("product_id")
                if product_id in products:
                    self._add_score(
                        score_cards,
                        product_id,
                        similarity_score,
                        "similar_user_interest",
                        "similar_user",
                    )

    def _rank(self, products, score_cards, *, limit, exclude_ids=None):
        exclude_ids = exclude_ids or set()
        ranked = []
        for product_id, product in products.items():
            if product_id in exclude_ids:
                continue
            if not product.get("has_stock", False):
                continue
            card = score_cards.get(product_id) or {"score": 0.0, "reason_codes": set(), "source_signals": {}}
            final_score = card["score"]
            if final_score <= 0:
                final_score = 0.1
                card = {
                    "score": final_score,
                    "reason_codes": {"catalog_fallback"},
                    "source_signals": {"catalog_fallback": 0.1},
                }
            ranked.append(
                {
                    "product": self._serialize_product(product),
                    "score": round(final_score, 2),
                    "reason_codes": sorted(card["reason_codes"]),
                    "source_signals": {
                        key: round(float(value), 2)
                        for key, value in sorted(card["source_signals"].items())
                    },
                }
            )
        ranked.sort(
            key=lambda item: (
                -item["score"],
                -self._to_float(item["product"].get("stock")),
                item["product"]["id"],
            )
        )
        return ranked[:limit]

    def _apply_recent_product_bias(self, score_cards, products, profile_snapshot):
        recent_product_ids = profile_snapshot.get("recent_viewed_product_ids", [])
        if not recent_product_ids:
            return

        recent_categories = {
            products[product_id].get("category_id")
            for product_id in recent_product_ids
            if product_id in products and products[product_id].get("category_id") is not None
        }
        recent_brands = {
            products[product_id].get("brand_id")
            for product_id in recent_product_ids
            if product_id in products and products[product_id].get("brand_id") is not None
        }

        for product_id, product in products.items():
            if product_id in recent_product_ids:
                continue
            if product.get("category_id") in recent_categories:
                self._add_score(score_cards, product_id, 0.8, "profile_recent_view_match", "profile_recent_view")
            if product.get("brand_id") in recent_brands:
                self._add_score(score_cards, product_id, 0.5, "profile_recent_brand_match", "profile_recent_brand")

    def _serialize_product(self, product):
        return {
            "id": int(product["id"]),
            "name": product.get("name"),
            "slug": product.get("slug"),
            "short_description": product.get("short_description"),
            "category_id": product.get("category_id"),
            "brand_id": product.get("brand_id"),
            "base_price": str(product.get("base_price")),
            "stock": product.get("stock"),
            "has_stock": product.get("has_stock", False),
            "tags": product.get("tags", []),
        }

    def _add_score(self, score_cards, product_id, score, reason_code, source_key):
        if product_id not in score_cards or score <= 0:
            return
        score_cards[product_id]["score"] += float(score)
        score_cards[product_id]["reason_codes"].add(reason_code)
        score_cards[product_id]["source_signals"][source_key] = (
            score_cards[product_id]["source_signals"].get(source_key, 0.0) + float(score)
        )

    def _to_decimal(self, value):
        try:
            return Decimal(str(value))
        except (InvalidOperation, TypeError, ValueError):
            return None

    def _to_float(self, value):
        try:
            return float(value)
        except (TypeError, ValueError):
            return 0.0

    def _is_within_band(self, value, pivot, tolerance_ratio):
        tolerance = abs(pivot) * Decimal(str(tolerance_ratio))
        return (pivot - tolerance) <= value <= (pivot + tolerance)
