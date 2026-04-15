# Backend API Docs (All Services)

This document summarizes all backend APIs in this project for frontend integration.

## 1. Base URL and Gateway

Recommended frontend base URL:

- `http://localhost` (api-gateway on port 80)

Gateway routes:

- `GET /` -> gateway root health text
- `GET /health` -> gateway health text
- `GET/POST/... /api/*` -> proxied to corresponding backend service

Gateway service mapping:

- `/api/staff/` -> staff-service
- `/api/customers/` -> customer-service
- `/api/cart/` -> cart-service
- `/api/products/` -> product-service
- `/api/orders/` -> order-service
- `/api/interactions/` -> interaction-service
- `/api/ai/` -> ai-service

## 2. Common Headers and Auth

### 2.1 Optional tracing header

- `X-Request-ID: <string>`
- AI service returns `X-Request-ID` in response.

### 2.2 Token auth (staff/customer profile endpoints)

- `Authorization: Token <token>`

### 2.3 Internal admin key (restricted endpoints)

- `X-Internal-Admin-Key: <internal_admin_key>`

### 2.4 Cart session header

- `X-Cart-Session-Key: <session_key>`
- Used by cart and order flows.

## 3. Staff Service

Base path: `/api/staff/`

Notes:

- Default CRUD routes exist but intentionally return 405 with guidance.
- Active endpoints are `register`, `login`, `me`.

### 3.1 POST `/api/staff/register/`

Auth:

- Requires `X-Internal-Admin-Key` (or authenticated staff/superuser).

Body:

- `username` string, required
- `password` string, required
- `name` string, required
- `email` string, required
- `phone` string, optional
- `position` string, optional

Response:

- `201` with staff object

### 3.2 POST `/api/staff/login/`

Body:

- `username` string, required
- `password` string, required

Response:

- `200`:
  - `token`
  - `staff`
- `401` invalid credentials

### 3.3 GET `/api/staff/me/`

Auth:

- `Authorization: Token <token>`

Response:

- `200` with current staff profile
- `404` if staff record not found

## 4. Customer Service

Base path: `/api/customers/`

Notes:

- Default CRUD routes exist but intentionally return 405 with guidance.
- Active endpoints are `register`, `login`, `profile`, `update_profile`.

### 4.1 POST `/api/customers/register/`

Body:

- `username` string, required
- `password` string, required
- `email` string, required
- `phone` string, optional
- `address` string, optional
- `city` string, optional
- `country` string, optional

Response:

- `201` with message

### 4.2 POST `/api/customers/login/`

Body:

- `username` string, required
- `password` string, required

Response:

- `200`:
  - `token`
  - `customer`
- `401` invalid credentials

### 4.3 GET `/api/customers/profile/`

Auth:

- `Authorization: Token <token>`

Response:

- `200` customer profile
- `404` if not found

### 4.4 PUT `/api/customers/update_profile/`

Auth:

- `Authorization: Token <token>`

Body:

- Partial customer profile fields:
  - `phone`, `address`, `city`, `country`

Response:

- `200` updated customer profile
- `404` if not found

## 5. Cart Service

Base path: `/api/cart`

Notes:

- Router uses no trailing slash style (`/api/cart/current`, not `/api/cart/current/`).
- Every response from cart actions returns `X-Cart-Session-Key`.

### 5.1 GET `/api/cart/current`

Headers:

- Optional `X-Cart-Session-Key`
- If missing, backend creates a new one.

Response:

- `200`:
  - `session_key`
  - `items`[]
  - `item_count`
  - `total_quantity`
  - `subtotal_amount`

### 5.2 POST `/api/cart/add_product`

Headers:

- Optional `X-Cart-Session-Key`

Body:

- `product_id` int, required
- `quantity` int >= 1, optional default 1

Response:

- `201` created cart item or `200` incremented existing
- `404` product not found
- `400` product unavailable

### 5.3 POST `/api/cart/remove_product`

Headers:

- Optional `X-Cart-Session-Key`

Body:

- `product_id` int, required

Response:

- `200` removed
- `404` cart item not found

### 5.4 POST `/api/cart/update_quantity`

Headers:

- Optional `X-Cart-Session-Key`

Body:

- `product_id` int, required
- `quantity` int >= 1, required

Response:

- `200` updated
- `404` item not found

### 5.5 POST `/api/cart/clear_cart`

Headers:

- Optional `X-Cart-Session-Key`

Response:

- `200` cart cleared

## 6. Product Service

Base path: `/api/products/`

Notes:

- This service uses trailing slash style.
- Read endpoints are public.
- Write endpoints require catalog admin access (`X-Internal-Admin-Key` or staff/superuser session).

## 6.1 Categories

### GET `/api/products/categories/`

- List categories.

### GET `/api/products/categories/{id}/`

- Category detail.

## 6.2 Products

### GET `/api/products/`

Query params:

- Filters:
  - `category_id` int
  - `product_type_id` int
  - `brand_id` int
  - `in_stock` bool string (`true`)
  - `search` string
  - `min_price` decimal
  - `max_price` decimal
  - `sort_by` string
  - `tag` string
- Admin-only visibility option:
  - `include_inactive=true` (only if admin access)

Response:

- Product list with fields:
  - `id, name, slug, short_description, description, full_description`
  - `category_id, brand_id, product_type_id`
  - `base_price, stock, attributes, is_active, status, tags, image_urls, has_stock`
  - `variants[]`

