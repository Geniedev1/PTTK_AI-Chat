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
11. [11-deep-model-mvp.md](./11-deep-model-mvp.md)
12. [11a-dataset-label-protocol.md](./11a-dataset-label-protocol.md)
13. [11b-deep-model-training-artifact.md](./11b-deep-model-training-artifact.md)
14. [11c-inference-integration.md](./11c-inference-integration.md)
15. [12-evaluation-ablation.md](./12-evaluation-ablation.md)
16. [12a-recommendation-evaluation-ablation.md](./12a-recommendation-evaluation-ablation.md)
17. [12b-chat-grounding-evaluation.md](./12b-chat-grounding-evaluation.md)
18. [13-defense-demo-readiness.md](./13-defense-demo-readiness.md)

## Thu tu trien khai

Thu tu khuyen nghi cho baseline demo-first:

`01 -> 02 -> 03 -> 04 -> 05 -> 06 -> 07 -> 09 -> 10`

`08` la advanced AI/ML phase. No khong nam trong scope 5 ngay ban dau, nhung da duoc dinh nghia lai thanh full-scope behavior modeling de mo rong sau khi baseline demo-first on dinh.

Thu tu khuyen nghi cho extension de toi da diem bao ve:

`08 -> 11 -> 11A -> 11B -> 11C -> 12 -> 12A -> 12B -> 13`

Y nghia:

- `08`: behavioral profile runtime cho recommend + chat
- `11`: umbrella cho deep-model phase
- `11A`: dataset va label protocol
- `11B`: deep model training + artifact
- `11C`: inference integration vao runtime ranking
- `12`: umbrella cho evaluation phase
- `12A`: recommendation evaluation + ablation
- `12B`: chat grounding evaluation
- `13`: demo-goi bao ve, rubric-evidence map, script trinh bay

## Ghi chu

- `product-service`, `cart-service`, `customer-service`, `staff-service`, va `api-gateway` da ton tai trong repo.
- `order-service` da duoc dua vao repo o baseline Plan 04.
- `interaction-service` da duoc dua vao repo o baseline Plan 05.
- `knowledge graph` baseline (Neo4j + graph query layer) da duoc dua vao repo o Plan 06.
- `ai-service` da duoc dua vao repo va duoc mo rong dan qua recommendation, chatbot, va personalization.
- Graph baseline da nam trong roadmap va da co o Plan 06.
- Plan 08 duoc giu vai tro bridge runtime; Plan 11 va 12 giu vai tro umbrella, con thuc thi chi tiet duoc tach thanh 11A-11C va 12A-12B de de quan ly scope va tang diem rubric.
- GNN, GraphRAG nang, SPD, va huong research sau DoD tiep tuc duoc de sau Plan 13.
