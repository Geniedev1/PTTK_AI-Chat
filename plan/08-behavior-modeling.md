# Plan 08: Behavioral Profile for Chat and Recommendation

## Trang thai

Reduced scope and refocused around core AI behavior loop.

## Muc tieu

Xay lop AI cot loi cua he thong theo dung flow:

`theo doi hanh vi -> tong hop behavioral profile -> dung profile cho recommend va chat`

Plan nay khong dat trong tam vao research model. Trong tam la bien interaction data thanh behavioral profile co the dung that trong runtime.

## Yeu cau cot loi ma plan nay phai dap ung

He thong phai theo doi duoc cac hanh vi nhu:

- view
- click
- add to cart
- update cart
- checkout
- purchase
- search
- chat message

Tu cac hanh vi do, he thong phai sinh ra duoc:

- recommendation ca nhan hoa hon
- chat co hieu biet ve muc do quan tam va ngu canh hanh vi cua user/session

Neu chua dung duoc behavioral profile cho ca `recommend` va `chat` thi Plan 08 chua xong.

## Scope da rut gon

### Bat buoc

- tong hop behavioral events thanh `behavioral profile`
- ho tro ca `user_id` va `session_id`
- dung behavioral profile trong recommendation
- dung behavioral profile trong chat
- co baseline scoring hoac intent signal nhe neu can
- co test va debug endpoint toi thieu

### Khong lam trong plan nay

- khong lam GNN
- khong lam SPD manifold
- khong lam graph neural embedding research
- khong lam multi-model stack
- khong lam heavy training pipeline
- khong lam full MLOps hay model registry

## Vai tro cua Plan 08 trong he thong

Plan 05 va 06 da tao behavioral events va graph baseline.

Plan 07 da co recommendation baseline.

Plan 09 da co chat grounded baseline.

Plan 08 phai la cau noi giua nhung phan do:

- lay behavioral data tu `interaction-service`
- rut ra behavioral profile co nghia
- dua profile vao `ai-service`
- cung mot profile do phuc vu ca recommend va chat

## Dau vao co san tu repo

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
- `chat_started`
- `chat_message_sent`

### Tu `product-service`

- `product_id`
- `category_id`
- `brand_id`
- `product_type_id`
- `base_price`
- `tags`
- `attributes`
- `is_active`

### Tu graph baseline

- `user_interest`
- `product_neighbors`
- `similar_users`
- `query_paths`

## Behavioral profile la artifact trung tam

Plan nay khong lay embedding hay model file lam artifact trung tam.

Artifact trung tam la:

- `behavioral_profile`

Moi `behavioral_profile` duoc tao theo:

- `user_id` neu da dinh danh user
hoac
- `session_id` neu user anonymous

## Cau truc behavioral profile toi thieu

Behavioral profile can co cac nhom thong tin sau:

### Identity scope

- `user_id`
- `session_id`
- `scope_type`

### Recent activity

- recent viewed products
- recent clicked products
- recent carted products
- recent purchased products
- recent searched queries
- recent chat intents hoac message cues

### Preference summary

- top categories
- top brands
- top price bands
- strong product interests
- graph interest summary

### Funnel / intent summary

- cart intensity
- purchase intensity
- checkout activity
- purchase intent score nhe
- stage gan dung trong funnel: browser / interested / high-intent / buyer

## Bai toan duoc chot cho Plan 08

Plan nay chi chot 2 bai toan runtime:

### 1. Behavioral recommendation

Recommendation phai dung behavioral profile de:

- tang diem item match top category
- tang diem item match top brand
- tang diem item phu hop price band
- uu tien graph neighbors lien quan toi lich su hanh vi
- uu tien item gan voi recent viewed/carted/purchased context

### 2. Behavioral chat personalization

Chat phai dung behavioral profile de:

- biet user/session dang quan tam nhom san pham nao
- uu tien retrieval lien quan toi recent interest
- dieu chinh answer framing dua tren purchase intent nhe
- tranh tra loi chung chung khi da co behavioral context ro rang

Chat van phai grounded. Behavioral profile chi bias retrieval va response framing, khong duoc lam sai fact.

## Cach lam implementation-first

Khong bat dau bang model nang. Bat dau bang 3 tang:

### 8A. Behavioral profile builder

Tao command hoac service:

- `build_behavior_profile`

No phai tong hop data tu event log + catalog + graph summary thanh profile dung duoc cho runtime.

Co the build:

- on-demand theo request
hoac
- precompute nhe theo user/session

Ban dau co the uu tien on-demand + cache nhe.

### 8B. Baseline scoring / intent layer

Chi them mot lop nhe, de profile co gia tri hon:

- weighted affinity score
- purchase intent score nhe

Khuyen nghi baseline:

- rule-based weighted score
hoac
- logistic regression / gradient boosting nhe

Neu du lieu chua du sach de train, van duoc phep bat dau bang weighted behavioral score truoc.

### 8C. Runtime integration trong `ai-service`

Phai tich hop behavioral profile vao:

- recommendation endpoints
- chat retrieval / chat response context

Khong de behavioral profile dung rieng cho recommendation roi bo chat o muc optional.

## Viec phai lam

1. Chot schema cho `behavioral_profile`.
2. Viet profile builder tu `interaction-service` + `product-service` + graph summary.
3. Them helper de lay profile theo `user_id` hoac `session_id`.
4. Tich hop profile vao recommendation scoring.
5. Tich hop profile vao chat retrieval bias va context.
6. Neu kha thi, them `purchase_intent_score` nhe.
7. Viet test cho profile builder va runtime integration.

## API toi thieu

Phai co cac API debug/runtime sau:

- `GET /api/ai/profile/snapshot`
- `GET /api/ai/models/status`

Co the de recommendation dung profile noi bo trong endpoint hien co, khong bat buoc tao endpoint moi.

Khong bat buoc:

- training API
- embedding API rieng
- evaluation API rieng

## Deliverable

- behavioral profile schema
- profile builder
- profile snapshot endpoint
- recommendation co dung behavioral profile
- chat co dung behavioral profile
- purchase intent score nhe neu kip
- test va demo flow

## Definition of Done

- system track duoc cac hanh vi chinh: view, click, add cart, purchase, search, chat
- build duoc behavioral profile cho `user_id` hoac `session_id`
- recommendation output thay doi theo profile
- chat retrieval hoac context thay doi theo profile
- profile duoc dung that trong runtime, khong chi dung de report
- co it nhat 1 debug endpoint de xem profile dang duoc dung

## Risk chinh

- du lieu demo qua it de profile that su co y nghia
- event semantics chua on dinh giua view/click/cart/purchase
- session anonymous bi dut doan
- neu nhung purchase intent score qua som, de overfit vao smoke data

## Thu tu thuc hien de tranh no scope

1. Behavioral profile schema
2. Profile builder
3. `GET /api/ai/profile/snapshot`
4. Recommendation integration
5. Chat integration
6. Sau cung moi can nhac them purchase intent score nhe

## Phan de sau

Nhung muc sau de sau Plan 08 nay:

- learned user embedding
- learned product embedding
- deep sequence model
- GNN
- SPD manifold
- trust propagation
- advanced segmentation research

Neu behavioral profile runtime da chay on va tao gia tri ro rang cho recommend/chat, khi do moi nen tach mot phase AI/ML research nang hon.
