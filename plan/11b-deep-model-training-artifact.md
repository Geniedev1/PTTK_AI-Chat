# Plan 11B: Deep Model Training and Artifact Packaging

## Trang thai

Planned.

## Muc tieu

Train duoc deep model MVP tren dataset da freeze tu Plan 11A, co metric ro rang, va dong goi artifact de dua vao runtime.

## Phu thuoc

- Plan 11A: dataset va label protocol
- Plan 11: deep-model umbrella

## Scope bat buoc

- chot cau hinh model MVP (MLP la mac dinh)
- train model tren train split
- tune nhe tren valid split
- bao cao metric tren test split
- package model artifact + metadata
- ghi lai train config de tai lap

## Kien truc model de xuat

- baseline: MLP 2-3 hidden layers + dropout
- loss: BCE hoac pairwise ranking loss nhe
- optimizer: Adam
- early stopping theo valid metric

Optional neu kip:

- sequence encoder nhe (GRU)
- calibration step nhe

## Metric bat buoc

- AUC
- F1 (neu binary)
- Recall@K (neu ranking framing)
- NDCG@K (neu ranking framing)

## Artifact packaging

- model weights
- preprocessing config (feature order, scaler, encoder)
- model metadata: version, train_time, dataset_version, metrics
- checksum file

## Viec phai lam

1. Chot model config v1.
2. Viet training script reproducible.
3. Train + validate + test.
4. Dong goi artifact va metadata.
5. Viet huong dan load artifact cho inference.

## Deliverable

- training script hoac notebook
- model artifact v1
- metric report train/valid/test
- metadata file de runtime doc duoc

## Definition of Done

- model train duoc tren dataset Plan 11A
- co metric test duoc ghi ro va luu artifact
- artifact load duoc trong moi truong runtime
- co model version de logging trong API

## Risk chinh

- overfit do du lieu nho
- metric dao dong do class imbalance
- artifact khong tuong thich voi pipeline inference

## Thu tu thuc hien

1. Train config v1
2. Training run
3. Validation/test report
4. Package artifact
5. Ban giao cho Plan 11C
