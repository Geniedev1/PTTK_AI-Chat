# Plan 14G: Implementation Roadmap

## Trang thai

Draft for review.

## Muc tieu

Chia nho cong viec de trien khai khong bi roi, uu tien sua bug dang can truoc roi moi them role shipper.

## Phase 1: Customer checkout fix

Scope:

- Bo shipping action khoi customer cart.
- Checkout tao order.
- Checkout clear cart.
- Orders page hien order moi.

Files likely touched:

- `frontend/src/pages/customer/CartPage.tsx`
- `frontend/src/pages/customer/OrdersPage.tsx`
- `frontend/src/shared/api/services.ts`
- `order-service/orders/views.py`

Done khi:

- User checkout xong cart empty.
- User thay order trong Orders page.

## Phase 2: Order timeline

Scope:

- Chuan hoa status order.
- Hien timeline tren order detail.
- Them filter `order_id` cho shipment neu can.

Files likely touched:

- `order-service/orders/models.py`
- `order-service/orders/serializers.py`
- `order-service/orders/views.py`
- `shipping-service/shipments/views.py`
- customer order UI.

Done khi:

- User/admin thay cung mot timeline.

## Phase 3: Role shipper

Scope:

- Them role `shipper`.
- Them permission cho shipper.
- Guard route FE.

Files likely touched:

- `staff-service` hoac `customer-service` tuy source of truth role.
- gateway/auth helper neu co.
- frontend router/layout.

Done khi:

- Shipper co route rieng.
- Customer khong truy cap duoc shipping/admin action.

## Phase 4: Shipper assignment

Scope:

- Them shipper profile.
- Them `shipper_id` vao shipment.
- Auto assign nearest shipper.
- Admin override.

Files likely touched:

- `shipping-service/shipments/models.py`
- `shipping-service/shipments/serializers.py`
- `shipping-service/shipments/views.py`
- migrations.

Done khi:

- Confirm order co the assign shipper gan nhat.
- Admin doi duoc shipper.

## Phase 5: Shipper page

Scope:

- Dashboard shipper.
- Assigned order list.
- Detail + actions.

Routes:

- `/shipper`
- `/shipper/orders`
- `/shipper/orders/:id`

Done khi:

- Shipper nhan don va update delivery status duoc.

## Phase 6: Admin ops page

Scope:

- Admin order list/detail.
- Verify order.
- Reassign shipper.
- Monitor status.

Done khi:

- Admin quan sat duoc toan bo hanh trinh don.

## Phase 7: End-to-end tests

Scenario chinh:

```text
Customer add cart
Customer checkout
Cart clear
Customer sees order PENDING
Admin confirms order
System assigns nearest shipper
Shipper starts delivery
Shipper marks delivered
Admin/system completes order
Customer sees completed timeline
```

## Risk can quyet dinh som

1. Role source of truth nam o `staff-service` hay `customer-service`.
2. Delivery location lay toa do tu dau: user input, mocked data, hay geocoding sau.
3. `COMPLETED` do admin bam hay system auto sau `DELIVERED`.
4. Payment co bat buoc truoc confirm/ship khong.

## De xuat mac dinh

- Lam Phase 1 truoc vi dang la bug test that.
- Dung `staff-service` cho admin/shipper neu customer-service chi phuc vu customer.
- MVP location dung lat/lng mock trong address/shipment, chua can geocoding.
- `DELIVERED -> COMPLETED` de admin verify trong MVP.
