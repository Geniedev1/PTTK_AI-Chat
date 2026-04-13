# Cart and Order Summary

## Scope delivered in repo

- tao `order-service` moi
- them order schema va order item schema
- them API tao order tu `X-Cart-Session-Key`
- them API list order, get order va update status
- noi `order-service` vao `api-gateway` va `docker-compose`
- bo sung `price_snapshot` o `cart-service` de checkout co snapshot gia

## Order contract baseline

### Create order from cart

- `POST /api/orders/`
- request header can `X-Cart-Session-Key`
- body ho tro:
  - `customer_id` optional
  - `clear_cart` default `true`

Ket qua:

- tao `Order` status mac dinh `PENDING`
- tao `OrderItem` tu snapshot cart + product detail
- clear cart neu request cho phep va upstream cart clear thanh cong

### Read order

- `GET /api/orders/?customer_id={id}`
- `GET /api/orders/{id}?customer_id={id}`
- hoac dung `X-Cart-Session-Key` de scope theo session cart

### Update status

- `POST /api/orders/{id}/update_status`
- can `X-Internal-Admin-Key`
- status support:
  - `PENDING`
  - `CONFIRMED`
  - `PAID`
  - `CANCELLED`
  - `COMPLETED`

## Remaining gaps before calling Plan 04 complete

- chua co payment integration that su
- chua co event `order_paid` / `order_completed` day sang interaction tracking
- chua map session cart sang customer identity lien-service that
- chua co rule inventory reservation khi create order
