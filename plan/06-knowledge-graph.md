
Plan này kế thừa phần interaction tracking của plan cũ, nhưng được bổ sung thêm phần **weighted behavioral signal** để đúng hơn với yêu cầu file gốc là không dừng ở log thô mà phải chuẩn bị dữ liệu cho graph và AI model. :contentReference[oaicite:1]{index=1} :contentReference[oaicite:2]{index=2}

---

# 06-knowledge-graph.md

```md
# Plan 06: Knowledge Graph and Graph Data Layer

## Mục tiêu

Xây dựng graph-based knowledge base cho e-commerce để biểu diễn ngữ nghĩa và quan hệ giữa:

- User
- Product
- Category
- Query
- Brand
- Optionally: Cart / Order / Policy node ở giai đoạn sau

Graph là core subsystem, không phải phần phụ.

## Vì sao cần Knowledge Graph

Graph dùng để trả lời các câu hỏi mà bảng quan hệ truyền thống xử lý kém linh hoạt hơn:

- user quan tâm sản phẩm nào
- sản phẩm nào liên quan nhau
- query nào dẫn đến nhóm sản phẩm nào
- user nào có hành vi tương tự
- chatbot nên lấy thêm context nào ngoài vector search

## Graph schema đề xuất

### Node types

- `User`
- `Product`
- `Category`
- `Query`
- `Brand`

### Edge types

- `(User)-[:VIEWED]->(Product)`
- `(User)-[:CLICKED]->(Product)`
- `(User)-[:ADDED_TO_CART]->(Product)`
- `(User)-[:PURCHASED]->(Product)`
- `(User)-[:SEARCHED]->(Query)`
- `(Product)-[:BELONGS_TO]->(Category)`
- `(Product)-[:OF_BRAND]->(Brand)`
- `(Query)-[:MATCHES]->(Product)`
- `(Product)-[:SIMILAR_TO]->(Product)`

## Weighted edge

Không chỉ tạo edge đơn thuần. Cần edge có trọng số để phản ánh mức độ quan tâm.

Ví dụ:

`w(u,p) = 1*view + 2*click + 4*cart + 6*purchase`

Hoặc lưu:
- `count`
- `last_interacted_at`
- `weight`
- `event_types`

## Graph storage

### Giai đoạn đầu

- dùng `Neo4j`

### Lý do

- dễ mô hình hóa
- dễ query bằng Cypher
- rất phù hợp cho MVP, demo, research prototype
- dễ dùng cho graph retrieval trong chatbot

## Đồng bộ dữ liệu vào graph

### Từ `product-service`

- product_id
- name
- category
- brand
- tags
- attributes
- status

### Từ `interaction-service`

- search/view/click/cart/order/chat-related events

## Use cases phải hỗ trợ

### Recommendation

- sản phẩm tương tự theo graph
- người dùng tương tự
- sản phẩm cùng category / brand / overlap behavior

### Personalization

- top category user quan tâm
- top brand user quan tâm
- query/product path gần đây

### Chatbot / GraphRAG

- lấy user recent interest
- lấy product neighbors
- mở rộng context theo graph traversal
- hỗ trợ grounded response tốt hơn vector-only retrieval

## Việc phải làm

1. Thiết kế graph schema.
2. Chọn Neo4j và setup local/dev.
3. Tạo pipeline sync product sang graph.
4. Tạo pipeline sync interaction sang graph.
5. Tạo logic aggregate edge weight.
6. Viết Cypher query cho các use case chính.
7. Tạo script rebuild graph khi cần.
8. Tạo tài liệu mapping relational data → graph node/edge.

## Query hệ thống phải trả lời được

- user A quan tâm category nào nhiều nhất
- product nào liên quan mạnh tới product X
- query nào thường dẫn đến product Y
- user nào có hành vi gần giống user A
- từ product hiện tại nên expand context sang node nào cho chatbot

## Deliverable

- graph schema hoàn chỉnh
- Neo4j setup/dev guide
- sync pipeline product → graph
- sync pipeline interaction → graph
- Cypher query mẫu cho recommend/chat
- tài liệu mapping node/edge
- script rebuild graph

## Definition of Done

- graph build được từ data thật
- query graph chạy được
- có weighted edge rõ ràng
- graph hỗ trợ được cả recommend và chatbot context expansion
- không chỉ lưu raw relation mà có aggregation logic

## Phụ thuộc

Phụ thuộc `05-interaction-tracking.md` và dữ liệu từ `product-service`.