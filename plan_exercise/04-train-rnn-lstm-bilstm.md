# Plan 04: Train 3 model RNN, LSTM, biLSTM va chon model_best

## Muc tieu

Dat dung yeu cau de bai: co 3 model `RNN`, `LSTM`, `biLSTM`, danh gia, so sanh, va chon `model_best`.

## Ghi chu quan trong

Plan nay la phan repo hien tai chua co. Repo dang co `MLP`, nen phai them pipeline moi rieng cho exercise.

## Scope bat buoc

- framework sequence model: `PyTorch` hoac `TensorFlow/Keras`
- 3 model:
  - vanilla RNN
  - LSTM
  - bidirectional LSTM
- cung dataset, cung metric, cung split
- co plot loss/metric
- co file `model_best`

## Metric de xuat

Neu la binary classification:

- Accuracy
- Precision
- Recall
- F1
- ROC-AUC

Neu class imbalance cao, uu tien:

- F1
- Recall
- ROC-AUC

## Viec phai lam

1. Tao module huan luyen rieng cho sequence models.
2. Tao dataloader tu sequence artifact.
3. Implement 3 model dung chung interface.
4. Train va log metric train/valid/test.
5. Ve plots:
   - train loss
   - valid loss
   - valid F1 hoac AUC
6. Tao bang so sanh 3 model.
7. Chon `model_best` theo rule ro rang.
8. Luu:
   - weight file
   - config
   - metric report
   - plot png
   - `model_best` symlink hoac metadata pointer

## Output bat buoc

- `artifacts/exercise_models/rnn/*`
- `artifacts/exercise_models/lstm/*`
- `artifacts/exercise_models/bilstm/*`
- `artifacts/exercise_models/model_best/*`
- `comparison_report.md`

## Definition of Done

- 3 model chay duoc end-to-end.
- Co bang metric so sanh.
- Co plot minh hoa.
- Co giai thich vi sao chon `model_best`.
- `model_best` co the nap lai de infer.

## Evidence can nop

- Bang metric 3 model.
- 2-3 plot chinh.
- Doan nhan xet model nao tot nhat va vi sao.
