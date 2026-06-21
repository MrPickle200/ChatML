# Báo cáo Dự án ChatML — Báo cáo Tiến độ & Kết quả Benchmark 

- **Thời gian cập nhật:** 20/06/2026
- **Người thực hiện:** Antigravity AI
- **Dự án:** ChatML (Document Ingestion & RAG Retrieval Service)

---

## Phần 1: Cập nhật Tiến độ Phát triển (Từ Thứ Hai đến Hôm Nay)

Trong tuần qua, dự án ChatML đã trải qua những cải tiến lớn về cả giao diện người dùng (Frontend), quản lý phiên hội thoại (Database) và tối ưu hóa truy vấn RAG (Core Backend), kết thúc bằng việc tích hợp hệ thống đánh giá hiệu năng (Benchmark).

### Tóm tắt Lộ trình Phát triển Tuần qua (15/06 - 20/06)

*   **15/06 - 16/06:** Phát triển Giao diện Chat UI ban đầu và thiết kế Schema lưu trữ trong MongoDB.
*   **17/06:** Xây dựng thanh bên (Sidebar) hiển thị danh sách và quản lý các cuộc hội thoại.
*   **18/06:** Triển khai `ContextBuilderService` để tổng hợp lịch sử chat làm ngữ cảnh cho LLM.
*   **19/06:** Tích hợp tính năng Rewrite Query để tạo câu hỏi độc lập (Standalone Question) từ ngữ cảnh.
*   **20/06:** Hoàn thiện Framework chấm điểm Benchmark, đo lường độ trễ (Latency) và phân tích các chỉ số đánh giá.

---

## Phần 2: Kết quả Đánh giá Hiệu năng (Benchmark Results)

Hệ thống đánh giá benchmark toàn diện đã được triển khai trên tập dữ liệu gồm **100 câu hỏi** đã qua sàng lọc thủ công . Kết quả chi tiết của từng thành phần RAG như sau:

### 1. Phân tích Luồng Dữ liệu & Độ trễ (RAG Latency Pipeline)

Dưới đây là tóm tắt quy trình xử lý và thời gian phản hồi của từng thành phần trong pipeline RAG, được đo lường thực tế trên **30 câu hỏi đại diện**:

1.  **Tiếp nhận yêu cầu:** Người dùng gửi câu hỏi qua API `POST /chat/chat`.
2.  **Rewrite câu hỏi:** `ChatService` gọi LLM để viết lại câu hỏi dựa vào lịch sử chat để tạo câu hỏi độc lập (Standalone Question).
3.  **Truy xuất (Retrieval):** Nhúng câu hỏi thông qua `EmbeddingService` thành vector 384 chiều, tìm kiếm top 5 chunks văn bản liên quan nhất trên Qdrant DB (Thời gian xử lý trung bình: ~108ms).
4.  **Tạo ngữ cảnh (Context Building):** Lấy lịch sử 10 câu chat gần nhất từ MongoDB (Thời gian xử lý trung bình: ~0.02ms).
5.  **Tạo câu trả lời & Tiêu đề:** Gọi LLM tạo câu trả lời chi tiết và sinh tiêu đề cuộc hội thoại ngắn gọn (Thời gian xử lý LLM trung bình: ~11.01s).
6.  **Lưu trữ & Phản hồi:** Lưu cuộc hội thoại mới vào MongoDB và trả về phản hồi cuối cùng (Độ trễ toàn trình E2E trung bình: ~11.13s).

### 2. Bảng chỉ số đo lường chi tiết (Benchmark Metrics)

Dưới đây là các chỉ số chi tiết được ghi nhận từ hệ thống đánh giá:

| Nhóm Đánh Giá | Chỉ số (Metric) | Giá trị ghi nhận | Ý nghĩa & Phân tích |
| :--- | :--- | :--- | :--- |
| **Truy xuất dữ liệu (Retrieval)** | **Recall@5** | **88.00%** | Tỷ lệ tìm thấy các chunks tài liệu thực tế chứa câu trả lời đúng nằm trong Top 5 kết quả tìm kiếm. |
| | **Hit Rate@5** | **88.00%** | Xác suất tìm thấy ít nhất 1 chunk tài liệu liên quan trong Top 5. |
| | **MRR (Mean Reciprocal Rank)** | **0.7715** | Điểm số thứ hạng của chunk liên quan (càng gần 1 thì chunk đúng càng nằm ở vị trí đầu tiên). |
| **Nội dung câu trả lời (Generation)** | **Average Correctness** | **4.16 / 5.0** | Điểm đánh giá chất lượng câu trả lời bằng LLM-as-Judge (4 = Hầu hết chính xác, 5 = Hoàn toàn chính xác). |
| | **Score Distribution** | 1: **2** \| 2: **2** \| 3: **3** \| 4: **64** \| 5: **29** | Phân phối điểm số độ chính xác (phần lớn tập trung ở điểm 4 và 5). |
| **Độ trung thực (Faithfulness)** | **Average Faithfulness** | **4.18 / 5.0** | Mức độ trung thực của câu trả lời so với ngữ cảnh (không tự ý bịa đặt thông tin). |
| | **Hallucination Rate** | **7.00%** | Tỷ lệ xảy ra hiện tượng ảo giác (câu trả lời có chứa thông tin không có trong tài liệu). |
| **Độ trễ hệ thống (Latency)** | **E2E Mean (Trung bình)** | **11.13s** | Thời gian phản hồi trung bình của người dùng cho một câu hỏi. |
| | **E2E Median (Trung vị)** | **11.62s** | Thời gian phản hồi trung vị. |
| | **E2E P95** | **21.99s** | Độ trễ ở phân vị 95 (bị ảnh hưởng lớn bởi giới hạn API Rate Limit của Groq và thời gian chờ retry). |

