# Plan 02: Tao data_user500.csv

## Muc tieu

Sinh ra file `data_user500.csv` dung so luong 500 user va behavior schema phu hop de bai.

## Yeu cau de bai can bam

CSV toi thieu nen co:

- `user_id`
- `product_id`
- `action`
- `timestamp`

Neu can them cot phu cho huan luyen thi tao them 1 file khac, khong pha file nop bai.

## Scope ky thuat

Can quy doi event hien co thanh action de bai:

- `product_viewed` -> `view`
- `product_clicked` -> `click`
- `cart_item_added` -> `add_to_cart`
- Neu muon du 8 behavior thi chot them bo action extension:
  - `search`
  - `remove_from_cart`
  - `checkout`
  - `purchase`
  - `chat`

## Viec phai lam

1. Sua command sinh synthetic data de ho tro `--users 500`.
2. Tao command export file de bai:
   - output mac dinh: `interaction-service/data_user500.csv`
   - schema dung de bai
3. Tach 2 che do export:
   - `submission` cho file nop bai
   - `full` cho file phuc vu graph/model
4. Dam bao co it nhat 500 distinct `user_id`.
5. Dam bao timestamp hop le va co thu tu session.
6. Viet script check nhanh:
   - row count
   - distinct user count
   - action distribution
   - null check

## Output bat buoc

- `interaction-service/data_user500.csv`
- `interaction-service/data_user500_profile.json` hoac `quality_report.json`
- command README de tai tao file

## Definition of Done

- File ton tai trong repo.
- Co 500 distinct user.
- Cot dung format da chot.
- Co toi thieu 8 behavior neu bai bat buoc dem theo "behavior type".
- Co command mot dong de tai tao.

## Rui ro

- Schema file nop bai va schema training xung dot.
- Du lieu synthetic mat can bang qua lon.

## Evidence can nop

- 5 dong dau file CSV.
- Tong so dong, tong so user.
- Bieu do phan bo action.
