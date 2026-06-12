# Plan 03: Catalog and Search

## Trạng thái

Completed.

## Deliverable files

- [artifacts/03-catalog-search-summary.md](./artifacts/03-catalog-search-summary.md)

## Completion notes

- Product seed da duoc mo rong len catalog sample quy mo lon hon de phuc vu UI, search va AI baseline.
- Contract README da duoc cap nhat theo dung gateway route va cart session flow hien tai.

## Mục tiêu

Hoàn thiện catalog đủ giàu metadata để phục vụ UI, search, recommendation và RAG.

## Mở rộng product schema

Product tối thiểu nên có:

- `id`
- `name`
- `slug`
- `short_description`
- `full_description`
- `category_id`
- `brand`
- `price`
- `stock`
- `status`
- `image_urls`
- `attributes`
- `tags`
- `created_at`
- `updated_at`

## Hướng xử lý trong repo

### `product-service`

- nâng cấp schema product hiện có
- chuẩn hóa category, brand, product type
- bổ sung serializer và validation
- seed dữ liệu mẫu đủ phong phú

### Search

- search theo tên
- search theo category
- filter theo brand/category/price
- sort theo giá hoặc mới nhất

## Việc phải làm

1. Chốt schema product mới.
2. Cập nhật migration và seed data.
3. Viết API create/update/get/list product.
4. Bổ sung endpoint search tách biệt hoặc nâng cấp endpoint list có filter/search.
5. Đảm bảo response product đủ metadata cho frontend và AI.
6. Seed ít nhất `50-100` sản phẩm với mô tả có giá trị.

## Deliverable

- product schema mới
- search/filter/sort API
- dữ liệu seed đủ dùng
- docs cho contract catalog/search

## Definition of Done

- user xem được list và detail sản phẩm với metadata đầy đủ
- search keyword hoạt động ổn định
- filter/sort dùng được
- dữ liệu catalog đủ giàu để chatbot có context

## Phụ thuộc

Phụ thuộc `02-core-hardening.md`.
