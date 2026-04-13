# Plan 10: Personalization, Metrics, Evaluation, and Deploy

## Mục tiêu

Nâng hệ thống từ mức baseline lên mức:
- có personalization rõ ràng
- đo được hiệu quả
- có logging đủ để debug/demo
- chạy được end-to-end bằng Docker

Plan này là phần hoàn thiện sản phẩm và demo.

## Personalization scope

### `user_profile_snapshot`

Tối thiểu nên có:

- top categories quan tâm
- top brands quan tâm
- khoảng giá hay xem
- recent viewed products
- recent searched queries
- graph-interest summary nếu có
- model-derived preference signal nếu có

## Personalized recommendation

- cộng thêm điểm khi sản phẩm khớp preference snapshot
- cộng thêm điểm từ model embedding / intent signal
- vẫn giữ fallback cho cold-start

## Personalized retrieval for chatbot

- bias nhẹ theo category/brand/price range user quan tâm
- có thể dùng recent behavior hoặc embedding similarity
- không để personalization bóp hẹp toàn bộ kết quả

## Metrics cần đo

### Interaction / funnel

- search volume
- click-through rate
- add-to-cart rate
- purchase rate

### Recommendation

- CTR on recommended items
- add-to-cart after recommendation
- purchase after recommendation
- hit rate của reranking nếu có

### Chatbot

- retrieval hit rate
- fallback rate
- latency
- grounded answer rate
- realtime-intent routing success rate

### Model

- Recall@K / HitRate@K / MRR hoặc F1 tùy bài toán
- uplift so với baseline

### System

- API error rate
- request latency
- event volume theo ngày
- embedding/index build duration

## Logging cần có

- request_id
- user_id
- session_id
- endpoint
- latency
- error_code
- recommendation reason / score component
- retrieved source ids cho chatbot
- graph query trace nếu cần
- model version nếu có ML output

## Testing scope

### API tests

- recommend endpoints
- chat endpoint
- realtime intent router

### Data tests

- sync job
- graph build
- chunking/embedding consistency

### Demo tests

- hai user khác history nhận gợi ý hơi khác nhau
- chat cùng câu hỏi nhưng context retrieval khác nhẹ theo interest

## Deploy scope

- Dockerfile cho service còn thiếu
- `docker-compose.yml` hoàn chỉnh
- Neo4j / PostgreSQL / vector DB hoặc local index
- seed data
- env vars
- startup order
- demo script
- README chạy nhanh

## Việc phải làm

1. Tạo job build `user_profile_snapshot`.
2. Cộng score personalization vào recommend.
3. Thêm personalized retrieval nhẹ cho chat.
4. Tích hợp model output vào production-like flow.
5. Thêm structured logging và metrics cơ bản.
6. Viết test cho AI endpoint.
7. Hoàn thiện Docker Compose cho toàn hệ.
8. Viết README/demo script/report.

## Deliverable

- personalization baseline
- metrics dashboard hoặc report query
- structured logs
- test cơ bản
- docker-compose chạy được
- tài liệu demo và báo cáo

## Definition of Done

- hai user khác history nhận gợi ý hơi khác nhau
- chatbot có thể dùng personalization nhẹ nhưng vẫn grounded
- hệ thống có số liệu để demo
- có log đủ để giải thích recommendation/chat behavior
- người khác clone repo có thể chạy được bằng Docker

## Phụ thuộc

Phụ thuộc `07-ai-data-and-recommendation.md`, `08-behavior-modeling.md`, `09-rag-chatbot.md`.