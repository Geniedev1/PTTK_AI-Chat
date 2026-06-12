# Plan 11C: Inference and Runtime Ranking Integration

## Trang thai

Planned.

## Muc tieu

Dua deep model artifact vao runtime recommendation de tao deep_model_score trong xep hang, co fallback an toan, co logging va test.

## Phu thuoc

- Plan 08: behavioral profile runtime
- Plan 11B: deep model artifact
- Plan 11: deep-model umbrella

## Scope bat buoc

- load model artifact trong ai-service
- map feature runtime theo schema cua Plan 11A
- tinh deep_model_score cho candidate items
- tich hop score vao tong diem recommendation
- fallback heuristic-only khi model unavailable
- bo sung logging/model status
- them test cho model-on/model-off

## Scoring integration de xuat

Tong diem:

final_score = heuristic_score + alpha * deep_model_score

Trong do:

- alpha configurable qua env
- deep_model_score duoc clip theo range hop ly

## Runtime constraints

- latency p95 trong nguong cho phep
- khong vo API contract cu
- reason_codes van giai thich duoc

## Logging va observability

Toi thieu can co:

- model_version
- deep_model_score
- fallback_mode
- request_id

Cap nhat endpoint:

- GET /api/ai/models/status (model loaded hay khong, version nao)

## Viec phai lam

1. Viet module load artifact + preprocess runtime.
2. Them deep scoring vao recommendation pipeline.
3. Them fallback mode va guardrail khi inference loi.
4. Cap nhat logging va model status endpoint.
5. Viet test cho model-on/model-off.
6. Chay smoke test voi sample request.

## Deliverable

- inference module trong ai-service
- recommendation runtime co deep_model_score
- fallback heuristic-only mode
- cap nhat model status endpoint
- test pass cho path chinh

## Definition of Done

- deep_model_score duoc tinh trong runtime
- fallback chay on dinh khi model fail
- endpoint status hien duoc model version/load state
- test va smoke flow pass

## Risk chinh

- mismatch feature order giua train va runtime
- latency tang qua muc chap nhan
- model artifact loi version

## Thu tu thuc hien

1. Load artifact
2. Runtime feature mapping
3. Score integration
4. Fallback + logging
5. Test + smoke demo
