# Plan 08: Advanced Behavior Modeling and Learned Personalization

## Muc tieu

Xay lop AI hoc hanh vi nguoi dung tu interaction logs va knowledge graph de:

- du doan san pham tiep theo
- hoc `user_embedding` va `product_embedding`
- du doan purchase intent
- tang chat luong recommendation
- bo sung behavioral context cho chatbot / RAG

Plan nay la phase AI/ML dung nghia. No dung graph baseline cua Plan 06, recommendation baseline cua Plan 07, chatbot grounded MVP cua Plan 09, va demo-ready stack cua Plan 10 lam nen.

## Vai tro cua Plan 08 trong toan he thong

- Plan 06 tra loi: cac entity lien ket voi nhau the nao
- Plan 07 tra loi: co the recommend baseline bang heuristic + graph signal
- Plan 09 tra loi: co the chat grounded + realtime routing
- Plan 10 tra loi: he thong demo duoc va co personalization nhe
- Plan 08 tra loi: tu data hanh vi, model hoc duoc pattern gi va dua lai gia tri learned vao recommend/chat

## Phu thuoc

Bat buoc co:

- `interaction-service` ingest event on dinh
- knowledge graph baseline chay on
- `ai-service` baseline da co recommendation endpoint
- chatbot grounded MVP da co retrieval va realtime routing
- data interaction du lon va du sach de train

## Nguon du lieu

### Tu `interaction-service`

- `search_performed`
- `product_viewed`
- `product_clicked`
- `cart_item_added`
- `cart_item_removed`
- `cart_item_quantity_updated`
- `checkout_started`
- `order_created`
- `order_paid`
- `order_completed`
- `order_cancelled`
- `chat_started`
- `chat_message_sent`

### Tu `product-service`

- product metadata
- category
- brand
- product type
- price band
- tags
- attributes

### Tu graph layer

- weighted user-product edges
- query-product relations
- product-category relations
- product-brand relations
- similar users
- similar products

## Bieu dien du lieu chuan

Khong train truc tiep tren raw logs roi dung thang trong serving. Can tao cac tang bieu dien sau:

- interaction sequence theo user hoac session
- weighted user-product matrix
- graph edges co trong so
- training dataset rieng cho tung bai toan
- evaluation split ro rang theo time hoac session

Vi du trong so interest:

`w(u,p) = alpha * clicks + beta * cart + gamma * purchases`

Trong do:

- click / view phan anh discovery
- cart phan anh intent manh hon
- purchase phan anh trust + preference cao nhat

## Bai toan cua Plan 08

### 1. Next-item prediction

Input:

- chuoi hanh vi gan day cua user/session

Output:

- top-K san pham co kha nang tuong tac tiep theo

### 2. Purchase intent prediction

Input:

- hanh vi gan day
- cart state
- query pattern

Output:

- xac suat di den `order_paid` hoac `order_completed`

### 3. User embedding learning

Output:

- vector bieu dien so thich, muc gia, category affinity, va behavioral style cua user

### 4. Product embedding learning

Output:

- vector bieu dien tinh tuong dong giua san pham tu metadata + interaction pattern

### 5. User segmentation

Muc tieu:

- nhom user theo hanh vi
- phan biet window shoppers, high-intent buyers, category-focused users, v.v.

## Model stack

### Tang baseline bat buoc

- shallow embedding / matrix factorization
- sequence baseline bang GRU hoac LSTM cho next-item prediction
- MLP hoac gradient boosting cho purchase intent

### Tang graph model

- Graph Neural Network tren heterogeneous graph
- sinh `user_embedding` va `product_embedding` tu graph neighborhood

### Tang research-level nang cao

- SPD manifold embedding
- trust propagation
- uncertainty-aware interaction representation
- affine-invariant metric de do similarity / clustering

Day la phan nghien cuu nang cao, co the la huong publishable neu duoc trien khai dung.

## Output ma model phai tao ra

Artifact can co:

- `user_embedding`
- `product_embedding`
- `next_product_scores`
- `purchase_intent_score`
- `user_segment_label`

Khong dung de artifact nam rieng trong notebook. Phai co cach export va tai lai trong `ai-service`.

## Tich hop lai vao `ai-service`

### Recommendation

Sau khi train:

- learned score duoc dung de rerank output heuristic cua Plan 07
- top-K recommendation duoc ca nhan hoa manh hon
- co the ket hop:
  - heuristic score
  - graph score
  - learned score

### Chat / RAG

Chatbot co the dung them:

- user embedding de bias retrieval
- product embedding de tim context lien quan hon
- purchase intent score de uu tien kieu tra loi va CTA phu hop
- behavioral summary de tang personalization

## Pipeline chuan

1. ingest interaction logs
2. xay training dataset
3. tao graph-derived features
4. train baseline model
5. evaluate offline
6. export model artifact
7. tai model vao `ai-service`
8. online inference / reranking

## API va job nen co

### Batch / training jobs

- `build_behavior_dataset`
- `train_next_item_model`
- `train_purchase_intent_model`
- `train_graph_embedding_model`
- `evaluate_behavior_models`
- `export_behavior_artifacts`

### Runtime API de debug / serving

- `GET /api/ai/models/status`
- `POST /api/ai/models/evaluate`
- `GET /api/ai/embeddings/user/{id}`
- `GET /api/ai/embeddings/product/{id}`
- `POST /api/ai/recommend/rerank`

Neu can cho MVP nghien cuu, training command line va artifact export la du. Khong bat buoc phai co full training API ngay tu dau.

## Metric bat buoc

### Recommendation / ranking

- Recall@K
- Precision@K
- MRR
- NDCG

### Purchase intent

- AUC
- F1
- Precision / Recall

### Embedding / retrieval

- nearest-neighbor relevance
- hit rate
- coverage

### Business-facing proxy

- cart-add lift
- purchase conversion proxy
- session depth proxy

## Deliverable

- dataset builder
- baseline next-item model
- baseline purchase intent model
- user/product embedding pipeline
- offline evaluation report
- model artifact export
- integration voi recommendation
- behavioral context feed cho chat

## Definition of Done

- co it nhat 1 baseline model train duoc end-to-end
- co metric offline ro rang
- output model duoc dung that trong `ai-service`
- recommendation co learned rerank hoac learned score
- chat co behavioral context duoc hoc tu model hoac embedding
- co artifact va report de demo

## Risk chinh

- du lieu qua it hoac qua ban
- smoke/demo data lam meo training
- event semantics chua on dinh
- label leakage
- GNN / SPD qua nang neu chua chot baseline truoc

## Thu tu trien khai noi bo de tranh no scope

### 8A. Dataset and feature export

- export session sequence
- export weighted user-product dataset
- export graph-derived features

### 8B. Baseline next-item model

- train sequence baseline
- evaluate offline
- export score artifact

### 8C. Purchase intent baseline

- train binary classifier
- expose intent score cho `ai-service`

### 8D. Learned reranking and embedding integration

- rerank recommendation bang model output
- bias retrieval bang embedding

### 8E. Advanced graph / SPD research layer

- GNN
- SPD manifold
- trust propagation

## Ghi chu quan trong

Plan 08 la full AI/ML phase. No khong thay the Plan 07, 09, 10 ma nang cap chung.

No cung khong nen duoc bat dau bang GNN hoac SPD ngay lap tuc. Cach dung la:

- baseline truoc
- graph-aware model sau
- research-level geometry cuoi cung

Neu thuc hien dung thu tu nay, Plan 08 se la cau noi tu he thong AI demo-first sang he thong AI hoc duoc tu hanh vi that.
