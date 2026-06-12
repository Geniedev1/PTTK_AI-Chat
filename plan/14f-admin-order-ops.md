# Plan 14F: Admin Order Operations

## Trang thai

Draft for review.

## Muc tieu

Admin quan sat, verify order, theo doi assignment va co quyen doi shipper.

## Admin order list

Can hien:

- Order id.
- Customer/session.
- Tong tien.
- Status.
- Payment status neu co.
- Shipper assigned neu co.
- Ngay tao.
- Warning neu order can admin action.

## Admin order detail

Can hien:

- Thong tin order.
- Items.
- Payment.
- Shipment.
- Shipper.
- Timeline.
- Audit/status history.
- Action hop le theo trang thai.

## Admin actions

### Verify order

```text
PENDING -> CONFIRMED
```

Sau khi confirm:

- system auto assign shipper neu co toa do va shipper available;
- neu khong assign duoc, admin thay warning.

### Reassign shipper

Admin co the:

- chon shipper khac;
- ghi reason neu order da bat dau giao;
- cap nhat assignment history.

### Complete order

```text
DELIVERED -> COMPLETED
```

Admin co the verify lan cuoi neu nghiep vu yeu cau.

## Dashboard metrics

- Pending orders.
- Confirmed but not assigned.
- Assigned orders.
- Out for delivery.
- Delivered waiting completion.
- Failed deliveries.

## API can co

```text
GET /api/admin/orders
GET /api/admin/orders/:id
POST /api/orders/:id/update_status
POST /api/shipping/shipments/:id/assign_shipper
GET /api/shipping/shippers
```

## Permission

Admin endpoint yeu cau:

- admin role; hoac
- internal admin key trong MVP.

## Test cases

1. Admin confirm order thanh cong.
2. Confirm order trigger auto assignment.
3. Admin reassign shipper thanh cong.
4. Admin complete order sau delivered.
5. Customer khong goi duoc admin endpoint.

## Definition of Done

- Admin co man hinh van hanh order.
- Admin verify va assign/reassign duoc.
- Timeline co audit ro rang.
