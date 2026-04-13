# Microservice E-Commerce Platform

Repo này đang triển khai roadmap theo thứ tự `01 -> 02 -> 03 -> 04 -> 05 -> 06 -> 07 -> 08` trong thư mục [`plan`](./plan).

## Services hiện tại

- `staff-service` trên cổng `8001`
- `customer-service` trên cổng `8002`
- `cart-service` trên cổng `8003`
- `product-service` trên cổng `8004`
- `order-service` trên cổng `8005`
- `api-gateway` trên cổng `80`

Gateway route:

- `/api/staff/`
- `/api/customers/`
- `/api/cart/`
- `/api/products/`
- `/api/orders/`

## Trạng thái roadmap

- Plan 01: kiến trúc MVP và ownership
- Plan 02: hardening core service và session cart
- Plan 03: catalog metadata + search/filter/sort
- Plan 04: baseline cart-to-order flow với `order-service`

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
