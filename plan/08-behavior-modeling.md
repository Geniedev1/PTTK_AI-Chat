# Plan 08: Deferred Behavior Modeling

## Trang thai

Deferred for post-demo phase.

## Vi sao defer

Plan nay la phan deep learning / behavior modeling:

- user embedding tu hoc
- product embedding tu hoc
- next-item prediction
- purchase intent model
- GNN / sequence model
- offline training + evaluation

Phan nay khong phu hop muc tieu 5 ngay. Neu dua vao luc nay se lam cham:

- recommendation baseline
- chatbot MVP
- demo end-to-end

## Khong lam trong scope hien tai

- khong train model rieng
- khong lam dataset training chinh quy
- khong lam notebook / training pipeline
- khong lam MRR / Recall@K / F1 cho model tu train
- khong tich hop GNN, Transformer-lite, LSTM/GRU

## Neu can thay the trong MVP

Dung cac thanh phan sau thay cho model train:

- heuristic recommendation
- graph similarity
- weighted interaction signal
- user recent-interest summary
- retrieval + external AI API cho chat

## Dieu kien de mo lai plan nay sau demo

- da co `ai-service` baseline
- da co recommendation API chay on
- da co chatbot grounded MVP
- da co du interaction data de train
- da co tieu chi metric ro rang

## Future scope

Sau demo, co the mo lai plan nay voi 1 bai toan cu the:

- next product prediction
hoac
- user embedding for personalized recommendation

Khong nen mo lai theo scope qua rong ngay tu dau.
