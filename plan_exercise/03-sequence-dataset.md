# Plan 03: Chuyen data sang sequence dataset cho RNN/LSTM/biLSTM

## Muc tieu

Tu `data_user500.csv` tao dataset sequence dung duoc cho 3 model sequence.

## Bai toan de xuat

Chon 1 bai toan ro rang va giu xuyen suot:

- Cach A: next-action classification.
- Cach B: predict add_to_cart/purchase intent tu chuoi hanh vi gan nhat.

De de bao cao, uu tien Cach B vi gan nghiep vu e-commerce hon.

## Feature schema de xuat

Moi step trong sequence gom:

- action id
- product id
- category id
- time delta
- vi tri trong session

Them actor-level feature neu can:

- tong so view/click/cart gan day
- so category da quan tam

## Viec phai lam

1. Chot max sequence length.
2. Chot cach pad/truncate.
3. Chot label:
   - binary
   - hoac multi-class
4. Tao script preprocess:
   - group theo user/session
   - sort theo timestamp
   - tao sequence window
5. Split train/valid/test theo user de tranh leakage.
6. Xuat artifact:
   - `train.pkl` hoac `train.npz`
   - tokenizer / vocab
   - label map
   - preprocess config

## Output bat buoc

- sequence dataset artifact
- protocol markdown
- script tai tao dataset

## Definition of Done

- Co the train model sequence tu artifact nay.
- Khong leakage user giua train/valid/test.
- Co file config mo ta feature va label.

## Evidence can nop

- 1 vi du sequence sample.
- Bang thong ke sequence length.
- Bang class balance.
