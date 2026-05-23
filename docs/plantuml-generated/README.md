# PlantUML Generated Diagrams

> **Nguyên tắc:** Toàn bộ sơ đồ trong thư mục này được tạo 100% dựa trên source code thực tế
> của project PTTK_AI-Chat. Không có thông tin nào được tự bịa hoặc giả định.
> Nguồn tham chiếu: models.py, views.py, serializers.py, urls.py, constants.py, knowledge_graph.py, docker-compose.yml.

---

## Danh sách sơ đồ đã tạo

| File | Loại | Mô tả | Dùng trong báo cáo |
|------|------|-------|---------------------|
| `01-usecase-overall.puml` | Use Case | Biểu đồ ca sử dụng tổng thể | Chương Phân tích yêu cầu |
| `02-staff-db.puml` | ERD | CSDL Staff Service (MySQL) — Staff, StaffProfile, StaffRoleAssignment, StaffActivityLog | Chương Thiết kế CSDL |
| `03-customer-db.puml` | ERD | CSDL Customer Service (MySQL) — Customer, CustomerProfile, CustomerAddress, CustomerActivityLog | Chương Thiết kế CSDL |
| `04-product-db.puml` | ERD | CSDL Product Service (PostgreSQL, DDD) — CategoryModel, BrandModel, ProductTypeModel, ProductModel, VariantModel | Chương Thiết kế CSDL |
| `05-cart-db.puml` | ERD | CSDL Cart Service (PostgreSQL) — Cart, CartSession, CartSnapshot, CartEvent | Chương Thiết kế CSDL |
| `06-order-db.puml` | ERD | CSDL Order Service (PostgreSQL) — Order, OrderItem, OrderStatusHistory, OrderNote | Chương Thiết kế CSDL |
| `07-payment-db.puml` | ERD | CSDL Payment Service (PostgreSQL) — Payment, PaymentMethod, PaymentTransaction, PaymentRefund | Chương Thiết kế CSDL |
| `08-shipping-db.puml` | ERD | CSDL Shipping Service (PostgreSQL) — Shipment, ShipmentAddress, ShipmentTrackingEvent, ShippingRate | Chương Thiết kế CSDL |
| `09-interaction-db.puml` | ERD | CSDL Interaction Service (PostgreSQL) — InteractionEvent, BehaviorProfile, SearchQueryLog, EventAggregate | Chương Thiết kế CSDL |
| `10-ai-service-db.puml` | ERD | CSDL AI Service — RecommendationRequest, RecommendationResult, ChatSession, ChatMessage | Chương Thiết kế CSDL |
| `11-neo4j-knowledge-graph-db.puml` | Graph | Knowledge Graph Neo4j — Nodes: User/Session/Product/Category/Brand/Query; Relationships: INTERACTED_WITH, SIMILAR_TO, BELONGS_TO, SEARCHED, MATCHES, ... | Chương AI & Knowledge Graph |

---

## Chi tiết từng sơ đồ

### 01-usecase-overall.puml — Use Case Diagram tổng thể

**Loại:** Biểu đồ ca sử dụng (Use Case Diagram)

**Dùng trong báo cáo:** Chương "Phân tích yêu cầu hệ thống" — phần tổng quan các chức năng

**Mô tả:**

Sơ đồ mô tả toàn bộ các ca sử dụng (use case) của hệ thống E-commerce Microservices + AI Service.

- **Actor chính:**
  - `Customer` — khách hàng sử dụng web/app
  - `Staff / Admin` — nhân viên quản lý hệ thống
  - `API Gateway` — điểm vào duy nhất (port 80), proxy đến các service
  - `AI Service` — service AI tự gọi các service khác để phục vụ gợi ý và chatbot

- **Nhóm use case theo domain:**

  | Nhóm | Use case nổi bật |
  |------|-----------------|
  | Xác thực (Auth) | Đăng ký, đăng nhập Customer/Staff, xem profile |
  | Danh mục sản phẩm | Xem/Tìm kiếm/Lọc/Chi tiết sản phẩm; Quản lý sản phẩm (Staff) |
  | Giỏ hàng (Cart) | Xem, thêm, xóa, cập nhật số lượng, clear giỏ |
  | Đặt hàng (Order) | Tạo đơn từ giỏ, xem lịch sử, cập nhật trạng thái (Staff) |
  | Thanh toán (Payment) | Tạo, xác nhận, hủy, hoàn tiền, báo thất bại |
  | Vận chuyển (Shipping) | Tạo vận đơn, cập nhật trạng thái giao hàng |
  | Tương tác & Knowledge Graph | Ghi nhận sự kiện, phân tích data quality, graph query (Neo4j) |
  | Dịch vụ AI | Gợi ý Home/Product-Detail/Cart, Chatbot RAG, Model Status |

- **Quan hệ include/extend** được đặt chính xác theo code thực tế:
  - `add_product` → include `product_detail` (kiểm tra sản phẩm trước khi thêm)
  - `create order` → include `cart_view` + extend `clear_cart`
  - `payment confirm` → include `order/update_status` → PAID
  - `create shipment` → include kiểm tra order PAID
  - `deliver shipment` → include `order/update_status` → COMPLETED
  - `AI recommend` → include graph queries từ interaction-service

---

## Kế hoạch sơ đồ tiếp theo

> Chờ bạn mô tả yêu cầu cụ thể cho từng phần bên dưới.

| File (dự kiến) | Loại | Mô tả dự kiến |
|----------------|------|----------------|
| `02-component-architecture.puml` | Component | Kiến trúc microservices tổng thể |
| `03-sequence-customer-shopping.puml` | Sequence | Luồng mua hàng: Browse → Cart → Order |
| `04-sequence-checkout-payment.puml` | Sequence | Luồng thanh toán và cập nhật trạng thái |
| `05-sequence-ai-recommendation.puml` | Sequence | Luồng AI gợi ý sản phẩm |
| `06-sequence-ai-chat.puml` | Sequence | Luồng Chat RAG với AI |
| `07-class-product-ddd.puml` | Class | Domain model Product Service (DDD) |
| `08-class-order-payment-shipping.puml` | Class | Class diagram Order/Payment/Shipping |
| `09-class-interaction-ai.puml` | Class | Class diagram Interaction & AI models |
| `10-er-all-services.puml` | ER | Entity-Relationship toàn bộ service |
| `11-activity-order-flow.puml` | Activity | Luồng xử lý đơn hàng |
| `12-state-order.puml` | State | State machine trạng thái Order |
| `13-state-payment.puml` | State | State machine trạng thái Payment |
| `14-state-shipment.puml` | State | State machine trạng thái Shipment |
| `15-deployment.puml` | Deployment | Sơ đồ triển khai Docker |

---

## Ghi chú kỹ thuật

- Tất cả API path được lấy từ `urls.py` + `BACKEND_API_DOCS.md`
- Auth token: `Authorization: Token <token>` (DRF TokenAuthentication)
- Cart session: `X-Cart-Session-Key` (UUID 40 ký tự)
- Admin access: `X-Internal-Admin-Key`
- Database per service: MySQL (staff, customer), PostgreSQL (cart, product, order, payment, shipping, interaction), Neo4j (knowledge graph)
- AI Service kết nối: product-service, cart-service, interaction-service (graph), OpenAI API
