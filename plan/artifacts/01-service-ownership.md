# Service Ownership

## API Gateway

### Vai trò

- entrypoint cho client
- route request sang backend service phù hợp
- chuẩn hóa access path qua `/api/...`

### Không sở hữu dữ liệu nghiệp vụ

- không phải source of truth
- không chứa business logic catalog/cart/order

## Customer Service

### Sở hữu

- customer account
- customer profile
- customer authentication

### Dữ liệu chính

- `Customer`
- liên kết với `User`

### Không sở hữu

- cart
- order
- product

## Staff Service

### Sở hữu

- staff account
- staff authentication

### Dữ liệu chính

- `Staff`
- liên kết với `User`

### Không sở hữu

- customer profile
- catalog
- cart
- order

## Product Service

### Sở hữu

- product catalog
- category
- brand
- product type
- variant

### Dữ liệu chính

- `ProductModel`
- `CategoryModel`
- `BrandModel`
- `ProductTypeModel`
- `VariantModel`

### Không sở hữu

- cart state
- order state
- customer account
- interaction log

## Cart Service

### Sở hữu

- current cart state
- cart item theo user/session

### Dữ liệu chính

- `Cart`
- `CartSession`

### Quan hệ với service khác

- tham chiếu `product_id` sang product-service
- sẽ tham chiếu `user/customer` theo auth flow được harden ở plan 02

## Order Service (planned)

### Sở hữu

- order
- order item
- order status
- payment/business transition đơn giản cho MVP

### Không sở hữu

- product catalog
- cart state
- behavioral events

## Interaction Service (planned)

### Sở hữu

- behavioral events
- session-level interaction history
- query/report nội bộ cho analytics và AI

### Không sở hữu

- business state của order/cart/product

## AI Service (planned)

### Sở hữu

- AI read model
- recommendation logic
- RAG chatbot
- user profile snapshot
- vector index

### Không sở hữu

- product source of truth
- order source of truth
- customer source of truth

## Nguyên tắc ownership

- Mỗi dữ liệu nghiệp vụ chỉ có 1 service làm source of truth.
- Các service khác chỉ tham chiếu bằng ID hoặc dùng API.
- AI service không update trực tiếp dữ liệu core.
- Interaction service chỉ log hành vi, không tự suy diễn trạng thái nghiệp vụ.
