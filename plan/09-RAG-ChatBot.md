# Plan 09: RAG Chatbot and GraphRAG Integration

## Mục tiêu

Tạo chatbot grounded, trả lời dựa trên context thật từ catalog, FAQ và policy; đồng thời có thể tận dụng graph và user behavior để nâng chất lượng retrieval.

Plan này phải phân biệt rõ:
- fact retrieval
- realtime API routing
- personalization support
- graph-aware context expansion

## Knowledge source ban đầu

### Product knowledge

- product catalog
- product description
- category
- brand
- notable attributes

### Business knowledge

- FAQ
- shipping policy
- return policy
- payment policy

## Không đưa vào giai đoạn đầu qua vector DB

- realtime order status
- realtime inventory
- realtime price nếu thay đổi liên tục
- dữ liệu nhạy cảm không cần thiết

## Chuẩn bị dữ liệu retrieval

### Với product

Ghép text từ:
- tên sản phẩm
- mô tả ngắn
- mô tả dài
- category
- brand
- thuộc tính nổi bật

### Với policy/FAQ

- chunk theo ý nghĩa hoàn chỉnh
- tránh chunk quá dài
- tránh chunk quá vụn
- giữ metadata rõ ràng

## Vector layer

Mỗi chunk cần có:

- `text`
- `embedding`
- `source_type`
- `source_id`
- `product_id` nếu có
- `title`
- `category`
- `brand`
- `policy_type` nếu có

## GraphRAG layer

Ngoài vector retrieval, cần có graph retrieval:

- user recent-interest nodes
- related product neighbors
- category neighbors
- graph-derived similar products
- query-product relation nếu có

### Ý nghĩa

Chat không chỉ dựa vào semantic vector match, mà còn có thể:
- expand context theo relation
- cá nhân hóa vừa phải
- grounded tốt hơn trong domain e-commerce

## Chat flow chuẩn

1. nhận câu hỏi
2. classify intent sơ bộ
3. nếu là realtime intent thì route sang core API
4. nếu là catalog/policy intent thì:
   - embed query
   - retrieve top-k vector chunks
   - retrieve graph context liên quan
   - lấy user profile / behavior context nếu phù hợp
   - merge context
   - build prompt có guardrail
   - gọi LLM
5. trả lời có căn cứ hoặc fallback an toàn

## Intent routing bắt buộc

Các intent như:
- trạng thái đơn hàng
- giá hiện tại
- tồn kho hiện tại
- khuyến mãi realtime

không được chỉ dựa vào vector search.
Phải route sang core API thật rồi mới format câu trả lời.

## Personalization trong chat

Có thể thêm nhẹ:

- ưu tiên category user quan tâm
- ưu tiên brand user quan tâm
- bias retrieval theo price range user hay xem
- thêm “recent interest” vào context

Không được personalization quá mạnh tới mức bóp méo fact.

## Prompt guardrail

Prompt phải ràng buộc:

- chỉ trả lời dựa trên context được cung cấp
- không tự bịa tồn kho, giá, order status
- nếu thiếu dữ liệu thì nói không chắc / không có thông tin
- nếu là realtime question thì yêu cầu dùng API tương ứng

## Fallback behavior

- không có data phù hợp → trả lời an toàn
- retrieval yếu → xin user làm rõ
- intent động nhưng chưa có API → nói rõ giới hạn hiện tại

## Việc phải làm

1. Tạo pipeline chunking.
2. Tạo embedding pipeline.
3. Tạo vector index.
4. Viết chat endpoint trong `ai-service`.
5. Thiết kế prompt template có guardrail.
6. Tạo intent router cho câu hỏi realtime.
7. Tích hợp graph retrieval.
8. Tích hợp user profile / behavior context nhẹ.
9. Log retrieved source ids để debug và đo grounding.

## Deliverable

- vectorized product/policy data
- chat API
- prompt template
- intent routing logic
- graph retrieval integration
- chatbot UI hoặc demo endpoint
- log retrieved sources

## Definition of Done

- chatbot trả lời được câu hỏi về sản phẩm và chính sách
- biết fallback khi không có dữ liệu
- không khẳng định dữ liệu realtime nếu chưa gọi API thật
- có sử dụng graph context ở ít nhất 1 luồng retrieval
- có logging nguồn context để kiểm tra grounding

## Phụ thuộc

Phụ thuộc `06-knowledge-graph.md`, `07-ai-data-and-recommendation.md`, `08-behavior-modeling.md`.