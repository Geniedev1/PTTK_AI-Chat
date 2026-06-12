# Plan 05: Interaction Tracking and Behavioral Data Foundation

## Trang thai

Completed.

## Deliverable files

- [artifacts/05-interaction-tracking-summary.md](./artifacts/05-interaction-tracking-summary.md)

## Mục tiêu

Tạo nền dữ liệu hành vi chuẩn hóa, đủ ngữ cảnh, đủ chất lượng để phục vụ:

- xây Knowledge Graph
- recommendation baseline
- deep learning behavior analysis
- personalization
- chatbot / GraphRAG

Plan này là đầu vào bắt buộc cho các plan sau.

## Phạm vi event tối thiểu

Các event bắt buộc nên có:

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

Có thể bổ sung nếu hệ thống có:

- `wishlist_added`
- `wishlist_removed`
- `coupon_applied`
- `product_shared`

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
    "page": 1,
    "category_id": 10,
    "brand": "Logitech",
    "device_type": "desktop"
  }
}
Nguyên tắc dữ liệu
mọi event phải có timestamp
phải có user_id hoặc cơ chế anonymous/session identity
event name phải nhất quán
dữ liệu phải cho phép nối chuỗi hành vi theo session hoặc user
event phải đủ metadata để dùng cho analytics và training
Mapping hành vi sang tín hiệu AI

Không chỉ lưu raw log. Cần chuẩn bị tín hiệu cho AI:

product_viewed → interest thấp
product_clicked → interest thấp-trung bình
cart_item_added → interest cao
order_paid → intent/mua rất cao

Ví dụ trọng số ban đầu:

view = 1
click = 2
cart = 4
order = 6

Trọng số này sẽ được dùng sau cho:

weighted edge trong graph
scoring baseline
training label / feature
Luồng triển khai
MVP
tạo interaction-service hoặc interaction module riêng
nhận event từ frontend/backend
lưu event vào PostgreSQL
Nâng cấp
đẩy event qua message broker
consumer ghi event bất đồng bộ
thêm dead-letter hoặc retry nếu cần
Việc phải làm
Chốt taxonomy event.
Chốt schema event thống nhất.
Tạo interaction-service hoặc module interaction.
Map event từ frontend/backend vào schema.
Log đầy đủ query_text, page, position, source, session_id nếu có.
Viết endpoint nội bộ hoặc consumer để ingest event.
Tạo query/report kiểm tra chất lượng data.
Chuẩn bị mapping từ event sang AI signal / weighted signal.
Câu hỏi hệ thống phải trả lời được
user A đã search gì trong tuần này
query nào dẫn đến nhiều click
product nào được view nhiều nhưng ít add cart
user nào thêm giỏ nhưng chưa mua
category nào được quan tâm nhiều nhất theo ngày/tuần
hành vi nào sẽ feed vào graph và model
Deliverable
schema event hoàn chỉnh
service ghi event
dữ liệu interaction mẫu
tài liệu mapping event
query/report kiểm tra chất lượng data
bảng quy đổi event → weighted signal
Definition of Done
mọi event chính đều có timestamp
có session hoặc cách nối chuỗi hành vi
event name nhất quán
query kiểm tra hành vi chạy được
có thể sinh behavioral signal phục vụ graph và model
Phụ thuộc

Phụ thuộc vào các module core như product, cart, order, chat để lấy nguồn event.
