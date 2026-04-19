# Plan 07: Tich hop vao giao dien e-commerce

## Muc tieu

Bien phan data/model/graph/chat thanh tinh nang nhin thay duoc tren he thong.

## Phan UI bat buoc theo de bai

- Danh sach hang khi user search hay click/gio hang.
- Giao dien chat rieng cua he thong, khong phai giao dien mac dinh cua ChatGPT.

## Viec phai lam

1. Chot 3 diem tich hop recommendation:
   - Home
   - Product detail
   - Cart/search result
2. Them recommendation vao search/cart neu hien tai chua co.
3. Hoan thien trang chat rieng:
   - khung hoi dap
   - lich su tin nhan
   - loading state
   - source/debug info khi can
4. Dam bao event tracking duoc ban ra tu:
   - search
   - view detail
   - add to cart
   - chat
5. Tao script demo end-to-end:
   - search
   - click
   - add cart
   - graph update
   - chat/recommend thay doi

## Output bat buoc

- UI recommendation trong luong search/cart/detail
- UI chat rieng
- demo script thao tac

## Definition of Done

- User nhin thay recommendation khi tuong tac.
- Chat UI chay duoc trong frontend hien tai.
- Co luong demo lien mach tu data -> graph -> recommend/chat.

## Evidence can nop

- Screenshot UI trang san pham.
- Screenshot UI chat.
- Video demo 1-2 phut neu can.
