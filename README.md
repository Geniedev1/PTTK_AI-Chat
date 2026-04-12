# Microservice E-Commerce Platform

Hệ thống đã được refactor theo DDD để dùng một `product-service` duy nhất cho bounded context `Catalog`.

## Kiến trúc hiện tại

- `staff-service` trên cổng `8001`
- `customer-service` trên cổng `8002`
- `cart-service` trên cổng `8003`
- `product-service` trên cổng `8004`
- `api-gateway` trên cổng `80`

Gateway route:

- `/api/staff/`
- `/api/customers/`
- `/api/cart/`
- `/api/products/`

## Vì sao đổi sang `product-service`

Theo tài liệu thiết kế DDD:

- không tách microservice theo category sản phẩm
- `Laptop`, `Clothes` chỉ là dữ liệu/category/product type
- `Catalog` là một domain duy nhất
- `Cart` chỉ lưu `product_id` và gọi sang `product-service`

## Product Service theo DDD

Cấu trúc chính ở [product-service](/Users/dongocminh/PTTK/KiemTra01/product-service):

- `config/settings/`
- `modules/catalog/domain/`
- `modules/catalog/application/`
- `modules/catalog/infrastructure/`
- `modules/catalog/presentation/api/`
- `shared/`

`Product` dùng model chung với:

- `name`
- `description`
- `category_id`
- `brand_id`
- `product_type_id`
- `base_price`
- `stock`
- `attributes` dạng JSON
- `variants`

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

## API chính

### Product

```text
POST   /api/products/
GET    /api/products/
GET    /api/products/{id}/
PUT    /api/products/{id}/
DELETE /api/products/{id}/
GET    /api/products/in_stock/
POST   /api/products/{id}/variants/
GET    /api/products/categories/
GET    /api/products/categories/{id}/
```

Ví dụ tạo product:

```bash
curl -X POST http://localhost/api/products/ \
  -H "Content-Type: application/json" \
  -d '{
    "name": "MacBook Pro 14",
    "description": "Powerful laptop for professionals",
    "base_price": 2000.00,
    "stock": 10,
    "attributes": {
      "ram": "16GB",
      "cpu": "M3 Pro",
      "storage": "512GB SSD"
    }
  }'
```

### Cart

```text
GET    /api/cart/
GET    /api/cart/by_customer?customer_id=1
POST   /api/cart/add_product?customer_id=1
POST   /api/cart/remove_product?customer_id=1
POST   /api/cart/update_quantity?customer_id=1
POST   /api/cart/clear_cart?customer_id=1
```

Ví dụ thêm vào giỏ:

```bash
curl -X POST "http://localhost/api/cart/add_product?customer_id=1" \
  -H "Content-Type: application/json" \
  -d '{
    "product_id": 1,
    "quantity": 2
  }'
```

## Tài liệu liên quan

- [DDD_REDESIGN.md](/Users/dongocminh/PTTK/KiemTra01/DDD_REDESIGN.md)
- [QUICK_START.md](/Users/dongocminh/PTTK/KiemTra01/QUICK_START.md)
- [API_DOCUMENTATION.md](/Users/dongocminh/PTTK/KiemTra01/API_DOCUMENTATION.md)
- [ARCHITECTURE.md](/Users/dongocminh/PTTK/KiemTra01/ARCHITECTURE.md)
