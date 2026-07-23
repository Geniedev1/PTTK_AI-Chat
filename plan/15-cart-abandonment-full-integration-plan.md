# Plan 15: Tích hợp đầy đủ Cart Abandonment Prediction vào hệ thống mới (Idea -> Data -> Train -> Serve)

## Trạng thái

Kế hoạch tích hợp end-to-end cho một **hệ thống mới** (không phải bản vá cho repo hiện tại) — hợp
nhất phần ý tưởng đã chọn, chiến lược dữ liệu cho bài toán cold-start, pipeline huấn luyện, và cách
đưa model vào runtime + hành động chủ động. Đây là bản đầy đủ, thay thế/đóng vai trò chi tiết hoá
cho phần Phase 6-7 đã phác thảo ở [14-cart-abandonment-behavioral-roadmap.md](./14-cart-abandonment-behavioral-roadmap.md).

---

## 1. Ý tưởng & bài toán

**Vấn đề:** user thêm sản phẩm vào giỏ hàng nhưng không hoàn tất thanh toán -> mất doanh thu tiềm
năng, và hệ thống không biết để can thiệp kịp thời.

**Mục tiêu AI:** dự đoán sớm xác suất một phiên (session) sẽ bỏ giỏ hàng, dựa trên hành vi
(behavioral signal) trong chính phiên đó, để kích hoạt can thiệp trước khi user rời đi.

**Vì sao chọn bài toán này làm tính năng AI đầu tiên triển khai thật (so với các ý tưởng khác đã
cân nhắc — segmentation, explainable recommendation, wiring sequence model có sẵn, dashboard
thuần BI):**

- Nhãn (label) suy ra trực tiếp từ business logic có sẵn (giỏ hàng có thêm nhưng không thanh toán),
  không cần gán tay.
- Feature tái dùng từ behavioral profile đã có trong roadmap (Phase 2), không cần pipeline feature
  riêng.
- Có đầy đủ vòng đời ML: feature -> label -> train -> serve -> hành động, thay vì dừng ở phân tích.
- Giá trị kinh doanh rõ ràng, dễ đo lường, dễ demo trực quan.

---

## 2. Kiến trúc tổng thể

```
[User hành động] -> [Core service (cart/order)] -> emit event
                                                        |
                                                        v
                                        [Tracking/Interaction service] -- luu InteractionEvent
                                                        |
                                                        v
                                   [Behavioral Profile module] -- tong hop + cache (Redis)
                                                        |
                                   +--------------------+---------------------+
                                   |                                          |
                                   v                                          v
                     [AI service - Cart Abandonment Model]      [AI service - Recommend/Chat]
                                   |
                                   v
                     [Intervention Worker] -- kiem tra nguong, chong spam
                                   |
                                   v
                     [Kenh hanh dong: chat nudge / banner giam gia / email]
```

Thành phần mới cần xây so với baseline (Phase 0-3 của Plan 14): **AI service module riêng cho
cart-abandonment** (dataset builder + training script + inference endpoint) và **Intervention
Worker** (job định kỳ hoặc event-driven).

---

## 3. Chiến lược dữ liệu (trọng tâm — vì đây là hệ thống MỚI, chưa có lịch sử)

### 3.1 Vấn đề cold-start

Hệ thống mới chưa có traffic thật -> chưa đủ dữ liệu để train ML ngay từ ngày đầu. Không có nguồn
dữ liệu nào là "chuẩn tuyệt đối" — cần phối hợp nhiều nguồn theo từng giai đoạn thời gian.

### 3.2 Nguồn dữ liệu theo giai đoạn, xếp theo độ ưu tiên

| Giai đoạn | Nguồn | Vai trò |
|---|---|---|
| Ngày 1 | Event tracking bật ngay (organic) | Nguồn thật duy nhất khớp 100% với hệ thống; cần thời gian tích lũy |
| Ngày 1 -> tuần vài | Rule-based heuristic (threshold trên `cart_intensity`) | Chạy được ngay không cần data; đồng thời sinh **pseudo-label** để bootstrap model đầu tiên |
| Song song | Public dataset cùng ngành (Instacart, RetailRocket, Olist, UCI Online Retail...) | Tham khảo phân phối chung của ngành (tỉ lệ bỏ giỏ hàng trung bình, thời gian quyết định mua) để hiệu chỉnh ngưỡng ban đầu — **không** dùng trực tiếp product_id/category của họ |
| Nếu cần rút ngắn thời gian chờ | Soft-launch/pilot với nhóm user thật giới hạn | Có data thật sớm hơn launch chính thức |
| Chỉ khi thực sự cần, có kiểm soát | Synthetic có chủ đích, dựa trên phân phối thực tế đã biết (không phải random thuần) | Bổ sung volume tạm thời cho giai đoạn train thử nghiệm |

