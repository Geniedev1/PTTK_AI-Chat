# Plan 12A: Recommendation Evaluation and Ablation

## Trang thai

Planned.

## Muc tieu

Danh gia dinh luong recommendation theo protocol E0/E1/E2 de chung minh tac dong cua behavioral profile va deep model.

## Phu thuoc

- Plan 08: behavioral profile runtime
- Plan 11C: runtime deep integration
- Plan 12: evaluation umbrella

## Scope bat buoc

- chot tap test offline cho recommendation
- chay 3 che do E0/E1/E2
- thu metric theo K (K=5,10 de xuat)
- tong hop bang ket qua va case-study
- xuat report co the tai lap

## Cau hinh ablation

- E0: heuristic-only
- E1: heuristic + behavioral profile
- E2: heuristic + behavioral profile + deep model

## Metric bat buoc

- Recall@K
- NDCG@K
- MRR@K
- Coverage@K

Neu kip:

- calibration check theo category/brand

## Segment bat buoc

- user history day
- user history it
- session anonymous
- cold-start item

## Viec phai lam

1. Freeze tap test recommendation.
2. Viet script benchmark E0/E1/E2.
3. Thu metric theo tung segment.
4. Tao bang truoc/sau va phan tich.
5. Tao 3 case-study minh hoa.

## Deliverable

- script evaluation recommendation
- metric table E0/E1/E2
- segment breakdown table
- case-study appendix

## Definition of Done

- script chay lai duoc ket qua
- co metric day du cho E0/E1/E2
- co ket luan ro ve trade-off quality/latency
- du bang chung de dua vao Plan 13

## Risk chinh

- test set nho gay noise
- protocol split khong on dinh
- metric khong phan biet ro giua E1 va E2
