# Implementation Plan

Thư mục này chứa roadmap triển khai theo thứ tự ưu tiên thực tế cho repo hiện tại.

## Danh sách plan

1. [01-mvp-architecture.md](./01-mvp-architecture.md)
2. [02-core-hardening.md](./02-core-hardening.md)
3. [03-catalog-search.md](./03-catalog-search.md)
4. [04-cart-order.md](./04-cart-order.md)
5. [05-interaction-tracking.md](./05-interaction-tracking.md)
6. [06-ai-data-and-recommendation.md](./06-ai-data-and-recommendation.md)
7. [07-rag-chatbot.md](./07-rag-chatbot.md)
8. [08-personalization-metrics-deploy.md](./08-personalization-metrics-deploy.md)

## Thứ tự triển khai

Thứ tự khuyến nghị:

`01 -> 02 -> 03 -> 04 -> 05 -> 06 -> 07 -> 08`

## Ghi chú

- `product-service`, `cart-service`, `customer-service`, `staff-service`, `api-gateway` đã tồn tại trong repo.
- `order-service`, `interaction-service`, `ai-service` là các thành phần dự kiến thêm mới ở các phase sau.
- Không triển khai Graph, GNN, GraphRAG trong roadmap này. Các phần đó để future work sau khi core và AI baseline ổn định.
