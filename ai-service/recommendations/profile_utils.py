from collections import Counter
from decimal import Decimal, InvalidOperation


RECENT_EVENT_FIELDS = {
    "product_viewed": "recent_viewed_product_ids",
    "product_clicked": "recent_clicked_product_ids",
    "cart_item_added": "recent_carted_product_ids",
    "cart_item_quantity_updated": "recent_carted_product_ids",
    "order_paid": "recent_purchased_product_ids",
    "order_completed": "recent_purchased_product_ids",
}

PRODUCT_INTEREST_MULTIPLIERS = {
    "product_viewed": 1.0,
    "product_clicked": 1.5,
    "cart_item_added": 3.0,
    "cart_item_quantity_updated": 2.0,
    "checkout_started": 3.5,
    "order_created": 4.0,
    "order_paid": 5.0,
    "order_completed": 5.0,
}

DEFAULT_PROFILE_FIELDS = (
    "top_categories",
    "top_brands",
    "top_price_bands",
    "recent_viewed_product_ids",
    "recent_clicked_product_ids",
    "recent_carted_product_ids",
    "recent_purchased_product_ids",
    "recent_queries",
    "recent_chat_cues",
    "strong_product_interests",
    "graph_interest_summary",
    "purchase_intent_score",
    "funnel_stage",
)


def _to_decimal(value):
    try:
        return Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError):
        return None


def _price_band(value):
    amount = _to_decimal(value)
    if amount is None:
        return None
    if amount < Decimal("50"):
        return "budget"
    if amount < Decimal("150"):
        return "mid"
    if amount < Decimal("500"):
        return "premium"
    return "luxury"


def _top_rows(counter, field_name, *, limit=3):
    return [
        {field_name: key, "score": round(float(score), 2)}
        for key, score in counter.most_common(limit)
    ]


def _append_unique(bucket, seen, value, *, limit=5):
    if value in seen or value in (None, ""):
        return
    bucket.append(value)
    seen.add(value)
    if len(bucket) > limit:
        bucket.pop()


def _build_funnel_summary(event_counts, cart_payload):
    cart_events = (
        event_counts["cart_item_added"]
        + event_counts["cart_item_quantity_updated"]
        + event_counts["cart_item_removed"] * 0.5
    )
    checkout_events = event_counts["checkout_started"] + event_counts["order_created"]
    purchase_events = event_counts["order_paid"] + event_counts["order_completed"]
    total_quantity = int(cart_payload.get("total_quantity", 0) or 0)
    item_count = int(cart_payload.get("item_count", 0) or 0)

    cart_intensity = min(((cart_events * 0.35) + (total_quantity * 0.2) + (item_count * 0.15)), 1.0)
    purchase_intensity = min((purchase_events * 0.5) + (checkout_events * 0.2), 1.0)
    purchase_intent_score = min(
        (
            event_counts["product_viewed"] * 0.04
            + event_counts["product_clicked"] * 0.07
            + cart_events * 0.18
            + checkout_events * 0.26
            + purchase_events * 0.35
            + (0.12 if item_count > 0 else 0.0)
            + (0.08 if event_counts["search_performed"] > 0 else 0.0)
        ),
        1.0,
    )

    if purchase_events > 0:
        funnel_stage = "buyer"
    elif checkout_events > 0 or purchase_intent_score >= 0.75:
        funnel_stage = "high-intent"
    elif cart_events > 0 or purchase_intent_score >= 0.4:
        funnel_stage = "interested"
    else:
        funnel_stage = "browser"

    return {
        "cart_intensity": round(float(cart_intensity), 2),
        "purchase_intensity": round(float(purchase_intensity), 2),
        "purchase_intent_score": round(float(purchase_intent_score), 2),
        "checkout_activity_count": int(checkout_events),
        "funnel_stage": funnel_stage,
        "current_cart": {
            "item_count": item_count,
            "total_quantity": total_quantity,
            "subtotal_amount": cart_payload.get("subtotal_amount"),
        },
    }


