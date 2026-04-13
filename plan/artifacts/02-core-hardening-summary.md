# Core Hardening Summary

## Mục tiêu đã xử lý

- khóa public CRUD ở `customer-service` và `staff-service`
- khóa ghi `product-service` bằng admin gate
- chuẩn hóa validation giá và stock logic
- bỏ ownership cart theo `customer_id` query param
- chuyển cart sang session-based ownership
- thêm test khung tối thiểu cho các behavior đã sửa

## Quyết định kỹ thuật chính

## 1. Product write dùng internal admin key

Repo hiện tại chưa có shared auth giữa `staff-service` và `product-service`, nên chưa thể xác thực staff token liên-service một cách sạch ngay trong Plan 02.

Giải pháp tạm thời nhưng an toàn hơn:

- read product vẫn public
- write product yêu cầu `X-Internal-Admin-Key`
- hoặc user local có quyền admin/staff nếu có

Mục đích:

- chặn anonymous write ngay bây giờ
- không làm giả kiến trúc staff auth liên-service khi nó chưa tồn tại

## 2. Cart chuyển sang session-based ownership

Repo hiện tại không có customer identity dùng chung giữa `customer-service` và `cart-service`.

Giải pháp đã áp dụng:

- cart không còn dựa vào `customer_id` từ query param
- cart dùng `X-Cart-Session-Key`
- nếu request chưa có key thì service tự tạo key mới
- các thao tác add/update/remove/clear/current đều hoạt động trong cùng session scope

Mục đích:

- tránh việc sửa cart của người khác bằng cách đoán `customer_id`
- vẫn giữ được anonymous cart cho MVP

## 3. Customer và Staff không còn lộ CRUD public

### Customer giữ lại

- `register`
- `login`
- `profile`
- `update_profile`

### Staff giữ lại

- `login`
- `me`
- `register` nội bộ có bảo vệ bằng admin key

Các route CRUD gốc giờ trả `405`.

## 4. Product visibility và stock thống nhất hơn

- `ProductWriteSerializer` chặn giá âm
- public retrieve không trả product inactive
- `include_inactive=true` chỉ dùng được nếu có admin access
- `in_stock` đã tính cả stock ở variant
- response product có thêm `has_stock`

## File code đã thay đổi

### Product service

- `product-service/modules/catalog/presentation/api/permissions.py`
- `product-service/modules/catalog/presentation/api/views/product_view.py`
- `product-service/modules/catalog/presentation/api/serializers/product_serializer.py`
- `product-service/modules/catalog/infrastructure/querysets/product_queryset.py`
- `product-service/config/settings/base.py`

### Cart service

- `cart-service/cart/views.py`
- `cart-service/cart/models.py`
- `cart-service/cart/serializers.py`
- `cart-service/cart/migrations/0003_harden_cart_ownership.py`

### Customer service

- `customer-service/customer/views.py`

### Staff service

- `staff-service/staff/views.py`
- `staff-service/staff/permissions.py`
- `staff-service/staff_service/settings.py`

### Shared runtime config

- `.env.example`
- `docker-compose.yml`

## Test skeleton đã thêm

- `product-service/modules/catalog/tests/test_product_hardening.py`
- `cart-service/cart/tests.py`
- `customer-service/customer/tests.py`
- `staff-service/staff/tests.py`

## Hạn chế còn lại

- chưa có central auth/shared token giữa services
- cart vẫn là anonymous session cart, chưa map sang customer identity thật
- chưa chạy được Django test suite trong workspace hiện tại vì thiếu dependency runtime

## Điều kiện để sang Plan 03

- chấp nhận tạm thời dùng `internal admin key` cho protected write
- chấp nhận `session cart` là giải pháp ownership của MVP
- nếu muốn chuyển sang auth liên-service thật thì nên đưa vào một plan riêng sau core hardening
