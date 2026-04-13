# Plan 05: Interaction Tracking

## Mục tiêu

Tạo nguồn behavioral data chuẩn hóa để recommendation, personalization và chatbot có dữ liệu đáng tin.

## Event tối thiểu cần có

- `search_performed`
- `product_clicked`
- `product_viewed`
- `cart_item_added`
- `cart_item_removed`
- `cart_item_quantity_updated`
- `checkout_started`
- `order_created`
- `order_paid`
- `chat_started`
- `chat_message_sent`

## Event schema chuẩn

Ví dụ:

```json
{
  "event_id": "uuid",
  "event_type": "product_clicked",
  "user_id": 123,
  "session_id": "sess_001",
  "product_id": 456,
  "query_text": "tai nghe gaming",
  "source": "web",
  "timestamp": "2026-04-12T10:00:00Z",
  "metadata": {
    "position": 3,
    "page": 1
  }
}
```

## Hướng triển khai

### MVP đơn giản

- tạo `interaction-service`
- lưu event vào PostgreSQL

### Nâng cấp sau

- đưa event qua message broker
- consumer lưu event bất đồng bộ

## Việc phải làm

1. Chốt schema event.
2. Tạo service hoặc module interaction riêng.
3. Map event từ frontend/backend vào interaction schema.
4. Log đầy đủ query text, page, position, source nếu có.
5. Viết endpoint nội bộ hoặc consumer để ghi event.
6. Tạo query/report cơ bản để kiểm tra chất lượng data.

## Câu hỏi hệ thống phải trả lời được

- user A đã search gì trong tuần này
- query nào dẫn đến nhiều click
- product nào view nhiều nhưng không add cart
- user nào thêm giỏ nhưng chưa mua

## Deliverable

- schema event hoàn chỉnh
- service ghi event
- dữ liệu interaction mẫu
- tài liệu mapping event

## Definition of Done

- mọi event chính đều có timestamp
- có session hoặc cách nối chuỗi hành vi
- tên event nhất quán
- query kiểm tra hành vi chạy được

## Phụ thuộc

Phụ thuộc `04-cart-order.md`.
