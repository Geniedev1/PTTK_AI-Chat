# Plan 08: Personalization, Metrics, and Deploy

## Mục tiêu

Nâng hệ thống từ baseline sang mức có cá nhân hóa, đo được hiệu quả, và chạy được end-to-end bằng Docker.

## Personalization scope

### `user_profile_snapshot`

Tối thiểu nên có:

- top categories quan tâm
- top brands quan tâm
- khoảng giá hay xem
- recent viewed products
- recent searched queries

### Personalized recommendation

- cộng thêm điểm khi sản phẩm khớp preference snapshot
- vẫn giữ fallback cho cold-start user

### Personalized retrieval

- ưu tiên category/brand/price range user quan tâm
- không để personalization bó hẹp toàn bộ kết quả

## Metrics cần đo

### Recommendation

- CTR
- add-to-cart after recommendation
- purchase after recommendation

### Search

- search-to-click rate
- zero-result rate

### Chatbot

- retrieval hit rate
- fallback rate
- latency
- grounded answer rate

### System

- API error rate
- request latency
- event volume theo ngày

## Logging cần có

- request_id
- user_id
- endpoint
- latency
- error_code
- retrieved source ids cho chatbot
- reason/score component cho recommendation

## Deploy scope

- Dockerfile cho service còn thiếu
- `docker-compose.yml` hoàn chỉnh
- seed data
- env vars
- startup order
- demo script

## Việc phải làm

1. Tạo job build `user_profile_snapshot`.
2. Cộng score personalization vào recommend.
3. Thêm personalized retrieval nhẹ cho chat.
4. Viết test cho AI endpoint.
5. Thêm structured logging và metrics cơ bản.
6. Hoàn thiện Docker Compose cho toàn hệ.
7. Viết README/demo script/report.

## Deliverable

- personalization baseline
- metrics dashboard hoặc report query
- structured logs
- docker-compose chạy được
- tài liệu demo và báo cáo

## Definition of Done

- hai user khác history nhận gợi ý hơi khác nhau
- hệ thống có số liệu để demo
- người khác clone repo có thể chạy được bằng Docker

## Phụ thuộc

Phụ thuộc `07-rag-chatbot.md`.
