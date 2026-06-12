# Plan 14: Business Flow Overview

## Trang thai

Draft for review.

## Muc tieu

Chuan hoa lai nghiep vu ecommerce sau khi test thuc te phat hien user, admin va shipping dang bi lan quyen.

## Van de hien tai

1. Customer vao cart thay duoc checkout hoac shipping. Shipping khong phai quyen customer.
2. Checkout xong cart khong clear on dinh.
3. Checkout xong user khong thay order de theo doi.
4. Order chua co hanh trinh ro rang cho customer xem: confirmed, assigned, delivering, delivered, completed.
5. Chua co role shipper va page rieng cho shipper.
6. Admin chua co workflow verify order va doi shipper neu can.

## Role chuan

### Customer

- Xem san pham.
- Add to cart.
- Checkout.
- Theo doi order cua minh.
- Khong duoc tao shipping hoac doi trang thai shipping.

### Admin

- Xem tat ca order.
- Verify order.
- Xem shipper duoc gan.
- Doi shipper thu cong khi can.
- Quan sat timeline van hanh.

### Shipper

- Xem order/shipment duoc assign cho minh.
- Nhan don.
- Cap nhat trang thai giao hang.
- Khong duoc verify order, cancel order, doi shipper khac.

## Lifecycle de xuat

```text
PENDING
  -> CONFIRMED
  -> ASSIGNED_TO_SHIPPER
  -> OUT_FOR_DELIVERY
  -> DELIVERED
  -> COMPLETED
```

## Y nghia trang thai

- `PENDING`: customer checkout thanh cong, order vua duoc tao.
- `CONFIRMED`: admin verify order hop le.
- `ASSIGNED_TO_SHIPPER`: system/admin da gan shipper.
- `OUT_FOR_DELIVERY`: shipper da nhan va dang giao.
- `DELIVERED`: shipper bao da giao den nguoi nhan.
- `COMPLETED`: admin/system xac nhan don hoan tat.

## Thu tu trien khai

1. Sua customer checkout/cart/order visibility.
2. Chuan hoa order lifecycle va status transition.
3. Them role `shipper`.
4. Them API assign shipper.
5. Them page shipper.
6. Them admin verify/assign UI.
7. Test end-to-end theo luong customer -> admin -> shipper -> admin/customer tracking.

## Definition of Done

- Customer chi thay checkout trong cart.
- Checkout tao order va clear cart.
- User xem duoc order vua tao.
- Admin verify duoc order.
- System/admin assign duoc shipper.
- Shipper cap nhat duoc hanh trinh giao hang.
- Timeline order thong nhat tren customer/admin.
