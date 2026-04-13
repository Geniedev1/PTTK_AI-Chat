# Plan 08: Deep Learning for Behavior Analysis

## Mục tiêu

Xây dựng lớp deep learning để phân tích hành vi user và sinh representation học được cho:

- user embedding
- product embedding
- intent signal
- next-action / next-item prediction

Đây là plan bắt buộc để đáp ứng phần “deep learning for analysing behaviors”.

## Vai trò của model này

Model không thay chatbot và cũng không thay recommendation baseline.
Model có nhiệm vụ:

- học pattern hành vi
- nén hành vi thành embedding
- tăng chất lượng recommendation
- hỗ trợ personalization
- hỗ trợ chatbot hiểu user hơn

## Dữ liệu đầu vào

### Từ interaction tracking

- chuỗi search → click → view → cart → order
- timestamp
- session_id
- query_text
- product_id
- category/brand/price context

### Từ graph

- user-product relation
- product-category relation
- product-product similarity
- query-product relation

## Hướng mô hình

### Baseline 1: Sequence model

- LSTM / GRU / Transformer-lite
- input là chuỗi hành vi theo thời gian
- mục tiêu: predict next item / next action / intent

### Baseline 2: Graph model

- GNN trên heterogeneous graph
- node: user/product/query/category
- edge: viewed/clicked/cart/purchased/searched
- output: node embedding

### Nâng cao

- trust propagation
- manifold / SPD direction nếu muốn đẩy sang research-level

## Bài toán cụ thể nên chọn

Ít nhất chọn 1 bài toán chính:

### Option A
Next product prediction

### Option B
Purchase intent prediction

### Option C
User embedding for personalized recommend

Khuyến nghị:
- MVP model: next product prediction hoặc user embedding
- dễ gắn với recommend và chat hơn

## Feature / label đề xuất

### Input features

- recent actions
- action type
- recency
- category frequency
- brand frequency
- price range preference
- query keywords hoặc query embedding

### Output

- user embedding
- product embedding
- predicted next item / intent score

## Tích hợp với hệ thống

### Với recommendation

- dùng embedding similarity để rerank
- cộng thêm model score vào baseline score

### Với personalization

- enrich `user_profile_snapshot`
- dùng predicted preference cho category/brand/price

### Với chatbot

- thêm user preference context vào prompt building
- dùng embedding hoặc intent score để bias retrieval nhẹ
- không để model tự bịa fact, chỉ hỗ trợ ranking/context

## Huấn luyện và cập nhật

### Giai đoạn đầu

- train offline theo batch
- lưu embedding định kỳ

### Giai đoạn sau

- retrain theo ngày/tuần
- có version model
- có đánh giá offline

## Evaluation tối thiểu

Tùy bài toán:

### Recommendation-oriented
- Recall@K
- HitRate@K
- MRR / NDCG nếu cần

### Intent classification
- Precision
- Recall
- F1

### Embedding usefulness
- uplift so với baseline recommend
- A/B demo hoặc offline reranking improvement

## Việc phải làm

1. Chốt bài toán ML chính.
2. Chuẩn bị dataset training từ interaction + graph.
3. Tạo feature pipeline.
4. Chọn baseline model đầu tiên.
5. Train và evaluate model.
6. Sinh `user_embedding` và `product_embedding`.
7. Lưu embedding vào AI data layer.
8. Tích hợp output model vào recommend và chat retrieval bias.

## Deliverable

- dataset training
- notebook hoặc training pipeline
- model baseline
- evaluation report
- user embedding
- product embedding
- tài liệu tích hợp model output vào system

## Definition of Done

- có ít nhất 1 model hành vi chạy được
- có metric đánh giá rõ ràng
- sinh được embedding hoặc intent score
- output model được dùng trong recommend hoặc chat
- phân biệt rõ model học pattern với chatbot dùng fact retrieval

## Phụ thuộc

Phụ thuộc `05-interaction-tracking.md`, `06-knowledge-graph.md`, `07-ai-data-and-recommendation.md`.