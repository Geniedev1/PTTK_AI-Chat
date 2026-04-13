# Plan 07: RAG Chatbot

## Mục tiêu

Tạo chatbot grounded, trả lời dựa trên context thật từ catalog và policy, không trả lời kiểu đoán mò.

## Knowledge source ban đầu

- product catalog
- FAQ
- shipping policy
- return policy
- payment policy

## Không đưa vào giai đoạn đầu

- realtime order data qua vector DB
- realtime inventory qua vector DB
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

- chia chunk theo ý nghĩa hoàn chỉnh
- tránh chunk quá dài hoặc quá vụn

## Vector layer

Mỗi chunk cần có:

- text
- embedding
- `source_type`
- `source_id`
- `product_id` nếu có
- title/category metadata

## Chat flow

1. nhận câu hỏi
2. embed query
3. retrieve top-k chunks
4. build prompt có guardrail
5. gọi LLM
6. trả lời có căn cứ

## Realtime intent

Các intent như:

- trạng thái đơn hàng
- giá hiện tại
- tồn kho hiện tại

không được chỉ dựa vào vector search. Phải route sang core API phù hợp rồi mới format câu trả lời.

## Việc phải làm

1. Tạo pipeline chunking.
2. Tạo embedding pipeline.
3. Tạo vector index.
4. Viết chat endpoint trong `ai-service`.
5. Thiết kế prompt template có guardrail.
6. Tách nhánh realtime intent nếu user hỏi order status hoặc dữ liệu động.

## Deliverable

- vectorized product/policy data
- chat API
- prompt template
- chatbot UI hoặc demo endpoint

## Definition of Done

- chatbot trả lời được câu hỏi về sản phẩm và chính sách
- biết fallback khi không có dữ liệu
- không khẳng định dữ liệu realtime nếu chưa gọi API thật

## Phụ thuộc

Phụ thuộc `06-ai-data-and-recommendation.md`.
