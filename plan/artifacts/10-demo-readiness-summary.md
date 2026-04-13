# Demo Readiness and Personalization Summary

## Scope delivered in repo

- them `user_profile_snapshot` nhe trong `ai-service`
- them endpoint `GET /api/ai/recommend/profile/snapshot`
- dua `profile_snapshot` vao response cua recommend va chat retrieve
- cong them personalization baseline vao recommendation va chat retrieval
- them structured request logging co `request_id`, path, latency, user/session context
- giu runtime stable trong Docker stack hien tai

## Personalization baseline da co

- top categories
- top brands
- recent viewed product ids
- recent queries
- graph interest summary

Recommendation duoc cong them diem nhe cho:

- recent-view category match
- recent-view brand match
- recent query / profile affinity

Chat retrieval duoc bias nhe theo:

- recent viewed products
- top categories
- top brands
- recent queries

## Verification

- `python -m py_compile` pass
- `docker compose run --rm --entrypoint python ai-service manage.py test recommendations.tests` -> `15/15` pass
- smoke test qua gateway pass:
  - `GET /api/ai/recommend/profile/snapshot?session_id=plan7-smoke-session`
  - `GET /api/ai/recommend/home?session_id=plan7-smoke-session`
  - `POST /api/ai/chat/retrieve`
- `docker compose logs --tail 20 ai-service` xac nhan log co:
  - `request_id`
  - endpoint
  - latency
  - source ids
  - reason codes / snapshot context

## Demo notes

- khong can `OPENAI_API_KEY` de demo baseline
- neu co `OPENAI_API_KEY`, chat co the nang cap len grounded generation bang OpenAI Responses API
- smoke session hien tai van con data local trong DB demo
