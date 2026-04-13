# Plan 07: AI Service and Recommendation Baseline

## Muc tieu

Tao `ai-service` nhe de phuc vu:

- recommendation baseline chay duoc
- chat/retrieval layer o plan sau
- tich hop AI ngoai nhu OpenAI / ChatGPT API

Plan nay khong lam deep learning tu train. Muc tieu la demo chay duoc, giai thich duoc, de nang cap sau.

## Scope trong 5 ngay

### Bat buoc

- tao `ai-service`
- tao endpoint recommendation baseline
- lay du lieu tu `product-service`, `interaction-service`, `knowledge graph`
- scoring heuristic + graph signal
- co fallback cho cold-start
- co log reason de debug/demo

### Khong lam trong plan nay

- khong train model rieng
- khong xay ETL phuc tap
- khong can read model qua nang
- khong can recommendation cache precompute cau ky
- khong can A/B test

## Nguon du lieu

### Tu `product-service`

- product_id
- name
- short_description
- full_description
- category_id
- brand_id
- price
- stock
- tags
- attributes
- status

### Tu `interaction-service`

- top queries
- product gaps
- category interest
- event stream da chuan hoa

### Tu graph layer

- product neighbors
- user interest
- similar users
- query -> product relation

## Kien truc de xuat

`ai-service` la layer doc / score nhe:

- doc catalog tu `product-service`
- doc behavioral signal tu `interaction-service`
- doc graph signal tu `interaction-service/graph/*`
- tinh score va tra top-k

Khong query truc tiep nhieu DB core trong moi request neu co the. Co the dung in-memory cache nhe neu can, nhung khong bat buoc trong MVP.

## Recommendation baseline can co

### `/api/ai/recommend/home`

- trending products
- popular in interested category
- graph-neighbor boosted items neu co user/session context

### `/api/ai/recommend/product-detail`

- same category
- same brand
- same price band
- graph neighbors

### `/api/ai/recommend/cart`

- also viewed
- also bought
- category-compatible items
- graph neighbors tu cac product trong cart

## Scoring baseline

Scoring phai de giai thich. Moi item co tong diem tu:

- popularity score
- category match score
- brand match score
- price affinity score
- recent-interest score
- graph relation bonus

Response nen tra kem:

- `score`
- `reason_codes`
- `source_signals`

## Business rules

- loai item inactive
- uu tien item con hang
- khong tra lai item dang o context hien tai neu khong phu hop
- co fallback cho user moi / session moi

## API toi thieu

- `GET /api/ai/recommend/home`
- `GET /api/ai/recommend/product-detail?product_id={id}`
- `GET /api/ai/recommend/cart?session_id={id}`

Co the bo qua trong 5 ngay:

- `/recommend/search-assist`
- `/recommend/for-you`

## Viec phai lam

1. Tao `ai-service`.
2. Noi `ai-service` vao Docker va gateway.
3. Tao service lay du lieu tu product / interaction / graph.
4. Viet scoring baseline.
5. Viet 3 endpoint recommendation.
6. Tra kem `reason_codes` de giai thich.
7. Viet test API co ban.

## Deliverable

- `ai-service`
- recommendation endpoints baseline
- scoring logic giai thich duoc
- integration voi graph signal
- test co ban
- README / curl demo

## Definition of Done

- 3 endpoint recommendation chay duoc
- response on dinh cho user co lich su va cold-start
- co `reason_codes` hoac score breakdown o muc co ban
- khong can model tu train van recommend duoc

## Phu thuoc

Phu thuoc `05-interaction-tracking.md` va `06-knowledge-graph.md`.
