# Plan 14B: Order Tracking Timeline

## Trang thai

Draft for review.

## Muc tieu

Cho customer theo doi duoc hanh trinh don hang sau checkout. Order page khong chi la lich su mua hang, ma phai la tracking page.

## Flow mong muon

```text
PENDING
  -> CONFIRMED
  -> ASSIGNED_TO_SHIPPER
  -> OUT_FOR_DELIVERY
  -> DELIVERED
  -> COMPLETED
```

## Customer Orders Page

Danh sach order can hien:

- Order id.
- Ngay tao.
- Tong tien.
- Trang thai hien tai.
- So luong item.
- CTA xem chi tiet.

## Customer Order Detail Page

Can hien:

- Thong tin order.
- Danh sach item.
- Tong tien.
- Trang thai hien tai.
- Timeline:
  - Order placed.
  - Confirmed.
  - Assigned to shipper.
  - Out for delivery.
  - Delivered.
  - Completed.
- Thong tin shipper neu da assign:
  - ten;
  - phone;
  - tracking number;
  - last update.

## BE data can tra

`order-service` nen tra:

- `status`
- `status_history`
- `items`
- `created_at`
- `updated_at`
- shipment/tracking info neu co the aggregate duoc

Neu order-service khong aggregate shipment, FE can goi:

```text
GET /api/orders/:id
GET /api/shipping/shipments?order_id=:id
```

Hien tai shipping-service chua co filter theo `order_id`, nen nen them query param nay.

## Status History

Moi lan doi status can ghi history:

- `old_status`
- `new_status`
- `changed_by`
- `metadata`
- `created_at`

## Test cases

1. Checkout xong order xuat hien trong Orders page.
2. Order detail hien item va tong tien dung.
3. Admin confirm -> customer refetch thay `CONFIRMED`.
4. Assign shipper -> customer thay shipper/tracking info.
5. Shipper update -> timeline cap nhat dung thu tu.

## Definition of Done

- User theo doi duoc don hang tu luc checkout den completed.
- Timeline co nghia ro va khong bi lech giua order-service/shipping-service.
