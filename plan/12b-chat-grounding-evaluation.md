# Plan 12B: Chat Grounding and Realtime Routing Evaluation

## Trang thai

Planned.

## Muc tieu

Danh gia chat theo tieu chi grounded answer, source citation, va realtime routing precision de tao bang chung cho rubric RAG + chat.

## Phu thuoc

- Plan 09: RAG chatbot baseline
- Plan 08: behavioral profile context
- Plan 12: evaluation umbrella

## Scope bat buoc

- xay bo cau hoi danh gia chat
- tach nhom retrieval question va realtime question
- do metric grounding/citation/routing
- tong hop loi chat quan trong va huong khac phuc
- xuat report tai lap duoc

## Bo cau hoi de xuat

- policy Q&A (shipping/return/payment)
- product explain (feature, compatibility, summary)
- realtime order/cart/price/stock
- ambiguous query de test guardrail

## Metric bat buoc

- grounded answer rate
- source citation rate
- realtime routing precision
- hallucination flagged rate

Neu kip:

- response helpfulness rubric nhe (manual 1-5)

## Logging evidence

Can trich xuat tu log/response:

- used_realtime_api
- retrieval_mode
- source_ids
- request_id

## Viec phai lam

1. Chot bo cau hoi va expected behavior.
2. Viet script hoac checklist chay batch test.
3. Thu metric theo tung nhom cau hoi.
4. Tong hop cac truong hop hallucination.
5. Viet report va de xuat fix uu tien.

## Deliverable

- question set va expected outcomes
- chat evaluation script/checklist
- metric report grounding/routing
- issue list cho nhung loi nghiem trong

## Definition of Done

- co metric chat ro rang va tai lap duoc
- co bang chung source citation va routing
- co danh sach loi va muc do uu tien sua
- ket qua san sang dua vao Plan 13

## Risk chinh

- bo cau hoi khong dai dien du nganh muc
- danh gia manual thieu nhat quan
- log thieu thong tin de truy vet source
