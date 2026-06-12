# Plan 14C: Role And Permission Model

## Trang thai

Draft for review.

## Muc tieu

Them role `shipper` va tach quyen ro giua customer, admin, shipper.

## Role

```text
customer
admin
shipper
```

## Customer permissions

Customer duoc:

- xem san pham;
- thao tac cart cua minh;
- checkout;
- xem order cua minh;
- xem timeline cua order cua minh.

Customer khong duoc:

- create shipment;
- assign shipper;
- update shipment/order delivery status;
- verify order;
- xem order cua nguoi khac.

## Admin permissions

Admin duoc:

- xem tat ca order;
- verify order;
- assign/reassign shipper;
- xem tat ca shipment;
- override mot so status hop le;
- quan sat dashboard van hanh.

Admin khong nen:

- thao tac cart thay customer trong luong customer UI.

## Shipper permissions

Shipper duoc:

- xem shipment/order duoc assign cho minh;
- accept/start delivery;
- mark delivered;
- report failed;
- cap nhat vi tri hien tai.

Shipper khong duoc:

- verify order;
- assign don cho shipper khac;
- cancel order;
- completed order theo nghia admin/system;
- xem shipment/order khong duoc assign.

## BE can co

Can xac dinh source of truth cho role:

- Neu staff-service dang quan ly staff/admin, them role `shipper` vao staff-service.
- Neu customer-service dang quan ly user chung, can tach user role tai day.
- Neu hien tai chua co auth that, co the lam MVP bang header noi bo tam thoi:
  - `X-User-ID`
  - `X-User-Role`

## FE can co

- Router guard cho:
  - customer routes;
  - admin routes;
  - shipper routes.
- Header/nav rieng theo role.
- Khong render action ma role khong co quyen.

## API authorization can co

- Endpoint customer chi scope theo `customer_id` hoac `session_key`.
- Endpoint admin yeu cau admin role/internal key.
- Endpoint shipper yeu cau shipper role va `shipper_id` match assignment.

## Test cases

1. Customer khong goi duoc create shipment.
2. Customer khong goi duoc assign shipper.
3. Shipper chi list duoc shipment cua minh.
4. Admin doi duoc shipper.
5. Role sai bi 403.

## Definition of Done

- Khong con lan quyen customer/shipping/admin.
- Role `shipper` co luong rieng va permission rieng.
