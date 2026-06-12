# Plan 10: Demo Readiness, Light Personalization, and Deploy

## Muc tieu

Hoan thien ban demo end-to-end:

- recommendation co personalization nhe
- chatbot grounded co logging co ban
- Docker stack chay duoc cho nguoi khac demo
- co tai lieu va flow demo ro rang

Plan nay khong nham muc production-grade observability.

## Scope trong 5 ngay

### Bat buoc

- user profile snapshot nhe
- personalization score nhe cho recommend
- personalization nhe cho chat retrieval
- structured logs co ban
- Docker / env / startup order on dinh
- README demo nhanh

### Khong lam trong plan nay

- khong lam dashboard metrics day du
- khong lam A/B testing
- khong lam uplift evaluation nghiem tuc
- khong lam model versioning
- khong lam monitoring production-grade

## Personalization baseline

`user_profile_snapshot` toi thieu:

- top categories
- top brands neu co
- recent viewed products
- recent searched queries
- recent graph-interest summary

Recommendation co the cong them diem khi:

- match top category
- match top brand
- gan price band user hay xem
- gan graph neighbors user vua tuong tac

Chat retrieval co the bias nhe theo:

- recent category interest
- recent product interest

## Logging toi thieu

- request_id
- user_id / session_id
- endpoint
- latency
- error_code neu co
- recommendation reason codes
- retrieved source ids cho chat

## Testing scope

- recommend endpoints
- chat endpoint
- realtime routing flow
- graph rebuild command
- Docker smoke test

## Deploy scope

- `docker-compose.yml` hoan chinh
- env vars mau
- startup order ro rang
- README chay nhanh
- demo script / curl examples

## Viec phai lam

1. Tao `user_profile_snapshot` nhe tu interaction/graph.
2. Cong score personalization vao recommendation baseline.
3. Bias retrieval nhe cho chat.
4. Them structured logging co ban.
5. Viet smoke test cho AI endpoints.
6. Chot Docker Compose va README demo.

## Deliverable

- personalization baseline nhe
- logs co ban de debug
- smoke tests
- Docker demo chay duoc
- README / demo script

## Definition of Done

- hai user/session co the nhan recommend hoi khac nhau
- chatbot van grounded khi co personalization nhe
- nguoi khac clone repo va chay demo duoc bang Docker
- co du log de giai thich output khi demo