### 3. Phân bổ Thời gian Xử lý Chi tiết (Latency Breakdown)

*   **Tìm kiếm tương đồng (Retrieval):** 0.108 giây (chiếm ~1.0%)
*   **Xây dựng ngữ cảnh (Context Building):** 0.00002 giây (chiếm ~0.0%)
*   **Thời gian gọi API LLM (LLM Calls):** 11.010 giây (chiếm ~99.0%)
*   **Tổng độ trễ phản hồi toàn trình (E2E Latency):** 11.129 giây

---

## Phần 3: Pipeline Xử lý Tài liệu (Document Ingestion Pipeline)

Pipeline xử lý tài liệu của ChatML chịu trách nhiệm tiếp nhận tài liệu học tập thô, chuyển đổi văn bản thành các vector nhúng ngữ nghĩa (embeddings) và lưu trữ vào Vector Database để làm cơ sở tri thức cho chatbot. Quy trình chi tiết gồm 5 bước chính:

```
[Tài liệu Thô] (.pdf, .docx, .txt, .md)
       │
       ▼
1. [Trích xuất Văn bản (Parsing)] (Đọc văn bản & siêu dữ liệu từ tệp)
       │
       ▼
2. [Phân đoạn (Chunking)] (Cắt văn bản thô: Size=500, Overlap=100)
       │
       ▼
3. [Vector hóa (Embedding)] (Chuyển văn bản thành Vector 384 chiều)
       │
       ▼
4. [Lưu trữ Qdrant] (Lưu Vector và chunk text làm Collection)
       │
       ▼
5. [Lưu trữ MongoDB] (Lưu siêu dữ liệu tài liệu & ID liên kết Dataset)
```

1.  **Tiếp nhận & Kiểm tra định dạng (Validation):**
    Tài liệu được tải lên thông qua API `/document/upload-document`. Hệ thống chỉ cho phép các định dạng `.pdf`, `.docx`, `.txt`, `.md` với kích thước tệp tối đa 50MB. Sau khi vượt qua kiểm tra, tệp được lưu vào thư mục lưu trữ cục bộ (`LocalStorage`).
2.  **Trích xuất văn bản thô (Parsing Service):**
    Dịch vụ `ParsingService` phân tích cấu trúc của từng loại tệp và trích xuất nội dung văn bản thuần túy cùng với các thông số cấu trúc cơ bản.
3.  **Cắt phân đoạn văn bản (Chunking Service):**
    Đoạn văn bản dài được `ChunkingService` phân tách thành các đoạn nhỏ (chunks) độc lập. Thuật toán sử dụng **Chunk Size = 500 ký tự** và **Chunk Overlap = 100 ký tự**. Việc thiết lập overlap đảm bảo ngữ cảnh ở ranh giới giữa hai đoạn không bị mất mát hoặc đứt gãy thông tin.
4.  **Nhúng Vector ngữ nghĩa (Embedding Service):**
    Mỗi chunk văn bản được gửi qua `EmbeddingService` để biểu diễn dưới dạng một vector số thực gồm 384 chiều. Quá trình này sử dụng mô hình nhúng cục bộ `BAAI/bge-small-en-v1.5`, giúp chuyển đổi ý nghĩa ngữ nghĩa của câu chữ thành vị trí trong không gian vector.
5.  **Lưu trữ đồng bộ:**
    *   **Qdrant Vector Database:** Lưu trữ các vector 384 chiều kèm nội dung text tương ứng (payload) vào collection `document_chunks` để phục vụ tìm kiếm tương đồng.
    *   **MongoDB:** Lưu trữ metadata của tài liệu (tên tệp, dung lượng, phiên bản, ngày tạo, đường dẫn đĩa vật lý và `dataset_id`) để quản lý tệp trên giao diện và phân loại theo các bộ dữ liệu.
