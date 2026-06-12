# Interaction Tracking Summary

## Scope delivered in repo

- tao `interaction-service` moi de ingest event hanh vi
- chot taxonomy event va signal weight mapping trong code
- them event schema co `event_id`, `event_type`, `user_id`, `session_id`, `product_id`, `query_text`, `source`, `timestamp`, `metadata`
- them report API cho data quality, top query, product gap, abandoned cart va signal weights
- noi `interaction-service` vao `api-gateway` va `docker-compose`
- emit event tu `product-service`, `cart-service`, `order-service`

## Event coverage da co

- `search_performed`
- `product_viewed`
- `cart_viewed`
- `cart_item_added`
- `cart_item_removed`
- `cart_item_quantity_updated`
- `checkout_started`
- `order_created`
- `order_paid`
- `order_cancelled`
- `order_completed`

## Event coverage san sang cho frontend/chat

Interaction service da support ingest truc tiep cho:

- `product_clicked`
- `chat_started`
- `chat_message_sent`

Frontend hoac chat service co the goi `POST /api/interactions/events` de gui event theo schema chuan.

## Report API baseline

- `GET /api/interactions/events/data_quality`
- `GET /api/interactions/events/top_queries`
- `GET /api/interactions/events/product_gaps`
- `GET /api/interactions/events/abandoned_carts`
- `GET /api/interactions/events/category_interest`
- `GET /api/interactions/events/signal_weights`

## Remaining gaps after Plan 05

- chua co message broker hay async consumer
- `product_clicked` va chat events chua co producer backend mac dinh
- report hien tai o muc operational baseline, chua phai BI layer day du
