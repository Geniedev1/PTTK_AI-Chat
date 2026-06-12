# Event Catalog

## Mục tiêu

Danh sách event chuẩn để các plan sau có thể triển khai tracking mà không phải đặt tên lại từ đầu.

## Core business events

### Auth and account

- `customer_registered`
- `customer_logged_in`
- `staff_logged_in`

### Product discovery

- `search_performed`
- `product_clicked`
- `product_viewed`

### Cart

- `cart_item_added`
- `cart_item_removed`
- `cart_item_quantity_updated`
- `cart_viewed`

### Checkout and order

- `checkout_started`
- `order_created`
- `order_paid`
- `order_cancelled`
- `order_completed`

### Chatbot

- `chat_started`
- `chat_message_sent`
- `chat_response_generated`

## Recommended event schema

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
    "page": 1,
    "from_page": "search_result"
  }
}
```

## Required fields

- `event_id`
- `event_type`
- `timestamp`

## Strongly recommended fields

- `user_id`
- `session_id`
- `product_id`
- `query_text`
- `source`
- `metadata`

## Event semantics

### `search_performed`

- user submit search query
- metadata nên có `page`, `filters`, `result_count`

### `product_clicked`

- user click product từ search/listing
- metadata nên có `position`, `page`, `from_page`

### `product_viewed`

- user mở trang chi tiết product
- metadata nên có `referrer`, `source_list`

### `cart_item_added`

- user thêm product vào cart
- metadata nên có `quantity`, `price_snapshot` nếu có

### `order_paid`

- tín hiệu mua thật nên ưu tiên event này hoặc `order_completed`
- không dùng `order_created` làm purchase signal cuối cùng

### `chat_message_sent`

- user gửi câu hỏi cho chatbot
- metadata nên có `conversation_id`, `intent_guess` nếu có

## Quy tắc đặt tên

- dùng snake_case
- động từ ở thì quá khứ hoặc trạng thái hoàn tất
- giữ nghĩa nhất quán giữa frontend, backend, analytics và AI

## Quyết định cho MVP

- Logging ban đầu có thể lưu trực tiếp vào PostgreSQL.
- Chưa bắt buộc message broker ở MVP.
- Event phải đủ ngữ cảnh để recommendation và analytics dùng được ngay.
