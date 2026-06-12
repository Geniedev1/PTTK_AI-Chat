# AI Service and Recommendation Summary

## Scope delivered in repo

- tao `ai-service` moi de phuc vu recommendation baseline
- noi `ai-service` vao `api-gateway` va `docker-compose`
- them 3 endpoint recommendation:
  - `GET /api/ai/recommend/home`
  - `GET /api/ai/recommend/product-detail`
  - `GET /api/ai/recommend/cart`
- scoring dung heuristic + interaction report + knowledge graph signal
- response tra kem `score`, `reason_codes`, `source_signals`
- co fallback cho cold-start va cart rong

## Data sources dang duoc dung

- `product-service` cho catalog va product detail
- `cart-service` cho current cart theo `X-Cart-Session-Key`
- `interaction-service` cho:
  - `product_gaps`
  - scoped event history
  - `graph/user_interest`
  - `graph/product_neighbors`
  - `graph/similar_users`

## Scoring baseline da co

- `popular`
- `recent_interest_category`
- `recent_interest_brand`
- `same_category`
- `same_brand`
- `price_band_match`
- `graph_neighbor`
- `cart_graph_neighbor`
- `similar_user_interest`
- `catalog_fallback`

## Verification

- `python -m py_compile` pass cho `ai-service`
- `docker compose run --rm --entrypoint python ai-service manage.py test recommendations.tests` -> `7/7` pass
- smoke test qua gateway pass:
  - `GET /api/ai/recommend/home`
  - `GET /api/ai/recommend/product-detail?product_id=6`
  - `GET /api/ai/recommend/cart?session_id=plan7-smoke-session`

## Remaining gaps after Plan 07

- chua goi AI ngoai; phan nay de cho Plan 09 chatbot/RAG
- scoring hien tai la explainable baseline, chua co cache hay precompute
- catalog smoke data hien chua co category/brand metadata day du nen mot so signal van dua nhieu vao graph + popularity