### 3.3 Cảnh báo bắt buộc: tránh "circular synthetic trap"

Nếu sinh dữ liệu giả bằng xác suất **tự đặt ra tuỳ ý** (vd "60% user sẽ thêm giỏ, 25% sẽ checkout"),
model train trên dữ liệu đó chỉ đang **học lại chính công thức đã tạo ra nó**, không học được pattern
hành vi thật. Khi đưa vào hệ thống thật, model sẽ không generalize được. Quy tắc: synthetic chỉ dùng
để test pipeline (chạy được code, không lỗi), **không** dùng làm cơ sở đánh giá chất lượng model
cuối cùng. Model production phải luôn được đánh giá lại trên dữ liệu thật khi đã có.

### 3.4 Đảm bảo dữ liệu "phù hợp" (fit) đúng hệ thống cần áp dụng

- **Label phải định nghĩa theo đúng business logic của chính hệ thống** — ví dụ window quan sát
  "bỏ giỏ hàng" cần khớp chu kỳ mua thực tế của ngành hàng (hàng tiêu dùng nhanh: 30-60 phút; hàng
  giá trị cao: có thể vài ngày).
- **Feature phải phản ánh domain thật** của hệ thống (khoảng giá, danh mục, hành vi đặc thù) — nếu
  tham khảo public dataset thì chỉ giữ lại "hình dạng phân phối"/insight định tính, không map thẳng
  category/product.
- **Theo dõi data drift liên tục**: so sánh phân phối feature giữa tập train và dữ liệu thực tế
  production theo chu kỳ (vd hàng tuần); lệch nhiều thì phải train lại.
- **Luôn có baseline heuristic để đối chiếu** — model ML mới chỉ được chấp nhận nếu chứng minh vượt
  baseline trên dữ liệu thật, không chỉ trên tập test nội bộ.

---

## 4. Feature & Label Engineering

**Label:** session có event `cart_item_added` nhưng không có `order_paid`/`order_completed` trong
cửa sổ quan sát W (mặc định 45 phút, cần hiệu chỉnh theo ngành hàng thực tế) -> `1` (abandon);
ngược lại -> `0`.

**Feature (lấy từ Behavioral Profile module, Phase 2 của Plan 14):**

| Feature | Ý nghĩa |
|---|---|
| `cart_intensity` | Mức độ tương tác với giỏ hàng |
| `purchase_intensity` | Mức độ tiến gần tới mua hàng |
| `purchase_intent_score` | Điểm ý định mua tổng hợp |
| `funnel_stage` | browser / interested / high-intent / buyer |
| `item_count`, `total_quantity`, `subtotal_amount` | Trạng thái giỏ hàng hiện tại |
| `time_since_last_cart_action` | Thời gian từ hành động giỏ hàng gần nhất |
| `cart_view_return_count` | Số lần quay lại xem giỏ hàng |

**Tách tập dữ liệu:** train/valid/test theo session, tránh rò rỉ (leakage) giữa các session của cùng
một user nếu có thể xảy ra chồng lấn thời gian.

---

## 5. Training Pipeline

- **Baseline bắt buộc:** luôn dự đoán lớp đa số (0 = không bỏ giỏ) — mọi model phải vượt baseline này.
- **Model khởi điểm:** Logistic Regression hoặc MLP nhỏ (tái dùng kiến trúc `NumpyMLPBinaryClassifier`
  nếu muốn nhất quán với phần recommend).
- **Đánh giá:** Precision/Recall/F1 cho lớp abandon (không dùng accuracy do lệch lớp), AUC-ROC,
  confusion matrix.
- **Chu kỳ retrain:** định kỳ (vd hàng tuần) khi dữ liệu thật đã đủ lớn, kèm theo dõi data drift
  (mục 3.4).
