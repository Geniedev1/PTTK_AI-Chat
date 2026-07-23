# Plan 14: Cart Abandonment Prediction & Behavioral AI Roadmap (New-System Template)

## Trạng thái

Tài liệu tham khảo (reference template) — mô tả thứ tự triển khai AI/Behavioral khuyến nghị khi
xây một hệ thống **mới từ đầu**, cùng với thiết kế chi tiết cho tính năng được chọn làm flagship:
**Cart Abandonment Prediction + Proactive Intervention**.

Khác với các plan 01-13 (roadmap thực thi cho chính repo này), plan này đóng vai trò tài liệu
nguyên tắc/thứ tự ưu tiên có thể tái sử dụng cho một hệ thống e-commerce mới, đồng thời chốt lại
lựa chọn tính năng ML đầu tiên nên làm dựa trên hạ tầng Behavioral đã có.

## Vì sao chọn Cart Abandonment Prediction làm tính năng ML đầu tiên

So với các ý tưởng khác (wiring lại sequence model có sẵn, customer segmentation, explainable
recommendation, admin dashboard, proactive nudge độc lập):

- Có **nhãn tự nhiên miễn phí**: logic "có `cart_item_added` nhưng không có `order_paid`/
  `order_completed`" đã tồn tại sẵn dưới dạng endpoint phân tích (`abandoned_carts`), không cần
  gán nhãn thủ công.
- Tận dụng đúng feature đã có từ behavioral profile (`cart_intensity`, `purchase_intensity`,
  `purchase_intent_score`, `funnel_stage`) — không cần xây feature pipeline mới từ đầu.
- Có vòng đời ML đầy đủ: feature engineering -> label -> train -> serve -> hành động, khác với
  các ý tưởng thuần BI (dashboard) hoặc thuần kỹ thuật (wiring model có sẵn).
- Business value rõ ràng, dễ demo: dự đoán -> chatbot/chủ động can thiệp (nhắn hỏi, gợi ý giảm giá).

## Roadmap tổng thể cho hệ thống mới (Phase 0 -> Phase 10)

### Phase 0 — Kiến trúc nền tảng

- Không cần tách nhiều microservice ngay từ đầu. Bắt đầu với 1 core service (nghiệp vụ chính) +
  1 tracking service riêng (event/behavioral), vì đây là ranh giới hay đổi và cần scale độc lập.
- Chọn Postgres cho core + tracking (chưa cần graph DB vội).
- Chốt event schema chuẩn ngay từ đầu, tránh đổi sau: `event_id, event_type, user_id, session_id,
  product_id, query_text, signal_weight, metadata(json), timestamp, source`.
- **DoD:** 2 service chạy được, gọi nhau qua REST, schema event đã review.

### Phase 1 — Event Tracking Infrastructure

- Định nghĩa danh mục event + bảng trọng số tín hiệu (signal weight), review kỹ vì đây là input
  cho mọi thứ sau.
- `POST /events` nhận và lưu event, non-blocking (timeout ngắn ~0.5s, lỗi thì log warning chứ
  không chặn request nghiệp vụ chính).
- Helper `emit_event()` dùng chung cho mọi module nghiệp vụ.
- Rủi ro cần né: mất event khi tracking service down — cân nhắc queue (Redis Streams/RabbitMQ)
  nếu có thời gian; nếu không, HTTP fire-and-forget vẫn chấp nhận được ở quy mô đồ án.
- **DoD:** query lại được toàn bộ event của 1 user/session; có thống kê event_type count theo ngày.

### Phase 2 — Behavioral Profile (Feature Aggregation)

- Hàm tổng hợp: N event gần nhất -> profile snapshot (top category/brand, price band, funnel_stage,
  purchase_intent_score).
- Cache profile theo session/user (Redis, TTL ngắn) để tránh tính lại mỗi request.
- Expose `GET /profile/snapshot?user_id=|session_id=`.
- **DoD:** endpoint trả profile hợp lý trong <200ms; có test với dữ liệu giả lập đủ nhiều event.

### Phase 3 — Recommendation heuristic (chưa cần ML)

- Rule-based: popularity + cùng category/brand + price band tương đồng, bias theo profile.
- Đây là AI-feature đầu tiên user thấy được, không cần model, không cần dữ liệu lớn.
- **DoD:** so sánh tỉ lệ click giả lập giữa "random" vs "heuristic recommend", chứng minh cải thiện.

### Phase 4 — Analytics/BI dashboard (song song Phase 3)

- Bài học rút ra: các API phân tích rất dễ bị build xong rồi bỏ quên vì không ai nối UI. Lần này
  bắt buộc có dashboard thật ngay từ đầu, không chỉ có API.
