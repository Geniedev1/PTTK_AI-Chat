# MVP Architecture Overview

## Mục tiêu của MVP

MVP của repo này là một hệ e-commerce có:

- customer đăng ký và đăng nhập
- staff đăng nhập để quản trị
- product catalog
- search/filter sản phẩm cơ bản
- cart
- order
- interaction tracking
- recommendation baseline
- chatbot RAG cho sản phẩm và chính sách

## Phạm vi hiện tại của repo

Đã có trong repo:

- `api-gateway`
- `product-service`
- `cart-service`
- `customer-service`
- `staff-service`

Chưa có trong repo nhưng sẽ thêm ở các plan sau:

- `order-service`
- `interaction-service`
- `ai-service`

## Runtime topology

```text
Client
  -> API Gateway
     -> Customer Service
     -> Staff Service
     -> Product Service
     -> Cart Service
     -> Order Service        (planned)
     -> Interaction Service  (planned)
     -> AI Service           (planned)
```

## Data topology

```text
Customer Service -> customer-db (MySQL)
Staff Service    -> staff-db    (MySQL)
Product Service  -> product-db  (PostgreSQL)
Cart Service     -> cart-db     (PostgreSQL)
Order Service    -> order-db    (PostgreSQL, planned)
Interaction Svc  -> interaction-db (PostgreSQL, planned)
AI Service       -> ai-db + vector index + Redis (planned)
```

## Source of truth and read model

### Source of truth

Là nơi ghi nhận dữ liệu nghiệp vụ chính thức:

- customer profile
- staff account
- product catalog
- cart state
- order state
- interaction event

### Read model

Là dữ liệu phục vụ suy luận hoặc truy vấn tối ưu:

- AI products snapshot
- user profile snapshot
- recommendation cache
- vectorized documents

Nguyên tắc:

- core service giữ source of truth
- AI service không được tự định nghĩa lại nghiệp vụ core
- AI service đọc từ sync/read model, không join runtime nặng vào nhiều DB core

## API surface hiện tại

### Qua gateway

- `/api/staff/`
- `/api/customers/`
- `/api/cart/`
- `/api/products/`

### Dự kiến thêm

- `/api/orders/`
- `/api/interactions/`
- `/api/ai/recommend/`
- `/api/ai/chat/`

## Hướng triển khai tuần tự

1. Hardening core hiện có
2. Mở rộng catalog và search
3. Hoàn thiện cart và order
4. Chuẩn hóa interaction tracking
5. Tạo AI read model
6. Recommendation baseline
7. RAG chatbot
8. Personalization, metrics, deploy

## Quyết định kiến trúc cho MVP

- Giữ repo hiện tại, không xoa va lam lai tu dau.
- Giữ microservice topology đang có.
- Thêm service mới theo nhu cầu thay vì reset toàn hệ.
- Chưa đưa RabbitMQ, Neo4j, GraphRAG, GNN vào MVP.
- AI được triển khai sau khi core và tracking ổn định.
