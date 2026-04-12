# Project Summary

## Trạng thái hiện tại

Repo đã được refactor từ mô hình tách service theo từng loại sản phẩm sang mô hình:

- `product-service`

## Mục tiêu đạt được

- gom toàn bộ product catalog vào một bounded context `Catalog`
- đưa cấu trúc `product-service` về DDD
- sửa `cart-service` để chỉ làm việc với `product_id`
- sửa `api-gateway` để route qua `/api/products/`
- sửa `docker-compose.yml` và `Makefile` theo kiến trúc mới
- xóa hẳn các service sản phẩm cũ để chỉ giữ `product-service`

## Thành phần chính

- `product-service/`
- `cart-service/`
- `customer-service/`
- `staff-service/`
- `api-gateway/`

## Kiểm tra đã chạy

Đã chạy thành công:

- `product-service`: `manage.py check`
- `cart-service`: `manage.py check`
- `api-gateway`: `manage.py check`

## Lưu ý migration

`cart-service` có migration mới để bỏ `product_type`.

Khi chạy trên môi trường Docker:

```bash
docker-compose up -d
```

thì `entrypoint.sh` của từng service sẽ tự gọi migrate.
