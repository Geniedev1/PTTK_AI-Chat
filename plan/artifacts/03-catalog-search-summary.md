# Catalog and Search Summary

## Mục tiêu đã xử lý

- mở rộng product schema để giàu metadata hơn
- giữ tương thích ngược với API cũ ở mức hợp lý
- thêm search/filter/sort phục vụ UI và AI
- bổ sung seed mẫu quy mô lớn hơn với mô tả và metadata tốt hơn
- thêm test khung cho serializer/search

## Schema mới trong product-service

Đã thêm vào `ProductModel`:

- `slug`
- `short_description`
- `tags`
- `image_urls`

Giữ lại:

- `description`

Quy ước mới:

- `description` tiếp tục là nội dung đầy đủ
- API response expose thêm `full_description` như alias của `description`
- API response có thêm `status` và `has_stock`

## Search contract mới

### Query params hỗ trợ

- `search`
- `category_id`
- `brand_id`
- `product_type_id`
- `in_stock`
- `min_price`
- `max_price`
- `sort_by`
- `tag`

### `sort_by` hỗ trợ

- `newest`
- `oldest`
- `price_asc`
- `price_desc`
- `name_asc`
- `name_desc`

### Endpoint

- `GET /api/products/` vẫn hỗ trợ filter/search như cũ
- `GET /api/products/search/` được thêm để rõ nghĩa cho frontend

## Quyết định tương thích ngược

- giữ field `description`
- thêm `full_description` thay vì đổi tên field cũ
- read product cũ vẫn dùng được
- create/update product có thể gửi `description` hoặc `full_description`

## File code chính đã thay đổi

- `product-service/modules/catalog/domain/entities/product.py`
- `product-service/modules/catalog/application/commands/create_product.py`
- `product-service/modules/catalog/application/commands/update_product.py`
- `product-service/modules/catalog/application/queries/filter_products.py`
- `product-service/modules/catalog/application/services/product_service.py`
- `product-service/modules/catalog/infrastructure/models/product_model.py`
- `product-service/modules/catalog/infrastructure/repositories/product_repository_impl.py`
- `product-service/modules/catalog/infrastructure/querysets/product_queryset.py`
- `product-service/modules/catalog/presentation/api/serializers/product_serializer.py`
- `product-service/modules/catalog/presentation/api/views/product_view.py`
- `product-service/modules/catalog/infrastructure/migrations/0002_expand_product_metadata.py`
- `product-service/modules/catalog/seeds/products_seed.py`
- `product-service/modules/catalog/tests/test_product_seed.py`

## Test đã thêm

- `product-service/modules/catalog/tests/test_product_catalog_search.py`

## Lưu ý còn lại

- seed data da duoc nang len baseline catalog sample quy mo lon hon cho UI, search va AI
- category/brand van chua duoc tach thanh bo seed management day du
- chưa có full-text search engine; search hiện vẫn là ORM-based search đủ cho MVP

## Điều kiện để sang Plan 04

- chấp nhận schema product mới là baseline cho cart/order/AI
- chấp nhận search hiện tại là baseline keyword search, chưa phải semantic search