- **Ghi log protocol dataset** (số lượng record, khung thời gian, tỉ lệ lớp) mỗi lần train — tránh
  lặp lại lỗi "train trên tập quá nhỏ mà không ai biết" đã từng gặp ở model deep-ranking hiện tại.

---

## 6. Serving & Integration

- Endpoint: `GET /predict/cart-abandonment?session_id=...`
- Luồng: nhận request -> gọi Behavioral Profile module lấy feature realtime -> chấm điểm bằng model
  đã load sẵn trong bộ nhớ -> trả về xác suất.
- Ngân sách độ trễ: nên dưới 200ms (tương tự yêu cầu của endpoint profile snapshot), vì đây là
  đường gọi có thể nằm trên luồng UI trực tiếp (vd hiển thị banner ngay khi vào trang giỏ hàng).
- Model artifact versioning: lưu kèm ngày train, số lượng dữ liệu, để dễ rollback nếu bản mới kém hơn.

---

## 7. Proactive Intervention Layer

- Job định kỳ (hoặc event-driven ngay khi có event `cart_item_added`) gọi endpoint dự đoán.
- Nếu xác suất vượt ngưỡng cấu hình được **và** session chưa từng được can thiệp -> kích hoạt một
  trong các hành động: chat nudge chủ động, banner giảm giá, email nhắc nhở (nếu có định danh email).
- Cơ chế chống spam: đánh dấu session đã can thiệp, không lặp lại; giới hạn tần suất can thiệp trên
  mỗi user trong một khoảng thời gian.

---

## 8. Lộ trình triển khai (gắn với Plan 14)

| Tuần | Việc chính |
|---|---|
| 1-2 | Event tracking + Behavioral Profile (Phase 1-2 của Plan 14) |
| 3 | Heuristic threshold tạm thời cho cart-abandonment (chưa cần ML), bắt đầu sinh pseudo-label |
| 4-5 | Thu thập dữ liệu thật (organic) song song soft-launch nếu có |
| 6 | Xây dataset builder + train model đầu tiên, so sánh với baseline heuristic |
| 7 | Serving endpoint + tích hợp Intervention Worker |
| 8 | Đo lường tác động thật (A/B: có can thiệp vs không), tinh chỉnh ngưỡng |
| Liên tục | Theo dõi data drift, retrain định kỳ |

---

## 9. Success Metrics / Definition of Done

- **Model metric:** AUC-ROC vượt rõ ràng baseline "luôn dự đoán 0" trên tập test dữ liệu thật.
- **Business metric:** tỉ lệ hoàn tất thanh toán ở nhóm được can thiệp cao hơn nhóm không can thiệp
  (đo qua A/B test).
- **Operational metric:** endpoint dự đoán phản hồi dưới ngân sách độ trễ đã đặt; tần suất can thiệp
  không vượt ngưỡng gây khó chịu cho user (theo dõi tỉ lệ user tắt/bỏ qua thông báo).
- Plan này được xem là hoàn thành khi cả 3 nhóm metric trên có số liệu thật để báo cáo, không chỉ
  dừng ở số liệu offline trên dữ liệu tự sinh.

---

## 10. Rủi ro & giảm thiểu

| Rủi ro | Giảm thiểu |
|---|---|
| Không đủ dữ liệu thật khi cần demo/bảo vệ đồ án | Dùng heuristic + soft-launch để có số liệu thật tối thiểu; nêu rõ giới hạn dữ liệu trong báo cáo thay vì che giấu |
| Synthetic data tạo ảo giác về chất lượng model | Luôn đối chiếu với baseline, không dùng synthetic làm căn cứ đánh giá cuối cùng |
| Can thiệp gây phiền (spam) | Giới hạn tần suất, có cơ chế đánh dấu đã can thiệp |
| Lệch lớp (class imbalance) khiến accuracy gây hiểu lầm | Dùng Precision/Recall/F1/AUC, không dùng accuracy |
| Model cũ không còn phù hợp khi hành vi user thay đổi | Theo dõi data drift, retrain định kỳ |

---

## Phụ thuộc

Kế thừa và chi tiết hoá Phase 2, 6, 7 của [14-cart-abandonment-behavioral-roadmap.md](./14-cart-abandonment-behavioral-roadmap.md),
đồng thời tham chiếu nguyên tắc dataset/label protocol từ [11a-dataset-label-protocol.md](./11a-dataset-label-protocol.md)
của repo hiện tại làm ví dụ đối chiếu.
