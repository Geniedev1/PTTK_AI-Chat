# Main Tables

## Current tables in repo

### Customer Service

#### `auth_user`

- built-in Django user
- username
- password hash
- email

#### `customer_customer`

- `id`
- `user_id`
- `phone`
- `address`
- `city`
- `country`
- `created_at`
- `updated_at`

### Staff Service

#### `auth_user`

- built-in Django user
- username
- password hash
- email

#### `staff_staff`

- `id`
- `user_id`
- `name`
- `email`
- `phone`
- `position`
- `created_at`
- `updated_at`

### Product Service

#### `catalog_products`

- `id`
- `name`
- `description`
- `category_id`
- `brand_id`
- `product_type_id`
- `base_price`
- `stock`
- `attributes`
- `is_active`
- `created_at`
- `updated_at`

#### `catalog_categories`

- `id`
- `name`
- `slug`
- `parent_id`

#### `catalog_brands`

- `id`
- `name`
- `slug`

#### `catalog_product_types`

- `id`
- `code`
- `name`
- `description`

#### `catalog_variants`

- `id`
- `product_id`
- `sku`
- `name`
- `attributes`
- `stock`
- `price_override`
- `is_default`
- `created_at`
- `updated_at`

### Cart Service

#### `cart_cart`

- `id`
- `customer_id`
- `product_id`
- `quantity`
- `created_at`
- `updated_at`

#### `cart_cartsession`

- `id`
- `session_key`
- `customer_id`
- `created_at`
- `updated_at`

## Planned tables

### Order Service

#### `orders`

- `id`
- `user_id`
- `status`
- `total_amount`
- `created_at`
- `updated_at`

#### `order_items`

- `id`
- `order_id`
- `product_id`
- `product_name_snapshot`
- `price_snapshot`
- `quantity`

### Interaction Service

#### `interaction_events`

- `event_id`
- `event_type`
- `user_id`
- `session_id`
- `product_id`
- `query_text`
- `source`
- `timestamp`
- `metadata`

### AI Service

#### `ai_products`

- product snapshot cho AI

#### `ai_user_events`

- event đã chuẩn hóa cho AI

#### `user_profile_snapshot`

- profile sở thích tóm tắt

#### `recommendation_cache`

- gợi ý precomputed

#### `vector_documents`

- chunk text
- embedding
- metadata

## Ghi chú cho plan tiếp theo

- `catalog_products` hiện còn thiếu `slug`, `short_description`, `full_description`, `image_urls`, `tags`.
- `cart_cart` hiện chưa gắn ownership đúng cách, đang chỉ giữ `customer_id` dạng số.
- `orders`, `interaction_events`, `ai_*` chưa tồn tại và sẽ được thêm ở các plan sau.
