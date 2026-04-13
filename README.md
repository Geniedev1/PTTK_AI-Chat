# Microservice E-Commerce Platform

Repo này đang triển khai roadmap theo thứ tự `01 -> 02 -> 03 -> 04 -> 05 -> 06 -> 07 -> 08` trong thư mục [`plan`](./plan).

## Services hiện tại

- `staff-service` trên cổng `8001`
- `customer-service` trên cổng `8002`
- `cart-service` trên cổng `8003`
- `product-service` trên cổng `8004`
- `order-service` trên cổng `8005`
- `interaction-service` trên cổng `8006`
- `api-gateway` trên cổng `80`

Gateway route:

- `/api/staff/`
- `/api/customers/`
- `/api/cart/`
- `/api/products/`
- `/api/orders/`
- `/api/interactions/`

## Trạng thái roadmap

- Plan 01: kiến trúc MVP và ownership
- Plan 02: hardening core service và session cart
- Plan 03: catalog metadata + search/filter/sort
- Plan 04: baseline cart-to-order flow với `order-service`
- Plan 05: interaction tracking foundation với `interaction-service`

Các phase `05-08` vẫn là bước tiếp theo cho interaction tracking, AI recommendation, RAG chatbot và personalization.

## Chạy hệ thống

```bash
docker-compose build
docker-compose up -d
docker-compose ps
```

Kiểm tra gateway:

```bash
curl http://localhost/health
```

## Contract chính

### Cart

Cart hiện dùng `X-Cart-Session-Key` thay cho `customer_id` query param.

```text
GET  /api/cart/current
POST /api/cart/add_product
POST /api/cart/remove_product
POST /api/cart/update_quantity
POST /api/cart/clear_cart
```

Ví dụ thêm sản phẩm:

```bash
curl -X POST http://localhost/api/cart/add_product \
  -H "Content-Type: application/json" \
  -H "X-Cart-Session-Key: demo-session-001" \
  -d '{
    "product_id": 1,
    "quantity": 2
  }'
```

### Product

```text
POST   /api/products/
GET    /api/products/
GET    /api/products/search
GET    /api/products/{id}
PUT    /api/products/{id}
DELETE /api/products/{id}
GET    /api/products/in_stock
POST   /api/products/{id}/variants
```

`GET /api/products/` và `GET /api/products/search` hỗ trợ `search`, `category_id`, `brand_id`, `product_type_id`, `in_stock`, `min_price`, `max_price`, `sort_by`, `tag`.

### Order

Order hiện được tạo trực tiếp từ cart session.

```text
POST /api/orders/
GET  /api/orders/?customer_id={id}
GET  /api/orders/{id}?customer_id={id}
POST /api/orders/{id}/update_status
```

Ví dụ tạo order từ cart:

```bash
curl -X POST http://localhost/api/orders/ \
  -H "Content-Type: application/json" \
  -H "X-Cart-Session-Key: demo-session-001" \
  -d '{
    "customer_id": 1,
    "clear_cart": true
  }'
```

Ví dụ update trạng thái order:

```bash
curl -X POST http://localhost/api/orders/1/update_status \
  -H "Content-Type: application/json" \
  -H "X-Internal-Admin-Key: change-this-in-dev" \
  -d '{
    "status": "PAID"
  }'
```

### Interaction

Interaction service vừa nhận event từ frontend/backend, vừa cung cấp report kiểm tra chất lượng dữ liệu.

```text
POST /api/interactions/events
GET  /api/interactions/events
GET  /api/interactions/events/data_quality
GET  /api/interactions/events/top_queries
GET  /api/interactions/events/product_gaps
GET  /api/interactions/events/abandoned_carts
GET  /api/interactions/events/category_interest
GET  /api/interactions/events/signal_weights
```

Ví dụ gửi event:

```bash
curl -X POST http://localhost/api/interactions/events \
  -H "Content-Type: application/json" \
  -d '{
    "event_type": "product_clicked",
    "session_id": "sess-demo-001",
    "product_id": 10,
    "query_text": "gaming headset",
    "source": "web",
    "metadata": {
      "position": 3,
      "page": 1,
      "from_page": "search_result"
    }
  }'
```

## Plan 06 Addendum

Plan 06 adds a Neo4j-backed knowledge graph baseline through `interaction-service`.

Runtime pieces:

- `knowledge-graph-db` exposes Neo4j on `7474` and `7687`
- `interaction-service` can sync interaction events on write into the graph
- `python manage.py rebuild_graph` rebuilds the graph from `product-service` catalog data and stored interaction events

Graph API:

```text
GET  /api/interactions/graph/status
POST /api/interactions/graph/rebuild
GET  /api/interactions/graph/user_interest?user_id={id}|session_id={id}
GET  /api/interactions/graph/product_neighbors?product_id={id}
GET  /api/interactions/graph/query_paths?product_id={id}|query_text={text}
GET  /api/interactions/graph/similar_users?user_id={id}|session_id={id}
```
