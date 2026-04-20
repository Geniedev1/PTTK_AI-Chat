# Defense Summary (Plan 08)

### 1. Bài toán là gì?
Xây dựng một hệ thống phân tích hành vi người dùng, đánh giá sở thích ngầm, từ đó cung cấp các gợi ý sản phẩm (Recommendation) và tư vấn thông minh (RAG AI Chat) được xây dựng trên Kiến thức Đồ thị (Knowledge Graph) và Mô hình Chuỗi học Sâu (Sequence Deep Learning). Quy mô yêu cầu 500 người dùng với 8 chuẩn hành vi khác nhau.

### 2. Đã làm gì?
- Phát triển module sinh dữ liệu tự động cho `500 user` gồm 8 luồng hành vi thương mại điện tử thật (add to cart, view, click, cancel, purchase, search...).
- Triển khai thuật toán xử lý dữ liệu sequence bằng cửa sổ trượt (sliding window) tạo tập training data. 
- Xây dựng mạng nơ-ron thuần túy (từ ma trận cơ bản) để huấn luyện 3 kiến trúc Deep Learning Sequence: **RNN**, **LSTM**, và **BiLSTM**.
- Đồng bộ hóa sự kiện vào hệ thống **Neo4j Graph Database** theo dạng luồng (real-time). Nodes gồm User, Product, Category, Query.
- Tích hợp pipeline **RAG** vào tính năng Chat, nơi Graph làm Context nền tảng kết hợp LLM để trả lời tương tác tự nhiên.
- Show kết quả trên Frontend thương mại điện tử chuyên dụng.

### 3. Model nào tốt nhất?
Theo báo cáo Metric, **RNN** là thuật toán được lựa chọn cuối cùng (`model_best`).  
Mặc dù LSTM và BiLSTM có năng lực học chuỗi phức tạp hơn, nhưng đối với chuỗi ngắn của e-commerce (chủ yếu là 4-5 bước hành vi), RNN đã tối ưu xuất sắc với metric **Validation F1 cao nhất (~0.93)**. Mô hình này ít bị Overfitting hơn ở quy mô mẫu thử hiện tại.

### 4. Graph dùng để làm gì?
Knowledge Graph đảm nhiệm 3 vai trò lõi mà Relation Database thông thường gặp khó:
1. **Tìm kiếm ngầm (Implicit Preferences)**: Quét nhanh chóng hạng mục và sở thích ẩn của người dùng thông qua cụm Nodes tương tác nhiều nhánh.
2. **Khám phá hàng xóm (Product Neighbors / Similarity)**: Gộp nhóm tự động những người đã truy cập món này thường xem món nào khác thay vì tính toán Cartesian cực nặng. Quá trình này giúp đưa ra hệ thống "Sản phẩm tương tự" chính xác.
3. **Phân cụm User**: Xác định Similar Users để gợi ý chéo.

### 5. Chat dựa trên Graph hoạt động ra sao?
Luồng kiến trúc RAG Chat tích hợp Graph:
1. NLP Model bóc tách Intent của người dùng (Hỏi hàng, hỏi sở thích, hỏi tương tự).
2. Nếu là tìm theo sở thích/sản phẩm tương tự: Pipeline bắn API xuống Knowledge Graph (Neo4j). Graph phân tích đường đi của Actor Node (User) để lấy list các Cụm Product Nodes.
3. Graph trả về Text Summary (Context) đẩy vào LLM Prompt.
4. LLM đọc Context này và dùng giọng văn khéo léo để phản hồi User. Flag `used_graph_context` bật xanh. Nếu câu hỏi là về "Kho/Giá tiền", pipeline tự chuyển hướng sang gọi Real-time API thay vì cache trong Graph.
