# DDD Redesign Summary

Project đã được thiết kế lại theo nội dung trong PDF `Thiết kế Product Service theo DDD`.

## Điểm thay đổi chính

- Bỏ mô hình tách service theo từng loại sản phẩm.
- Thêm `product-service` duy nhất cho bounded context `Catalog`.
- `category`, `product_type`, `brand` trở thành dữ liệu của domain `Catalog`, không còn là ranh giới microservice.
- `cart-service` chỉ lưu `product_id` và gọi sang `product-service` để xác thực sản phẩm.
- `api-gateway` route sản phẩm qua `/api/products/`.

## Cấu trúc mới

`product-service/` được tổ chức theo DDD:

- `config/settings/`: tách `base.py`, `dev.py`, `prod.py`
- `modules/catalog/domain/`: entity, value object, repository interface
- `modules/catalog/application/`: command, query, application service
- `modules/catalog/infrastructure/`: Django ORM models, queryset, repository implementation, migrations
- `modules/catalog/presentation/api/`: serializers, views, urls
- `modules/catalog/tests/`: test cơ bản
- `shared/`: shared utility và exception

## Product API

- `GET /api/products/`
- `POST /api/products/`
- `GET /api/products/{id}/`
- `PUT /api/products/{id}/`
- `DELETE /api/products/{id}/`
- `GET /api/products/in_stock/`
- `POST /api/products/{id}/variants/`
- `GET /api/products/categories/`
- `GET /api/products/categories/{id}/`

## Product data model

`Product` dùng dữ liệu chung cho nhiều loại sản phẩm:

- `name`
- `description`
- `category_id`
- `brand_id`
- `product_type_id`
- `base_price`
- `stock`
- `attributes` (`JSONField`)
- `is_active`

Ví dụ `attributes`:

```json
{
  "ram": "16GB",
  "cpu": "i7"
}
```

## Kiểm tra đã chạy

Mình đã chạy thành công:

- `product-service`: `python3 manage.py check`
- `cart-service`: `python3 manage.py check`
- `api-gateway`: `python3 manage.py check`

Các lệnh check được chạy với `DB_ENGINE=django.db.backends.sqlite3` để tránh phụ thuộc PostgreSQL local; khi chạy Docker, service vẫn dùng PostgreSQL như cấu hình trong `docker-compose.yml`.
