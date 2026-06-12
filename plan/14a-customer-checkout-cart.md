# Plan 14A: Customer Checkout And Cart

## Trang thai

Draft for review.

## Muc tieu

Sua luong customer checkout dung nghiep vu: customer chi checkout tu cart, khong duoc thao tac shipping.

## Bug can sua

1. Cart page dang cho customer thay shipping action.
2. Checkout thanh cong nhung cart khong clear on dinh.
3. Sau checkout FE chua refetch cart/order dung cach.
4. Neu clear cart fail, UI khong noi ro trang thai.

## Flow dung

```text
Customer add product
  -> Cart
  -> Checkout
  -> Order PENDING duoc tao
  -> Cart clear
  -> Redirect sang Orders hoac Order Detail
```

## FE changes

- Cart page chi hien nut `Checkout`.
- Bo moi nut/link/action shipping khoi customer cart.
- Checkout success:
  - invalidate/refetch cart query;
  - invalidate/refetch orders query;
  - redirect sang `/orders` hoac `/orders/:id`;
  - hien message neu cart clear fail.

## BE changes

- `order-service` create order phai tiep tuc clear cart sau khi tao order.
- Response checkout nen tra:
  - `order`;
  - `cart_cleared`;
  - warning neu cart clear fail.
- Neu can chac chan hon, them retry clear cart ngan.

## Permission

- Customer duoc:
  - add/update/remove cart;
  - checkout.
- Customer khong duoc:
  - create shipment;
  - assign shipper;
  - update delivery status.

## Test cases

1. Add product -> cart co item.
2. Checkout -> response 201 va co `order`.
3. Checkout -> cart empty sau khi refetch.
4. Checkout -> order hien trong Orders page.
5. Customer khong thay shipping action tren cart page.

## Definition of Done

- Cart customer khong con shipping action.
- Checkout tao order thanh cong.
- Cart clear sau checkout.
- User thay order moi trong danh sach order.
