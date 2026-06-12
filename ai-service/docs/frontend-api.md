# AI Service Frontend API Docs

This document describes the APIs used by frontend for recommendation and chat flows.

## 1. Base URL

Use one of these base URLs:

- Through gateway (recommended for frontend): `http://<gateway-host>/api/ai`
- Direct AI service (dev/debug): `http://<ai-service-host>:8007/api/ai`

All routes below are relative to `/api/ai`.

## 2. Request/Response Conventions

- Content type:
  - `GET`: query params
  - `POST`: `application/json`
- Optional request id:
  - Request header: `X-Request-ID: <string>`
  - Response always includes `X-Request-ID`
- No trailing slash required.

## 3. Recommendation APIs

## 3.1 GET `/recommend/home`

Get home feed recommendations.

Query params:

- `user_id` (optional, integer)
- `session_id` (optional, string, max 64)
- `limit` (optional, integer, min 1)

Notes:

- If `limit` is omitted, backend uses default.
- Backend clamps limit to max allowed.

Success `200` response shape:

```json
{
  "context": {
    "strategy": "home",
    "user_id": 77,
    "session_id": "sess-1",
    "recent_product_ids": [1, 2],
    "profile_snapshot": {
      "scope_type": "user",
      "purchase_intent_score": 0.56,
      "funnel_stage": "interested"
    },
    "deep_model": {
      "enabled": true,
      "loaded": true,
      "applied": true,
      "alpha": 0.35,
      "model_version": "plan11b-mlp-v1",
      "fallback_mode": "deep-model",
      "error": null
    }
  },
  "items": [
    {
      "product": {
        "id": 2,
        "name": "Silent Keyboard Pro",
        "slug": "silent-keyboard-pro",
        "short_description": "Low-noise switches",
        "category_id": 10,
        "brand_id": 201,
        "base_price": "109.00",
        "stock": 7,
        "has_stock": true,
        "tags": ["keyboard"]
      },
      "score": 12.45,
      "deep_model_score": 0.95,
      "reason_codes": ["deep_model", "graph_neighbor", "popular"],
      "source_signals": {
        "deep_model_bonus": 0.33,
        "deep_model_score": 0.95,
        "popularity": 8.8
      }
    }
  ]
}
```

## 3.2 GET `/recommend/product-detail`

Get related recommendations for a product detail page.

Query params:

- `product_id` (required, integer >= 1)
- `user_id` (optional, integer)
- `session_id` (optional, string)
- `limit` (optional, integer)

Success `200` response:

- Same `items` shape as `/recommend/home`
- `context.strategy = "product-detail"`
- `context.product_id` included

Validation error `400` examples:

```json
{"product_id": ["This field is required."]}
```

## 3.3 GET `/recommend/cart`

Get cart-based recommendations.

Query params:

- `session_id` (required, string, max 64)
- `user_id` (optional, integer)
- `limit` (optional, integer)

Success `200` response:

- Same `items` shape as `/recommend/home`
- `context.strategy = "cart"` or `"cart-fallback-home"`
- `context.cart_product_ids` included

Validation error `400` example:

```json
{"session_id": ["This field is required."]}
```

## 4. Profile APIs

## 4.1 GET `/recommend/profile/snapshot`

Get behavioral profile snapshot.

Query params:

- `user_id` (optional, integer)
- `session_id` (optional, string)
- At least one of `user_id` or `session_id` must be provided.

Success `200` response shape:

```json
{
  "user_id": 77,
  "session_id": null,
  "profile_snapshot": {
    "scope_type": "user",
    "top_categories": [{"category_id": 10, "score": 12.0}],
    "top_brands": [{"brand_id": 200, "score": 10.0}],
    "top_price_bands": [{"price_band": "mid", "score": 9.5}],
    "recent_viewed_product_ids": [1, 4],
    "recent_clicked_product_ids": [1],
    "recent_carted_product_ids": [1],
    "recent_purchased_product_ids": [],
    "recent_product_ids": [1, 4],
    "recent_queries": ["quiet keyboard"],
    "recent_chat_cues": ["need silent keyboard"],
    "strong_product_interests": [{"product_id": 1, "score": 19.0}],
    "graph_interest_summary": [{"category_id": 10, "score": 8.0}],
    "purchase_intent_score": 0.33,
    "funnel_stage": "interested"
  }
}
```