### GET `/api/products/{id}/`

- Product detail.
- Returns 404 for inactive products unless admin access.

### GET `/api/products/search/`

- Same filter params as list, explicitly search route.

### GET `/api/products/in_stock/`

- In-stock product list.

### POST `/api/products/`

Auth:

- Catalog admin access required.

Body:

- `name` string, required
- `base_price` decimal, required
- Optional:
  - `slug`, `short_description`, `description` or `full_description`
  - `category_id`, `brand_id`, `product_type_id`
  - `stock`, `attributes`, `tags`, `image_urls`, `is_active`

### PUT `/api/products/{id}/`

Auth:

- Catalog admin access required.

Body:

- Same as create payload.

### DELETE `/api/products/{id}/`

Auth:

- Catalog admin access required.

### POST `/api/products/{id}/variants/`

Auth:

- Catalog admin access required.

Body:

- `sku` string, required
- `name` string, required
- `stock` int >= 0, required
- Optional:
  - `attributes` object
  - `price_override` decimal
  - `is_default` bool

## 7. Order Service

Base path: `/api/orders`

Notes:

- Router uses no trailing slash style.
- Scope is required for read operations: `customer_id` query param and/or `X-Cart-Session-Key` header.

### 7.1 GET `/api/orders`

Scope requirements:

- Provide `customer_id` query param or `X-Cart-Session-Key` header.

Response:

- List of orders with nested items.

### 7.2 GET `/api/orders/{id}`

Scope requirements:

- Same as list.

Response:

- Order detail in scope.

### 7.3 POST `/api/orders`

Headers:

- `X-Cart-Session-Key` required.

Body:

- `customer_id` int, optional
- `clear_cart` bool, optional default true

Behavior:

- Reads current cart from cart-service.
- Snapshots product info from product-service.
- Creates order and items.
- Optionally clears cart.

Response:

- `201`:
  - `order`
  - `cart_cleared` bool

### 7.4 POST `/api/orders/{id}/update_status`

Auth:

- Requires `X-Internal-Admin-Key`.

Body:

- `status` one of:
  - `PENDING`
  - `CONFIRMED`
  - `PAID`
  - `CANCELLED`
  - `COMPLETED`

Response:

- `200` updated order
- `400` invalid transition
- `403` missing admin access

## 8. Interaction Service

Base path: `/api/interactions`

Notes:

- Router uses no trailing slash style.

## 8.1 Events API

### GET `/api/interactions/events`

Query params:

- `event_type`, `user_id`, `session_id`, `product_id`, `query_text`, `source`
- `date_from` (YYYY-MM-DD)
- `date_to` (YYYY-MM-DD)
- `limit` (max 200)

Response:

- Event list.

### POST `/api/interactions/events`

Body:

- `event_type` required
- `user_id` optional
- `session_id` optional
- `product_id` optional
- `query_text` optional
- `source` optional
- `timestamp` optional
- `metadata` optional object

Validation:

- Must provide at least one of `user_id` or `session_id`.
- `event_type` must be supported.

Response:

- `201` created event

### GET `/api/interactions/events/data_quality`

- Data quality aggregates.

### GET `/api/interactions/events/top_queries`

- Top search queries.

### GET `/api/interactions/events/product_gaps`

- Product interaction funnel stats.

### GET `/api/interactions/events/abandoned_carts`

- Sessions with cart add but no paid/completed order event.

### GET `/api/interactions/events/category_interest`

- Daily grouped category interest.

### GET `/api/interactions/events/signal_weights`

- Configured weight plus recorded count by event type.

## 8.2 Graph API

### GET `/api/interactions/graph/status`

- Graph runtime status.

### POST `/api/interactions/graph/rebuild`

Auth:

- Requires `X-Internal-Admin-Key`.

- Rebuilds graph from product catalog + interaction events.

### GET `/api/interactions/graph/user_interest`

Query:

- `user_id` or `session_id` required
- `limit` optional

### GET `/api/interactions/graph/product_neighbors`

Query:

- `product_id` required
- `limit` optional

### GET `/api/interactions/graph/query_paths`

Query:

- `product_id` or `query_text` required
- `limit` optional

### GET `/api/interactions/graph/similar_users`

Query:

- `user_id` or `session_id` required
- `limit` optional

## 9. AI Service

Base path: `/api/ai`

Key endpoint groups:

- Recommendation:
  - `GET /api/ai/recommend/home`
  - `GET /api/ai/recommend/product-detail`
  - `GET /api/ai/recommend/cart`
  - `GET /api/ai/recommend/profile/snapshot`
- Profile:
  - `GET /api/ai/profile/snapshot`
- Model status:
  - `GET /api/ai/models/status`
- Chat:
  - `POST /api/ai/chat`
  - `POST /api/ai/chat/retrieve`

Full AI request/response details are documented in:

- `ai-service/docs/frontend-api.md`

## 10. Frontend Integration Checklist

- Route all frontend requests through gateway: `http://localhost`.
- Persist `X-Cart-Session-Key` from cart responses and reuse it.
- Persist customer/staff token after login and send `Authorization: Token ...`.
- Send `X-Internal-Admin-Key` only from privileged admin tools (not public UI).
- Respect trailing-slash differences:
  - Product, staff, customer often use slash style.
  - Cart, order, interaction, ai use no-slash style.
- Handle common error forms:
  - `{"detail": "..."}`
  - serializer validation object (field -> messages)
