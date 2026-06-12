# Plan 14D: Shipper Assignment

## Trang thai

Draft for review.

## Muc tieu

Tu dong assign order cho shipper gan nhat dua tren vi tri hien tai, admin van co quyen thay doi.

## Trigger assign

De xuat trigger:

```text
Admin verify order
  -> Order CONFIRMED
  -> System tim shipper gan nhat
  -> Tao/cap nhat shipment
  -> Order ASSIGNED_TO_SHIPPER
```

## Data model can them

### Shipper profile

- `id`
- `user_id`
- `name`
- `phone`
- `current_lat`
- `current_lng`
- `is_available`
- `last_location_at`
- `created_at`
- `updated_at`

### Shipment assignment

Co the them vao `Shipment`:

- `shipper_id`
- `assigned_at`
- `accepted_at`
- `distance_km_snapshot`
- `assignment_source`: `system` hoac `admin`

### Delivery location

Order/shipment can co toa do dia chi giao:

- `delivery_lat`
- `delivery_lng`
- `address`
- `city`
- `country`

## Assignment algorithm MVP

1. Lay danh sach shipper available.
2. Loc shipper co location moi trong nguong thoi gian hop le.
3. Tinh khoang cach den delivery location.
4. Chon shipper co khoang cach nho nhat.
5. Gan shipment cho shipper.

Cong thuc MVP:

- Haversine distance.

## Manual override by admin

Admin co endpoint:

```text
POST /api/shipping/shipments/:id/assign_shipper
```

Payload:

```json
{
  "shipper_id": 12
}
```

Ket qua:

- shipment doi `shipper_id`;
- ghi assignment history;
- order van giu status neu da assigned;
- timeline ghi `shipper_reassigned`.

## Edge cases

- Khong co shipper available: order giu `CONFIRMED`, admin thay warning `No shipper available`.
- Shipper offline qua lau: khong duoc auto assign.
- Admin doi shipper sau khi shipper da out for delivery: can chan hoac yeu cau reason.
- Shipper reject/failed: system co the reassign sau.

## Test cases

1. Co 3 shipper, system chon shipper gan nhat.
2. Khong co shipper available, khong tao assignment sai.
3. Admin override shipper thanh cong.
4. Shipper khong duoc assign don cho chinh minh.
5. Assignment ghi history ro rang.

## Definition of Done

- Confirm order co the auto assign shipper.
- Admin doi duoc shipper.
- Assignment co audit/history.
