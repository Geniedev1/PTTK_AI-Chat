# RAG Chatbot MVP Summary

## Scope delivered in repo

- mo rong `ai-service` voi chatbot MVP grounded
- them endpoint:
  - `POST /api/ai/chat`
  - `POST /api/ai/chat/retrieve`
- them realtime intent routing cho:
  - order status
  - cart status
  - current price
  - current stock
- them retrieval layer doc product + policy document
- them graph context nhe tu `interaction-service`
- them khung tich hop OpenAI qua Responses API va Embeddings API
- co fallback local neu chua cau hinh `OPENAI_API_KEY`

## Knowledge sources dang duoc dung

- `product-service` cho product content va runtime verification
- `order-service` cho order status
- `cart-service` cho current cart summary
- `interaction-service` cho:
  - `chat_message_sent`
  - `graph/user_interest`
  - `graph/query_paths`
- static policy docs trong `ai-service/knowledge_base/policies`

## Verification

- `python -m py_compile` pass cho chat files
- `docker compose run --rm --entrypoint python ai-service manage.py test recommendations.tests` -> `12/12` pass
- smoke test qua gateway pass:
  - realtime order status
  - realtime product price/stock
  - retrieval debug
  - retrieval answer fallback khi khong co OpenAI key

## Remaining gaps after Plan 09

- chua verify goi OpenAI that vi local stack chua co `OPENAI_API_KEY`
- retrieval hien la lexical fallback khi khong bat embedding API
- policy docs hien la baseline demo content, can thay bang tai lieu nghiep vu that neu muon demo sat domain hon
