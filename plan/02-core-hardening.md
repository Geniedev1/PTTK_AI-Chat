# Plan 02: Core Hardening

## Trạng thái

Completed for review.

## Deliverable files

- [artifacts/02-core-hardening-summary.md](./artifacts/02-core-hardening-summary.md)

## Mục tiêu

Làm sạch các service hiện có để dữ liệu nghiệp vụ đáng tin cậy trước khi xây tracking và AI.

## Lý do phải làm trước

Repo hiện tại còn các rủi ro lớn:

- nhiều endpoint ghi dữ liệu đang để `AllowAny`
- cart đang dựa vào `customer_id` từ query param
- business rule `active/in_stock` chưa nhất quán
- test coverage rất mỏng

Nếu giữ nguyên, dữ liệu hành vi thu được sẽ bẩn và AI layer học sai.

## Phạm vi xử lý

### `product-service`

- khóa quyền create/update/delete cho staff hoặc admin
- chuẩn hóa rule `is_active`, `stock`, `variant stock`
- validate giá không âm
- validate dữ liệu product khi create/update

### `cart-service`

- bỏ quyền public cho thao tác sửa cart
- gắn cart với user thật hoặc session thật
- phân biệt rõ `add item` và `update quantity`
- chặn add product inactive hoặc không bán được

### `customer-service`

- khóa CRUD public ngoài các action cần thiết
- giữ `register`, `login`, `profile`, `update_profile`

### `staff-service`

- khóa CRUD public
- chỉ mở đúng luồng staff login và endpoint nội bộ cần thiết

## Việc phải làm

1. Rà toàn bộ `permission_classes` và default permission ở từng service.
2. Chuyển các `ModelViewSet` public sang action/API tối thiểu cần thiết.
3. Chuẩn hóa auth flow cho customer và staff.
4. Refactor cart ownership.
5. Thêm validation cho `base_price`, `price_override`, `status`, `quantity`.
6. Viết test cho:
   - unauthorized write
   - product inactive
   - cart add/update/remove
   - auth flow cơ bản

## Deliverable

- permission policy mới
- core API không còn lộ CRUD công khai
- business rules thống nhất
- test cơ bản cho auth, product, cart

## Definition of Done

- anonymous user không thể sửa product/cart/customer/staff tùy ý
- cart không thể bị sửa bằng cách giả `customer_id`
- product inactive hoặc invalid không lọt vào flow bán hàng
- test core pass ổn định

## Phụ thuộc

Phụ thuộc `01-mvp-architecture.md`.
