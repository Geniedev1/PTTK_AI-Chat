# Plan 09: RAG Chatbot MVP with External AI

## Muc tieu

Tao chatbot grounded cho e-commerce bang cach dung AI ngoai nhu OpenAI / ChatGPT API, khong tu host LLM, khong tu train model rieng.

Chatbot phai:

- tra loi duoc cau hoi ve san pham va policy
- biet fallback neu thieu du lieu
- route cau hoi realtime sang core API khi can
- co the dung graph context nhe neu co loi

## Scope trong 5 ngay

### Bat buoc

- chat endpoint trong `ai-service`
- embedding + retrieval cho product/policy text
- prompt template co guardrail
- realtime intent routing co ban
- tich hop OpenAI API

### Khong lam trong plan nay

- khong lam GraphRAG phuc tap
- khong lam multi-stage rerank cau ky
- khong lam intent classifier train rieng
- khong lam orchestration research-level

## Nguon du lieu retrieval

### Product knowledge

- name
- short_description
- full_description
- category / brand
- notable attributes

### Business knowledge

- FAQ
- shipping policy
- return policy
- payment policy

## Kien truc de xuat

`ai-service` se:

1. nhan user query
2. detect realtime hay retrieval question
3. neu la realtime:
   - goi core API that
   - format lai cau tra loi
4. neu la retrieval:
   - embed query bang external embedding API
   - lay top-k chunks
   - lay graph context nhe neu can
   - build prompt
   - goi chat completion API

## Realtime intents bat buoc

Nhung cau hoi sau khong duoc tra loi chi bang vector search:

- order status
- current stock
- current price neu can xac thuc runtime
- cart/order related status

Phai route sang API that roi moi tra loi.

## Personalization nhe

Co the them nhe:

- top category user quan tam
- recent viewed products
- recent searched queries

Khong duoc de personalization lam meo fact.

## Prompt guardrail

Prompt phai ro:

- chi dung context duoc cung cap
- khong tu dua gia / ton kho / order status neu chua goi API
- neu thieu context thi noi ro gioi han
- uu tien cau tra loi ngan, grounded, de kiem chung

## API toi thieu

- `POST /api/ai/chat`
- `POST /api/ai/chat/retrieve` neu muon tach debug

Response nen co:

- `answer`
- `sources`
- `used_realtime_api`
- `used_graph_context`

## Viec phai lam

1. Chon external AI provider.
2. Tao prompt template va config API key.
3. Tao chunking + embedding pipeline cho product/policy.
4. Tao retrieval layer.
5. Tao realtime intent router.
6. Viet chat endpoint.
7. Them logging nguon context.
8. Viet smoke test / demo script.

## Deliverable

- chat API MVP
- retrieval pipeline cho product/policy
- realtime routing co ban
- OpenAI integration
- source logging cho debug

## Definition of Done

- chatbot tra loi duoc cau hoi san pham / policy
- route duoc it nhat 1 nhom realtime intent
- khong hallucinate du lieu realtime khi chua goi API
- response co kem nguon context o muc co ban

## Phu thuoc

Phu thuoc `06-knowledge-graph.md` va `07-ai-and-recommend.md`.
