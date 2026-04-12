# Architecture

## Overview

Hệ thống hiện được chia theo bounded context:

- `Catalog` → `product-service`
- `Cart` → `cart-service`
- `Customer` → `customer-service`
- `Staff` → `staff-service`
- `Gateway` → `api-gateway`

Điểm quan trọng:

- không còn tách microservice theo loại sản phẩm
- `Laptop` và `Clothes` chỉ còn là category hoặc `attributes`
- `Cart` chỉ giữ `product_id`
- `Gateway` chỉ route sản phẩm qua `/api/products/`

## Runtime Topology

```text
Client
  -> API Gateway :80
     -> Staff Service :8001
     -> Customer Service :8002
     -> Cart Service :8003
     -> Product Service :8004
```

## Databases

- `staff-db` → MySQL
- `customer-db` → MySQL
- `cart-db` → PostgreSQL
- `product-db` → PostgreSQL

## Product Service theo DDD

```text
product-service/
  config/
    settings/
      base.py
      dev.py
      prod.py
  modules/
    catalog/
      domain/
      application/
      infrastructure/
      presentation/
  shared/
```

### Layer responsibility

- `domain`: entity, value object, repository contract
- `application`: command, query, use case orchestration
- `infrastructure`: Django ORM, queryset, migration, repository implementation
- `presentation`: API serializer, view, route

## Product Model

`Product` có các trường chính:

- `name`
- `description`
- `category_id`
- `brand_id`
- `product_type_id`
- `base_price`
- `stock`
- `attributes`
- `is_active`

Ví dụ `attributes`:

```json
{
  "ram": "16GB",
  "cpu": "i7",
  "storage": "512GB SSD"
}
```

## Cart Flow

1. Client gọi `POST /api/cart/add_product?customer_id=...`
2. `cart-service` gọi `GET /api/products/{id}/`
3. Nếu product tồn tại, cart lưu `customer_id`, `product_id`, `quantity`
4. Cart không còn biết gì về `laptop` hay `clothes`