def build_profile_snapshot(
    products,
    events,
    interest_rows,
    *,
    user_id=None,
    session_id=None,
    cart_payload=None,
):
    cart_payload = cart_payload or {}
    event_counts = Counter()
    category_counter = Counter()
    brand_counter = Counter()
    price_band_counter = Counter()
    product_interest_counter = Counter()

    recent_fields = {
        "recent_viewed_product_ids": [],
        "recent_clicked_product_ids": [],
        "recent_carted_product_ids": [],
        "recent_purchased_product_ids": [],
    }
    recent_seen = {key: set() for key in recent_fields}
    recent_queries = []
    seen_queries = set()
    recent_chat_cues = []
    seen_chat_cues = set()

    for event in events:
        event_type = event.get("event_type")
        event_counts[event_type] += 1
        signal_weight = max(float(event.get("signal_weight", 1) or 1), 1.0)
        product_id = event.get("product_id")
        query_text = (event.get("query_text") or "").strip()

        if query_text:
            if event_type == "chat_message_sent":
                _append_unique(recent_chat_cues, seen_chat_cues, query_text)
            else:
                _append_unique(recent_queries, seen_queries, query_text)

        field_name = RECENT_EVENT_FIELDS.get(event_type)
        if field_name and product_id is not None:
            _append_unique(recent_fields[field_name], recent_seen[field_name], int(product_id))

        if product_id not in products:
            continue

        product = products[product_id]
        category_id = product.get("category_id")
        brand_id = product.get("brand_id")
        if category_id is not None:
            category_counter[int(category_id)] += signal_weight
        if brand_id is not None:
            brand_counter[int(brand_id)] += signal_weight

        band = _price_band(product.get("base_price"))
        if band:
            price_band_counter[band] += signal_weight

        multiplier = PRODUCT_INTEREST_MULTIPLIERS.get(event_type)
        if multiplier is not None:
            product_interest_counter[int(product_id)] += signal_weight * multiplier

    graph_interest_summary = [
        {
            "category_id": row.get("category_id"),
            "category_name": row.get("category_name"),
            "score": round(float(row.get("total_weight", 0)), 2),
        }
        for row in interest_rows[:3]
    ]

    strong_product_interests = []
    for product_id, score in product_interest_counter.most_common(5):
        product = products.get(product_id, {})
        strong_product_interests.append(
            {
                "product_id": int(product_id),
                "name": product.get("name"),
                "category_id": product.get("category_id"),
                "brand_id": product.get("brand_id"),
                "score": round(float(score), 2),
            }
        )

    funnel_summary = _build_funnel_summary(event_counts, cart_payload)
    recent_product_ids = []
    for field_name in (
        "recent_purchased_product_ids",
        "recent_carted_product_ids",
        "recent_clicked_product_ids",
        "recent_viewed_product_ids",
    ):
        for product_id in recent_fields[field_name]:
            if product_id not in recent_product_ids:
                recent_product_ids.append(product_id)

    preference_summary = {
        "top_categories": _top_rows(category_counter, "category_id"),
        "top_brands": _top_rows(brand_counter, "brand_id"),
        "top_price_bands": _top_rows(price_band_counter, "price_band"),
        "strong_product_interests": strong_product_interests,
        "graph_interest_summary": graph_interest_summary,
    }
    recent_activity = {
        "recent_viewed_product_ids": recent_fields["recent_viewed_product_ids"][:5],
        "recent_clicked_product_ids": recent_fields["recent_clicked_product_ids"][:5],
        "recent_carted_product_ids": recent_fields["recent_carted_product_ids"][:5],
        "recent_purchased_product_ids": recent_fields["recent_purchased_product_ids"][:5],
        "recent_queries": recent_queries[:5],
        "recent_chat_cues": recent_chat_cues[:5],
        "event_counts": {key: int(value) for key, value in sorted(event_counts.items())},
    }

    return {
        "user_id": user_id,
        "session_id": session_id,
        "scope_type": "user" if user_id is not None else ("session" if session_id else "anonymous"),
        "top_categories": preference_summary["top_categories"],
        "top_brands": preference_summary["top_brands"],
        "top_price_bands": preference_summary["top_price_bands"],
        "recent_viewed_product_ids": recent_activity["recent_viewed_product_ids"],
        "recent_clicked_product_ids": recent_activity["recent_clicked_product_ids"],
        "recent_carted_product_ids": recent_activity["recent_carted_product_ids"],
        "recent_purchased_product_ids": recent_activity["recent_purchased_product_ids"],
        "recent_product_ids": recent_product_ids[:6],
        "recent_queries": recent_activity["recent_queries"],
        "recent_chat_cues": recent_activity["recent_chat_cues"],
        "strong_product_interests": preference_summary["strong_product_interests"],
        "graph_interest_summary": preference_summary["graph_interest_summary"],
        "cart_intensity": funnel_summary["cart_intensity"],
        "purchase_intensity": funnel_summary["purchase_intensity"],
        "purchase_intent_score": funnel_summary["purchase_intent_score"],
        "checkout_activity_count": funnel_summary["checkout_activity_count"],
        "funnel_stage": funnel_summary["funnel_stage"],
        "recent_activity": recent_activity,
        "preference_summary": preference_summary,
        "funnel_summary": funnel_summary,
    }


class BehavioralProfileBuilder:
    def __init__(self, interaction_client, cart_client=None):
        self.interaction_client = interaction_client
        self.cart_client = cart_client

    def build(self, products, *, user_id=None, session_id=None, cart_payload=None):
        events = self.interaction_client.fetch_events(user_id=user_id, session_id=session_id, limit=25)
        interest_rows = self.interaction_client.fetch_user_interest(user_id=user_id, session_id=session_id, limit=5)
        effective_cart_payload = cart_payload
        if effective_cart_payload is None and session_id and self.cart_client is not None:
            try:
                effective_cart_payload = self.cart_client.fetch_current_cart(session_id)
            except Exception:
                effective_cart_payload = {}

        return build_profile_snapshot(
            products,
            events,
            interest_rows,
            user_id=user_id,
            session_id=session_id,
            cart_payload=effective_cart_payload or {},
        )

    def empty(self, *, user_id=None, session_id=None):
        return build_profile_snapshot({}, [], [], user_id=user_id, session_id=session_id, cart_payload={})

    def status(self):
        return {
            "behavioral_profile_enabled": True,
            "profile_version": "behavioral-profile-v1",
            "scoring_mode": "behavioral-heuristic",
            "supported_scopes": ["user_id", "session_id"],
            "profile_fields": list(DEFAULT_PROFILE_FIELDS),
            "integrations": {
                "recommendation": {
                    "profile_bias": True,
                    "graph_signals": True,
                    "purchase_intent_score": True,
                },
                "chat": {
                    "retrieval_bias": True,
                    "prompt_context": True,
                    "grounded_realtime_guardrails": True,
                },
            },
            "fallbacks": {
                "missing_behavior_data": "empty-profile",
                "missing_cart_scope": "profile-without-cart-summary",
            },
        }
