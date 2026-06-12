# Plan 14E: Shipper Page

## Trang thai

Draft for review.

## Muc tieu

Them page rieng cho shipper de xem don duoc assign va cap nhat trang thai giao hang.

## Route de xuat

```text
/shipper
/shipper/orders
/shipper/orders/:id
```

## Shipper dashboard

Can hien:

- So don duoc assign.
- So don dang giao.
- So don da giao hom nay.
- Vi tri hien tai/cap nhat gan nhat.

## Assigned orders list

Moi item can hien:

- Order id.
- Trang thai.
- Ten nguoi nhan.
- So dien thoai.
- Dia chi.
- Khoang cach uoc tinh.
- Thoi gian assign.
- CTA xem chi tiet.

## Order detail for shipper

Can hien:

- Thong tin nguoi nhan.
- Thong tin order can giao.
- Dia chi giao.
- Phone.
- Tracking number.
- Timeline.
- Action theo trang thai.

## Allowed actions

```text
ASSIGNED_TO_SHIPPER -> OUT_FOR_DELIVERY
OUT_FOR_DELIVERY -> DELIVERED
OUT_FOR_DELIVERY -> DELIVERY_FAILED
```

UI actions:

- `Start delivery`
- `Mark delivered`
- `Report failed`

## Khong hien cho shipper

- Verify order.
- Assign/reassign shipper.
- Cancel order.
- Complete order.
- Thong tin noi bo admin khong can thiet.

## API can co

```text
GET /api/shipping/shipments?shipper_id=:id
GET /api/shipping/shipments/:id
POST /api/shipping/shipments/:id/start_delivery
POST /api/shipping/shipments/:id/deliver
POST /api/shipping/shipments/:id/fail
POST /api/shipping/shippers/:id/location
```

## Test cases

1. Shipper list chi thay shipment cua minh.
2. Shipper start delivery thanh cong.
3. Shipper mark delivered thanh cong.
4. Shipper khong update duoc shipment cua shipper khac.
5. Customer/admin timeline cap nhat sau thao tac shipper.

## Definition of Done

- Shipper co page rieng de van hanh don.
- Shipper chi thao tac duoc don duoc assign.
- Trang thai order/shipment cap nhat dong bo.
