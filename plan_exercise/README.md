# Exercise Plan Index

Thu muc nay tach de bai thanh cac plan nho de lam lan luot va de gom evidence cho bao cao.

## Muc tieu tong

Can dat du 4 nhom yeu cau:

1. Tao `data_user500.csv` voi 500 user va bo behavior dung format de bai.
2. Train va danh gia 3 model `RNN`, `LSTM`, `biLSTM`, chon `model_best`.
3. Xay `KB_Graph` bang `neo4j` tu du lieu hanh vi.
4. Xay `RAG + chat` dua tren `KB_Graph` va tich hop vao UI e-commerce.

## Thu tu de xuat

1. [01-gap-analysis.md](./01-gap-analysis.md)
2. [02-data-user500.md](./02-data-user500.md)
3. [03-sequence-dataset.md](./03-sequence-dataset.md)
4. [04-train-rnn-lstm-bilstm.md](./04-train-rnn-lstm-bilstm.md)
5. [05-kb-graph-neo4j.md](./05-kb-graph-neo4j.md)
6. [06-rag-chat-graph.md](./06-rag-chat-graph.md)
7. [07-ecommerce-integration.md](./07-ecommerce-integration.md)
8. [08-evaluation-and-defense-pack.md](./08-evaluation-and-defense-pack.md)

## Mapping voi plan cu trong repo

- `02-data-user500` an khop voi Plan 05 va mot phan Plan 11A.
- `03-sequence-dataset` an khop voi Plan 11A.
- `04-train-rnn-lstm-bilstm` la plan moi de dap ung dung de bai, khong trung voi Plan 11B hien tai vi repo dang dung MLP.
- `05-kb-graph-neo4j` an khop voi Plan 06.
- `06-rag-chat-graph` an khop voi Plan 09 va mot phan Plan 10.
- `07-ecommerce-integration` an khop voi Plan 07, Plan 09, Plan 11C.
- `08-evaluation-and-defense-pack` an khop voi Plan 12A, 12B, 13.

## Nguyen tac lam

- Moi plan phai co artifact ro rang, khong chi co code.
- Moi plan phai co command tai tao.
- Moi plan phai co "evidence can nop" de luc bao cao khong bi thieu.
- Neu mot plan chua tao ra file/dataset/model/API/UI nhin thay duoc thi chua tinh la xong.
