# Implementation Plan

Thu muc nay chua roadmap trien khai theo thu tu uu tien thuc te cho repo hien tai.

## Danh sach plan

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

## Thu tu trien khai

Thu tu khuyen nghi cho baseline demo-first:

`01 -> 02 -> 03 -> 04 -> 05 -> 06 -> 07 -> 09 -> 10`

`08` la advanced AI/ML phase. No khong nam trong scope 5 ngay ban dau, nhung da duoc dinh nghia lai thanh full-scope behavior modeling de mo rong sau khi baseline demo-first on dinh.

## Ghi chu

- `product-service`, `cart-service`, `customer-service`, `staff-service`, va `api-gateway` da ton tai trong repo.
- `order-service` da duoc dua vao repo o baseline Plan 04.
- `interaction-service` da duoc dua vao repo o baseline Plan 05.
- `knowledge graph` baseline (Neo4j + graph query layer) da duoc dua vao repo o Plan 06.
- `ai-service` da duoc dua vao repo va duoc mo rong dan qua recommendation, chatbot, va personalization.
- Graph baseline da nam trong roadmap va da co o Plan 06.
- GNN, GraphRAG, SPD, va behavior modeling learned phase thuoc Plan 08 va nen duoc trien khai theo tung pha sau khi baseline da on dinh.
