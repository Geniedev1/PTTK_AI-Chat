# Plan 07: AI Data Layer and Recommendation Baseline

## Mục tiêu

Tạo AI read model riêng và recommendation baseline chạy được, giải thích được, không phụ thuộc runtime nặng vào core services.

Plan này đóng vai trò:
- cầu nối giữa dữ liệu thô và AI
- lớp baseline trước khi đưa deep learning vào
- lớp read model phục vụ recommend và chat

## AI read model đề xuất

### `ai_products`

Product đã làm sạch để dùng cho:
- retrieval
- recommend
- chat context

### `ai_user_events`

Interaction đã chuẩn hóa từ `interaction-service`

### `user_profile_snapshot`

Summary hành vi user để dùng cho:
- personalization baseline
- retrieval bias nhẹ
- explainability

### `recommendation_cache`

Top item gợi ý precomputed nếu cần

## Đồng bộ dữ liệu cần có

### Từ `product-service`

- product_id
- name
- short_description
- full_description
- category
- brand
- price
- stock snapshot
- tags
- attributes
- status

### Từ `interaction-service`

- search/view/click/cart/order/chat events đã chuẩn hóa

### Từ `knowledge graph`

- graph-derived relation nếu cần để enrich scoring
- product similarity signal
- user-interest signal

## Recommendation baseline cần có

### Home recommend

- trending products
- new arrivals
- recent-interest match
- popular in preferred category

### Product detail recommend

- same category
- same brand
- same price range
- overlapping attributes/tags
- graph-neighbor candidates nếu có

### Cart recommend

- also viewed
- also bought
- complementary items
- category-compatible items

## Logic scoring baseline

Scoring phải đơn giản nhưng giải thích được.

Ví dụ thành phần điểm:

- popularity score
- freshness score
- category match score
- brand match score
- price affinity score
- recent-interest score
- graph relation bonus

## Ràng buộc business

- loại item inactive
- loại item out-of-stock nếu business yêu cầu
- loại item user vừa mua nếu không phù hợp
- giữ fallback cho cold-start user

## API cần có

- `/recommend/home`
- `/recommend/product-detail`
- `/recommend/cart`

Có thể thêm:
- `/recommend/search-assist`
- `/recommend/for-you`

## Việc phải làm

1. Tạo `ai-service`.
2. Tạo schema read model cho AI.
3. Làm job sync product sang AI.
4. Làm job sync interaction sang AI.
5. Đọc signal từ graph nếu cần.
6. Xây scoring baseline có thể giải thích được.
7. Viết API recommendation.
8. Ghi log reason/score component cho debug và demo.

## Deliverable

- `ai-service` đầu tiên
- product sync pipeline
- interaction sync pipeline
- AI read model schema
- API recommendation
- logic scoring baseline
- tài liệu giải thích score component

## Definition of Done

- recommendation endpoint trả dữ liệu ổn định
- logic recommend giải thích được
- AI không phải query trực tiếp nhiều DB core cho mọi request
- có fallback cho cold-start
- có thể kết hợp data từ graph nếu cần

## Phụ thuộc

Phụ thuộc `05-interaction-tracking.md` và `06-knowledge-graph.md`.