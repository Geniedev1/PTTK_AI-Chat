# Plan 06: AI Data Layer and Recommendation Baseline

## Mục tiêu

Tách AI sang read model riêng và ra recommendation baseline chạy được, không phụ thuộc runtime nặng vào core services.

## AI read model đề xuất

### `ai_products`

- product đã làm sạch cho retrieval và recommend

### `ai_user_events`

- interaction đã chuẩn hóa

### `user_profile_snapshot`

- summary hành vi user

### `recommendation_cache`

- top item gợi ý precomputed nếu cần

## Sync cần làm

### Từ `product-service`

- product_id
- name
- description
- category
- brand
- price
- stock snapshot
- tags
- attributes

### Từ `interaction-service`

- user view/click/cart/order/chat events

## Baseline recommendation

### Home recommend

- trending
- new arrivals
- user recent-interest match

### Product detail recommend

- same category
- same brand
- same price range
- overlapping attributes/tags

### Cart recommend

- also viewed
- also bought
- complementary items

## Việc phải làm

1. Tạo `ai-service`.
2. Tạo schema read model cho AI.
3. Làm job sync product sang AI.
4. Làm job sync interaction sang AI.
5. Xây scoring baseline có thể giải thích được.
6. Viết API:
   - `/recommend/home`
   - `/recommend/product-detail`
   - `/recommend/cart`
7. Loại bỏ item inactive hoặc out-of-stock khỏi kết quả.

## Deliverable

- `ai-service` đầu tiên
- product sync pipeline
- interaction sync pipeline
- API recommendation
- logic scoring baseline

## Definition of Done

- recommendation endpoint trả dữ liệu ổn định
- logic recommend giải thích được
- AI không phải query trực tiếp nhiều DB core cho mọi request

## Phụ thuộc

Phụ thuộc `05-interaction-tracking.md`.
