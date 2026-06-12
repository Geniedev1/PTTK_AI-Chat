# Plan 11A: Dataset and Label Protocol for Deep Ranking

## Trang thai

Planned.

## Muc tieu

Chot duoc dataset protocol co the tai tao de train deep model recommendation, khong leakage, va co quality gate ro rang.

## Phu thuoc

- Plan 05: interaction tracking
- Plan 08: behavioral profile runtime
- Plan 11: deep-model umbrella

## Scope bat buoc

- chot event-to-label mapping
- chot sample unit (user-item, session-item, hoac sequence window)
- chot split protocol (time-based hoac actor-bucket)
- xay dataset builder script reproducible
- xuat train/valid/test theo format thong nhat
- co data quality checks

## Label strategy de xuat

- positive manh: order_paid, order_completed
- positive vua: cart_item_added
- weak positive: product_clicked
- weak negative: viewed/clicked nhung khong co hanh vi tiep theo trong cua so T

Co the dung hai che do:

- binary label (phu hop/khong phu hop)
- weighted target theo signal_weight

## Split protocol

- uu tien time-based split de giam leakage
- giu nguyen actor scope (user/session) trong split
- ghi ro timestamp boundary cua tung split

## Feature schema MVP

- actor/profile: top categories, top brands, price bands, funnel stage, purchase_intent_score
- item: category_id, brand_id, base_price band, stock, is_active
- relation: graph neighbor score, interaction overlap, popularity score
- recency: count view/click/cart/purchase theo cua so 1d/7d/30d

## Data quality gate

- ty le null theo field chinh
- class balance check
- duplicate row check
- leakage check (feature tuong lai)
- min sample threshold theo split

## Viec phai lam

1. Chot label mapping va cua so thoi gian T.
2. Chot schema feature dau vao.
3. Viet dataset builder script.
4. Tao pipeline xuat train/valid/test.
5. Them script quality-check.
6. Ghi protocol vao artifact markdown.

## Deliverable

- dataset protocol document
- script build dataset reproducible
- train/valid/test dataset sample
- data quality report

## Definition of Done

- dataset co the tai tao bang 1 command
- split protocol ro rang, co timestamp boundary
- co quality report dat nguong toi thieu
- khong co leakage hien nhien trong feature set

## Risk chinh

- event semantics chua dong nhat giua service
- class imbalance qua cao
- session data bi dut quang hoac thieu identity

## Thu tu thuc hien

1. Label + split
2. Feature schema
3. Dataset builder
4. Quality gate
5. Freeze dataset v1 cho Plan 11B
