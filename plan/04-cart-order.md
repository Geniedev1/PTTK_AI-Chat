# Plan 04: Cart and Order

## Mục tiêu

Hoàn thiện flow mua hàng từ cart sang order để tạo được tín hiệu nghiệp vụ chuẩn cho analytics và AI.

## Phạm vi

### Cart

- add item
- remove item
- update quantity
- get current cart

### Order

- create order từ cart
- lưu order item
- cập nhật order status
- xác định mốc mua thành công thật

## Thiết kế gợi ý

### Cart item

- `cart_id`
- `user_id`
- `product_id`
- `quantity`
- `price_snapshot`
- `updated_at`

### Order

- `id`
- `user_id`
- `status`
- `total_amount`
- `created_at`
- `updated_at`

### Order item

- `order_id`
- `product_id`
- `product_name_snapshot`
- `price_snapshot`
- `quantity`

### Order status

- `PENDING`
- `CONFIRMED`
- `PAID`
- `CANCELLED`
- `COMPLETED`

## Việc phải làm

1. Chuẩn hóa nghĩa của `add item` và `update quantity`.
2. Bổ sung `price_snapshot` nếu business cần.
3. Tạo `order-service`.
4. Thiết kế order schema và order item schema.
5. Viết API:
   - create order
   - get order
   - list user orders
   - update order status
6. Chốt mốc event mua thật dùng cho AI, ưu tiên `order_paid` hoặc `order_completed`.

## Deliverable

- cart API sạch
- `order-service` mới
- order flow hoàn chỉnh
- contract rõ giữa cart và order

## Definition of Done

- user có thể đi từ cart sang order
- order status có nghĩa rõ ràng
- hệ thống phân biệt được `tạo đơn` và `mua thành công`

## Phụ thuộc

Phụ thuộc `03-catalog-search.md`.