- Tối thiểu: `data_quality`, `top_queries`, `product_gaps`, `abandoned_carts`, `category_interest`.
- Lợi ích kép: vừa là công cụ vận hành, vừa sinh sẵn nhãn cho Phase 6.
- **DoD:** admin xem được dashboard thật, không phải chỉ gọi qua Postman.

### Phase 5 — Knowledge Graph (chỉ khi đủ dữ liệu)

- Ngưỡng bắt đầu: ít nhất vài nghìn event, vài trăm session — trước đó graph rỗng, không đáng làm.
- Neo4j, đồng bộ catalog (Product/Category/Brand) + interaction (weighted edges).
- Query cần có: similar products, similar users, query -> product path.
- **DoD:** Cypher trả kết quả đúng nghĩa (không rỗng, không trùng lặp vô nghĩa).

### Phase 6 — Cart Abandonment Prediction (flagship ML)

Model ML đầu tiên thật sự của hệ thống.

**Dataset:**

| Feature | Nguồn |
|---|---|
| cart_intensity, purchase_intensity, purchase_intent_score, funnel_stage | Behavioral profile (Phase 2) |
| item_count, total_quantity, subtotal_amount | Giỏ hàng hiện tại |
| Thời gian từ lúc thêm giỏ đến hiện tại | Tính từ timestamp event |
| Số lần quay lại xem giỏ | Đếm event `cart_viewed` |

**Label:** session có `cart_item_added` nhưng không có `order_paid`/`order_completed` trong cửa sổ
quan sát (ví dụ 30-60 phút) -> 1 (abandon), ngược lại -> 0.

**Model:** logistic regression hoặc MLP nhỏ (numpy hoặc scikit-learn đều được cho đồ án) — bắt
buộc so sánh với baseline "luôn dự đoán 0".

**Evaluation:** Precision/Recall/F1 cho lớp abandon (không dùng accuracy vì lệch lớp), AUC-ROC.

**Serving:** `GET /predict/cart-abandonment?session_id=`, tính feature realtime từ Phase 2 rồi
chấm điểm.

**DoD:** AUC rõ ràng tốt hơn baseline; có báo cáo confusion matrix.

**Rủi ro cần lưu ý:**

- Dữ liệu có thể lệch lớp nặng (đa số session không mua nhưng chưa chắc có ý định mua) — cần định
  nghĩa rõ observation window.
- Cold-start: session mới chưa đủ event thì feature nghèo — cần fallback (empty-profile).

### Phase 7 — Can thiệp chủ động (Proactive Intervention)

- Job định kỳ (hoặc trigger theo event) check prediction, nếu vượt ngưỡng và chưa từng can thiệp
  trong session này -> gửi hành động (chat nudge / banner giảm giá / flag cho frontend).
- Cơ chế chống spam: đánh dấu đã can thiệp, không lặp lại trong cùng session.
- **DoD:** demo được kịch bản: thêm giỏ -> không thanh toán -> sau X phút hệ thống chủ động nhắn.

### Phase 8 — Chatbot RAG (có thể làm song song từ Phase 6 nếu chia người)

- Knowledge base từ policy docs + catalog, retrieval (embedding hoặc lexical fallback), generation
  qua LLM, bias bằng behavioral profile (Phase 2).
- **DoD:** trả lời đúng câu hỏi FAQ + câu hỏi realtime (trạng thái đơn) qua gọi API core.

### Phase 9 — Model nâng cao (tuỳ chọn, điểm cộng)

- Sequence model (LSTM/GRU nhỏ) dự đoán sản phẩm tiếp theo, so sánh ablation với heuristic — chỉ
  làm nếu Phase 6 đã ổn và còn thời gian.

### Phase 10 — Vận hành & đo lường (liên tục)

- Theo dõi model drift (phân phối feature thay đổi theo thời gian), retrain định kỳ.
- Đo tác động thực (conversion uplift của Phase 7 so với nhóm không can thiệp — A/B test đơn giản).

## Bảng ưu tiên nếu thiếu thời gian

| Bắt buộc (core đồ án) | Nên có (điểm cộng) | Có thể bỏ nếu gấp |
|---|---|---|
| Phase 1, 2, 3, 6 | Phase 4, 7, 8 | Phase 5 (graph), Phase 9 |

## Phụ thuộc

Kế thừa nguyên lý từ [05-interaction-tracking.md](./05-interaction-tracking.md),
[06-knowledge-graph.md](./06-knowledge-graph.md), [08-behavior-modeling.md](./08-behavior-modeling.md)
và [11-deep-model-mvp.md](./11-deep-model-mvp.md) của repo hiện tại, tổng hợp lại thành thứ tự
triển khai khuyến nghị cho một hệ thống mới bắt đầu từ con số 0.
