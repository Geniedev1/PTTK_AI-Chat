# Plan 11: Deep Model MVP for Behavioral Ranking

## Trang thai

Planned.

Split into executable subplans: 11A, 11B, 11C.

## Muc tieu

Dua deep model vao he thong recommendation o muc MVP de tang diem rubric va co bang chung ve nang luc modeling.

Plan 11 giu vai tro umbrella cho toan bo deep-model phase. Cac cong viec ky thuat chi tiet duoc tach sang:

- Plan 11A: dataset va label protocol
- Plan 11B: training va artifact
- Plan 11C: inference integration vao runtime

## Dau vao va phu thuoc

Phu thuoc vao:

- Plan 05: interaction tracking
- Plan 06: knowledge graph baseline
- Plan 08: behavioral profile runtime
- Plan 10: logging/deploy baseline

Du lieu va ky thuat chi tiet nam trong 11A-11C.

## Cau truc tach plan

### Plan 11A: Dataset and Label Protocol

- dong bo event taxonomy va feature schema
- dinh nghia label/split tranh leakage
- tao dataset builder reproducible

### Plan 11B: Deep Model Training and Artifact

- train deep model MVP (MLP hoac sequence nhe)
- ghi metric train/valid/test
- dong goi model artifact + metadata version

### Plan 11C: Inference and Runtime Integration

- dua deep_model_score vao recommendation ranking
- fallback heuristic khi model unavailable
- cap nhat status/logging/test cho runtime path

## Khong lam trong plan nay

- khong lam distributed training
- khong lam full feature store
- khong lam online learning
- khong lam heavy hyperparameter search
- khong lam production MLOps day du
- khong thay doi kien truc recommendation lon ngoai pham vi 11C

## Milestone gate

M1 (sau 11A): dataset protocol duoc freeze, co script tai tao.

M2 (sau 11B): model MVP train duoc, co metric ro rang.

M3 (sau 11C): runtime ranking su dung deep score, co fallback va test.

## Viec phai lam

1. Chot ranh gioi va phu thuoc giua 11A, 11B, 11C.
2. Chot milestone gate M1/M2/M3.
3. Theo doi rui ro quality/latency trong luc tich hop.
4. Chot DoD tong cho ca deep-model phase.

## Deliverable

- mot deep-model phase co roadmap ro rang va phan ra duoc theo 11A-11C
- cac artifact chi tiet duoc ban giao boi 11A, 11B, 11C

## Definition of Done

- Plan 11A, 11B, 11C deu dat DoD rieng
- deep_model_score duoc dung that trong runtime recommendation
- co metric va evidence du de di tiep Plan 12

## Risk chinh

- du lieu event lech hoac it positive signal
- leakage khi split khong dung
- model overfit do du lieu demo nho
- latency tang neu inference khong duoc toi uu

## Thu tu thuc hien de tranh no scope

1. Plan 11A
2. Plan 11B
3. Plan 11C