Error `400` when missing scope:

```json
{"detail": "Provide user_id or session_id."}
```

## 4.2 GET `/profile/snapshot`

Alias endpoint for profile snapshot.

- Same query params, constraints, and response as `/recommend/profile/snapshot`.

## 5. Model Status API

## 5.1 GET `/models/status`

Runtime model and integration status.

Success `200` response includes:

- `behavioral_profile_enabled`
- `profile_version`
- `scoring_mode` (`behavioral-heuristic` or `hybrid-deep-heuristic`)
- `deep_model` object:
  - `enabled`, `loaded`, `model_version`, `artifact_dir`, `alpha`, `score_clip`, `fallback_mode`, `error`
- `runtime` object:
  - `recommendation_limit_default`, `recommendation_limit_max`, `request_timeout_seconds`, `deep_model_alpha`

## 6. Chat APIs

## 6.1 POST `/chat`

Main chat endpoint (supports realtime routing and grounded retrieval fallback).

Request body:

```json
{
  "message": "What is my order status?",
  "user_id": 77,
  "session_id": "sess-1",
  "customer_id": 7,
  "product_id": 2,
  "order_id": 99
}
```

Fields:

- `message` (required, string, max 4000)
- `user_id` (optional, integer)
- `session_id` (optional, string, max 64)
- `customer_id` (optional, integer)
- `product_id` (optional, integer)
- `order_id` (optional, integer)

Success `200` response (common shape):

```json
{
  "answer": "Order #99 is currently `PAID`. Total amount is 149.99 with 1 item(s).",
  "sources": [
    {
      "source_type": "realtime_order",
      "source_id": "99",
      "title": "Order #99",
      "excerpt": "{\"status\": \"PAID\", \"total_amount\": \"149.99\"}"
    }
  ],
  "used_realtime_api": true,
  "used_graph_context": false,
  "retrieval_mode": "realtime-order"
}
```

For non-realtime route, response may also include:

- `profile_snapshot`

Example retrieval mode values:

- `realtime-order`
- `realtime-cart`
- `realtime-product`
- `lexical`
- `embedding`

## 6.2 POST `/chat/retrieve`

Retrieve grounded chat context without generating final answer.

Request body:

```json
{
  "message": "return policy keyboard",
  "user_id": 77,
  "session_id": "sess-1",
  "product_id": 2,
  "limit": 5
}
```

Fields:

- Same as `/chat`
- `limit` (optional, integer, min 1)

Success `200` response:

```json
{
  "query": "return policy keyboard",
  "sources": [
    {
      "source_type": "policy",
      "source_id": "returns-1",
      "title": "Returns",
      "excerpt": "Return requests are accepted within ...",
      "product_id": null,
      "score": 2.1
    }
  ],
  "graph_context": [
    {
      "type": "user_interest",
      "label": "Keyboards",
      "score": 6
    }
  ],
  "used_graph_context": true,
  "retrieval_mode": "lexical",
  "profile_snapshot": {
    "scope_type": "user",
    "purchase_intent_score": 0.42,
    "funnel_stage": "interested"
  }
}
```

## 7. Error Handling

Typical non-200 responses:

- `400`: serializer validation errors
- `502` (or downstream status mapped): dependency/service client issues

Error body shape:

```json
{
  "detail": "<error message>"
}
```

or serializer errors:

```json
{
  "message": ["This field is required."]
}
```

## 8. Frontend Integration Notes

- Always pass `X-Request-ID` from frontend for log traceability.
- Treat `deep_model_score` as optional (`null` possible on fallback).
- Prefer `reason_codes` and `source_signals` for UI explainability chips/tooltips.
- For anonymous users, use stable `session_id` across requests.
- Chat UX should branch by `used_realtime_api` and `retrieval_mode` to show proper source badges.
