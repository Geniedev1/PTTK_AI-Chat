# Implementation Plan

Thư mục này chứa roadmap triển khai theo thứ tự ưu tiên thực tế cho repo hiện tại.

## Danh sách plan

1. [01-mvp-architecture.md](./01-mvp-architecture.md)
2. [02-core-hardening.md](./02-core-hardening.md)
3. [03-catalog-search.md](./03-catalog-search.md)
4. [04-cart-order.md](./04-cart-order.md)
5. [05-interaction-tracking.md](./05-interaction-tracking.md)
6. [06-knowledge-graph.md](./06-knowledge-graph.md)
7. [07-ai-and-recommend.md](./07-ai-and-recommend.md)
8. [08-behavior-modeling.md](./08-behavior-modeling.md)
9. [09-RAG-ChatBot.md](./09-RAG-ChatBot.md)
10. [10-personalization-metrics-deploy.md.md](./10-personalization-metrics-deploy.md.md)

## Thứ tự triển khai

Thứ tự khuyến nghị:

`01 -> 02 -> 03 -> 04 -> 05 -> 06 -> 07 -> 08 -> 09 -> 10`

## Ghi chú

- `product-service`, `cart-service`, `customer-service`, `staff-service`, `api-gateway` đã tồn tại trong repo.
- `order-service` da duoc dua vao repo o baseline Plan 04.
- `interaction-service` da duoc dua vao repo o baseline Plan 05.
- `knowledge graph` baseline (Neo4j + graph query layer) da duoc dua vao repo o Plan 06.
- `ai-service` van la thanh phan du kien them moi o cac phase sau.
- Clarification: the repo now includes the Plan 06 knowledge graph baseline; only GNN and GraphRAG remain future work.
- Không triển khai Graph, GNN, GraphRAG trong roadmap này. Các phần đó để future work sau khi core và AI baseline ổn định.
