# Plan 01: MVP Architecture and Scope

## Trạng thái

Completed for review.

## Deliverable files

- [artifacts/01-mvp-architecture-overview.md](./artifacts/01-mvp-architecture-overview.md)
- [artifacts/01-service-ownership.md](./artifacts/01-service-ownership.md)
- [artifacts/01-main-tables.md](./artifacts/01-main-tables.md)
- [artifacts/01-event-catalog.md](./artifacts/01-event-catalog.md)

## Mục tiêu

Khóa phạm vi MVP, chốt trách nhiệm từng service và xác định luồng dữ liệu chuẩn trước khi sửa code hoặc thêm AI feature.

## Trạng thái hiện tại

Repo đang có:

- `api-gateway`
- `product-service`
- `cart-service`
- `customer-service`
- `staff-service`

Repo chưa có:

- `order-service`
- `interaction-service`
- `ai-service`

## Phạm vi MVP đề xuất

Bao gồm:

- đăng ký và đăng nhập user
- danh sách và chi tiết sản phẩm
- search và filter cơ bản
- giỏ hàng
- tạo đơn hàng và cập nhật trạng thái
- recommendation baseline
- chatbot RAG cho sản phẩm và chính sách

Không bao gồm:

- thanh toán phức tạp
- livestream
- social feed
- dynamic pricing
- GraphRAG
- GNN

## Service ownership

### `product-service`

- source of truth cho catalog
- product, category, brand, product type
- search/filter cơ bản

### `cart-service`

- source of truth cho cart
- cart item
- cart state theo user/session

### `customer-service`

- source of truth cho customer profile
- auth của customer

### `staff-service`

- source of truth cho staff account
- quyền quản trị vận hành

### `order-service`

- source of truth cho order
- order item
- order status

### `interaction-service`

- source of truth cho behavioral events
- event schema chuẩn hóa
- query/report nội bộ cho AI và analytics

### `ai-service`

- read model cho AI
- recommendation
- RAG chatbot
- user profile snapshot

## Việc phải làm

1. Vẽ sơ đồ hệ thống mức service và DB.
2. Chốt service nào sở hữu dữ liệu nào.
3. Chốt danh sách bảng chính của từng service.
4. Chốt danh sách event nghiệp vụ chính.
5. Chốt rule phân biệt `source of truth` và `read model`.
6. Chốt môi trường chạy local bằng Docker Compose.

## Deliverable

- sơ đồ kiến trúc tổng thể
- danh sách service và trách nhiệm
- danh sách schema/bảng chính
- danh sách event chính
- tài liệu phạm vi MVP

## Definition of Done

Plan này hoàn thành khi có thể trả lời rõ:

- product nằm ở service nào
- order nằm ở service nào
- interaction được lưu ở đâu
- AI đọc dữ liệu từ đâu
- chatbot được phép lấy dữ liệu gì

## Phụ thuộc

Không phụ thuộc plan nào khác. Đây là plan gốc.
