# Plan 12: Evaluation, Ablation, and Benchmark Evidence

## Trang thai

Planned.

Split into executable subplans: 12A and 12B.

## Muc tieu

Chot bo bang chung dinh luong de bao ve he thong: cai tien do behavioral profile va deep model mang lai phai do duoc, lap lai duoc.

Plan nay khong tao them model moi. Trong tam la protocol danh gia va bao cao metric.

Plan 12 giu vai tro umbrella cho evaluation phase. Cong viec chi tiet duoc tach sang:

- Plan 12A: recommendation evaluation + ablation
- Plan 12B: chat grounding evaluation

## Dau vao va phu thuoc

Phu thuoc vao:

- Plan 08 da co behavioral profile runtime
- Plan 11 da co deep model MVP

Phu thuoc chi tiet cho recommendation/chat nam trong 12A va 12B.

## Cau truc tach plan

### Plan 12A: Recommendation Evaluation and Ablation

- protocol E0/E1/E2
- metric recommendation (Recall@K, NDCG@K, MRR@K, Coverage@K)
- bang ket qua va case-study recommendation

### Plan 12B: Chat Grounding Evaluation

- bo cau hoi danh gia retrieval va realtime routing
- metric grounding/source citation/hallucination flag
- bang ket qua chat va danh sach loi can sua

## Khong lam trong plan nay

- khong lam online A/B test production
- khong lam dashboard BI full
- khong lam significance study qua sau
- khong them model moi ngoai pham vi Plan 11

## Milestone gate

M1 (sau 12A): co bang metric recommendation E0/E1/E2.

M2 (sau 12B): co bang metric chat grounding va routing.

M3 (ket thuc 12): co report tong hop san sang cho Plan 13.

## Evidence format

- bang metric tong hop truoc/sau
- bang ablation theo E0/E1/E2
- 3-5 case study query minh hoa
- log trich xuat request_id + source_ids + retrieval_mode

## API/Tooling goi y

Toi thieu:

- script `make eval` hoac command tuong duong
- file report markdown/json trong plan artifacts

Khong bat buoc:

- endpoint cong khai cho evaluation

## Viec phai lam

1. Chot giao dien du lieu dau ra giua 12A va 12B.
2. Dong bo format metric report de tong hop.
3. Chot gate M1/M2/M3 truoc khi sang Plan 13.

## Deliverable

- evaluation umbrella protocol
- metric package tong hop tu 12A va 12B
- benchmark evidence san sang cho defense

## Definition of Done

- Plan 12A va 12B deu dat DoD rieng
- co report tong hop du bang chung cho Plan 13
- ket qua co the tai lap bang script hoac command ro rang

## Risk chinh

- test set qua nho dan den metric nhieu noise
- protocol khong nhat quan gay kho so sanh
- neu logging thieu, kho truy vet source evidence

## Thu tu thuc hien de tranh no scope

1. Plan 12A
2. Plan 12B
3. Tong hop metric package cho Plan 13
