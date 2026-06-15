# Báo cáo Dự án ChatML

- **Thời gian cập nhật:** 14/06/2026
- **Người thực hiện:** Antigravity AI
- **Dự án:** ChatML (Document Ingestion & RAG Retrieval Service)

---

## I. Tổng quan dự án
ChatML là một dự án chatbot hỗ trợ học tập Machine Learning. Hệ thống được thiết kế dưới dạng dịch vụ backend sử dụng mô hình RAG (Retrieval-Augmented Generation), cho phép người dùng nạp các giáo trình, tài liệu học tập Machine Learning (`.pdf`, `.docx`, `.txt`, `.md`) vào hệ thống để chatbot học hỏi và trả lời các câu hỏi thắc mắc dựa trên nội dung chính xác của những tài liệu này.

---

## II. Công nghệ sử dụng (Tech Stack)
Hệ thống được tích hợp các công nghệ hiện đại phục vụ cho RAG và AI Chatbot:
1. **Framework chính:** **FastAPI** - Framework web Python bất đồng bộ hiệu năng cao dùng để xây dựng các RESTful API nhanh chóng và trực quan.
2. **Cơ sở dữ liệu Metadata:** **MongoDB** - Lưu trữ và quản lý metadata của tài liệu học tập tải lên.
3. **Cơ sở dữ liệu Vector:** **Qdrant Vector Database** - Lưu trữ các đoạn văn bản học tập đã được nhúng vector và thực hiện tìm kiếm tương đồng (Similarity Search) dựa trên khoảng cách Cosine.
4. **Trích xuất văn bản (Parsing):** `unstructured` - Trích xuất văn bản thô từ nhiều định dạng file tài liệu khác nhau.
5. **Phân đoạn văn bản (Chunking):** **LangChain** - Sử dụng `RecursiveCharacterTextSplitter` giúp chia tài liệu thành các khối văn bản (chunks) nhỏ có độ dài tối ưu và chồng lấp (overlap) hợp lý để bảo toàn ngữ cảnh.
6. **Vector Embeddings:** `sentence-transformers` - Chạy mô hình nhúng cục bộ `BAAI/bge-small-en-v1.5` để chuyển đổi các đoạn văn bản thành vector 384 chiều.
7. **Mô hình ngôn ngữ lớn (LLM):** **Gemini API (Google GenAI)** - Mô hình tạo câu trả lời tự nhiên cho chatbot dựa trên ngữ cảnh được trích xuất từ tài liệu học tập.
8. **Kiểm thử tự động:** `pytest` - Framework chạy unit tests, kiểm thử chức năng ngoại tuyến thông qua mocking.
9. **Đóng gói dịch vụ:** **Docker & Docker Compose** - Container hóa và chạy các dịch vụ cơ sở dữ liệu độc lập (MongoDB, Qdrant).
10. **Giao diện Web Chatbot (Frontend Web UI):** Xây dựng dưới dạng ứng dụng đơn trang (SPA) tối ưu hóa trải nghiệm người dùng bằng HTML5, CSS3 (phong cách Glassmorphism và Sleek Dark Mode), và Vanilla JavaScript (ES6+). Tích hợp các thư viện qua CDN:
    - **Lucide Icons:** Cung cấp hệ thống biểu tượng trực quan, hiện đại.
    - **marked.js:** Trình phân tích cú pháp giúp chuyển đổi phản hồi Markdown từ LLM thành HTML.
    - **Prism.js:** Tô sáng cú pháp (syntax highlighting) mã nguồn trong câu trả lời (hỗ trợ Python, JavaScript, Bash...).

---

## III. Cấu trúc thư mục dự án (Project Structure)
Dự án được phân chia theo cấu trúc modular rõ ràng giúp dễ bảo trì và mở rộng:

```text
ChatML/
├── app/                       # Mã nguồn chính của ứng dụng
│   ├── api/                   # Định nghĩa các router endpoints
│   │   ├── chat.py            # API Chatbot hỏi đáp (`/chat/chat`)
│   │   └── document.py        # API quản lý tài liệu (tải lên, cập nhật, xóa, tìm kiếm tương đồng)
│   ├── core/                  # Cấu hình hệ thống và quản lý biến môi trường
│   │   └── config.py          # Ánh xạ cấu hình biến môi trường từ .env
│   ├── database/              # Quản lý kết nối cơ sở dữ liệu
│   │   ├── mongodb.py         # Client kết nối MongoDB
│   │   └── qdrant.py          # Client kết nối Qdrant Vector DB
│   ├── models/                # Các schemas/models dữ liệu Pydantic
│   │   ├── chat.py            # Schema yêu cầu & phản hồi Chatbot
│   │   ├── document.py        # Schema thông tin tài liệu
│   │   └── retrieved_chunk.py # Schema kết quả tìm kiếm tương đồng
│   ├── prompts/               # Các mẫu gợi ý (templates prompt) cho LLM
│   │   ├── base.py            # Prompt trừu tượng cơ sở (Abstract class)
│   │   ├── blank.py           # Prompt dự phòng khi ngữ cảnh trống
│   │   └── simple.py          # Prompt tiêu chuẩn kết hợp câu hỏi và ngữ cảnh
│   ├── repositories/          # Lớp thao tác cơ sở dữ liệu (Data Access Layer)
│   │   ├── document_repository.py # CRUD dữ liệu metadata trên MongoDB
│   │   └── qdrant_repository.py   # CRUD và quản lý các điểm vector trên Qdrant
│   ├── services/              # Lớp xử lý logic nghiệp vụ chính (Business Logic Layer)
│   │   ├── chat_service.py    # Điều phối quy trình tìm kiếm ngữ cảnh và gọi LLM trả lời
│   │   ├── chunking_service.py# Logic phân đoạn tài liệu học tập
│   │   ├── document_service.py# Điều phối vòng đời CRUD tài liệu
│   │   ├── embedding_service.py # Sinh vector nhúng 384 chiều từ các đoạn văn bản
│   │   ├── ingestion_service.py # Điều phối quy trình nạp tài liệu (parse -> chunk -> embed -> store)
│   │   ├── llm_service.py     # Kết nối và gọi mô hình Google Gemini API
│   │   ├── parsing_service.py # Trích xuất văn bản thô từ các định dạng file tài liệu
│   │   └── retrieval_service.py # Thực hiện tìm kiếm vector tương đồng trên Qdrant
│   ├── storage/               # Quản lý lưu trữ vật lý tài liệu
│   │   └── document_storage.py # Driver lưu trữ file vật lý trên đĩa cứng local
│   └── main.py                # Điểm khởi chạy ứng dụng FastAPI
├── data/                      # Thư mục lưu trữ vật lý các file tài liệu tải lên
├── docs/                      # Sơ đồ kiến trúc và tài liệu đặc tả hệ thống
│   ├── api_contract.md        # Đặc tả các API endpoints contract
│   ├── architechture.md       # Mô tả kiến trúc hệ thống mức cao
│   ├── database_schema.md     # Đặc tả cấu trúc database MongoDB và payload Qdrant
│   ├── system-flow.png        # Sơ đồ tổng quan luồng hệ thống
│   ├── ingestion-flow.png     # Sơ đồ luồng xử lý nạp tài liệu
│   └── chat-flow.png          # Sơ đồ luồng chatbot hỏi đáp RAG
├── reports/                   # Thư mục chứa các báo cáo dự án
│   └── report_0.md            # Báo cáo chi tiết dự án (file này)
├── tests/                     # Bộ kiểm thử tự động (Unit tests giả lập)
│   ├── test_api_document.py
│   ├── test_chat_service.py
│   ├── test_chunking_service.py
│   ├── test_document_service.py
│   ├── test_embedding_service.py
│   ├── test_ingestion_service.py
│   ├── test_parsing_service.py
│   └── test_retrieval_service.py
├── web/                       # Giao diện người dùng Web Chatbot (HTML, CSS, JS)
│   ├── index.html             # Cấu trúc giao diện ứng dụng
│   ├── style.css              # Định kiểu CSS (Glassmorphism & Dark Mode)
│   └── app.js                 # Xử lý sự kiện giao diện, kết nối API backend
├── .env                       # Cấu hình biến môi trường dự án
├── docker-compose.yml         # Cấu hình Docker để chạy MongoDB & Qdrant
├── requirements.txt           # Danh sách các thư viện Python cần thiết
└── README.md                  # Tài liệu hướng dẫn sử dụng dự án
```

---

## IV. Vòng đời của dữ liệu (Data Lifecycle)
Trong dự án ChatML, dữ liệu tài liệu học tập Machine Learning trải qua vòng đời đầy đủ bao gồm các giai đoạn: Khởi tạo (Create), Sử dụng (Used), Cập nhật (Update), và Xóa (Delete).

### 1. Giai đoạn CREATE (Khởi tạo dữ liệu)
- **Trình kích hoạt:** Người dùng tải lên tệp tài liệu thông qua phương thức POST tới `/document/upload-document` (hoặc kéo-thả tệp tin trực tiếp vào vùng **Upload Zone** trên giao diện Web UI).
- **Lưu trữ Vật lý:** Tệp gốc được lưu trữ cục bộ trên máy chủ trong thư mục dữ liệu `data/` với tên tệp là ID duy nhất dạng UUID.
- **Cơ sở dữ liệu Metadata (MongoDB):** Bản ghi thông tin tài liệu được tạo mới, lưu trữ các trường:
  - `_id`: ID tài liệu tự sinh (UUID).
  - `filename`, `file_type`, `file_size_byte`: Thông tin cơ bản của tệp.
  - `version`: Phiên bản khởi tạo (mặc định = 1).
  - `status`: Trạng thái ban đầu (`"uploaded"`).
  - `created_at`, `updated_at`: Thời gian khởi tạo/cập nhật.
  - `storage`: Đường dẫn lưu trữ vật lý local.
- **Cơ sở dữ liệu Vector (Qdrant):** 
  - Văn bản trong tệp được trích xuất thành chuỗi văn bản thuần túy.
  - Văn bản được cắt nhỏ thành các đoạn (chunks). Mỗi đoạn được gán một UUID (`chunk_id`) và chỉ số index.
  - Mỗi đoạn được tính toán vector embedding (kích thước 384 chiều).
  - Các điểm vector (Points) được ghi vào Qdrant với ID là `chunk_id`, vector nhúng, cùng payload chứa: `document_id`, `dataset_id`, `chunk_id`, `chunk_index`, `chunk_text`, `source` (tên tệp), `version` và tên mô hình nhúng.

### 2. Giai đoạn USED (Sử dụng dữ liệu)
- **Đọc thông tin:** 
  - Xem danh sách tài liệu đang có bằng GET `/document/get-list-document` (đọc trực tiếp từ MongoDB hoặc hiển thị danh sách trong **Cơ sở tri thức** trên thanh bên của Web UI).
  - Xem chi tiết metadata của một tài liệu cụ thể bằng GET `/document/get-document/{document_id}` (đọc từ MongoDB).
- **Truy vấn ngữ nghĩa (Semantic Search):**
  - Truy cập thông qua GET `/document/retrieval`. Nhận câu hỏi học tập, mã hóa câu hỏi thành vector, thực hiện tìm kiếm tương đồng trên Qdrant để trả về các đoạn văn bản Machine Learning có độ tương đồng cao nhất kèm payload.
- **Hỏi đáp tích hợp LLM (RAG Chat):**
  - Truy cập qua POST `/chat/chat`. Hệ thống gọi dịch vụ tìm kiếm ngữ nghĩa Qdrant để lấy các đoạn văn bản chứa thông tin cần tìm, ghép các đoạn này lại làm ngữ cảnh (context), kết hợp câu hỏi học tập để tạo Prompt hoàn chỉnh gửi tới Gemini API. Phản hồi trả về gồm câu trả lời giải thích kiến thức và thông tin nguồn tham khảo.
  - Trên **Web UI**, người học đặt câu hỏi tại khung chat, tin nhắn phản hồi của Bot sẽ tự động hiển thị tài liệu nguồn tham khảo dưới dạng thẻ tag đính kèm (Citations) để người dùng dễ đối chiếu.

### 3. Giai đoạn UPDATE (Cập nhật dữ liệu)
- **Trình kích hoạt:** Người dùng gửi tệp tài liệu mới thay thế thông qua POST tới `/document/update-document/{document_id}`.
- **Xử lý tệp:** Thay thế tệp vật lý cũ trong thư mục `data/` bằng tệp mới.
- **Cập nhật Metadata (MongoDB):**
  - Tăng giá trị phiên bản `version` lên +1.
  - Cập nhật các trường: `filename`, `file_type`, `file_size_byte`, `updated_at`.
  - Đổi trạng thái `status` thành `"updated"`.
- **Đồng bộ hóa Qdrant Vector DB:**
  - Tìm kiếm và xóa tất cả các điểm vector (points) hiện tại trong Qdrant có chứa `document_id` tương ứng để dọn dẹp các chunk cũ của tài liệu này.
  - Tiến hành trích xuất văn bản từ tệp mới, chia nhỏ, nhúng vector và đẩy toàn bộ các vector chunks mới này lên Qdrant với phiên bản `version` mới cập nhật.

### 4. Giai đoạn DELETE (Xóa dữ liệu)
- **Trình kích hoạt:** Người dùng gọi phương thức DELETE tới `/document/delete-document/{document_id}` (hoặc bấm vào biểu tượng Thùng rác cạnh tài liệu trên thanh bên của Web UI).
- **Xóa Vật lý:** Tệp tài liệu tương ứng lưu trữ trong thư mục `data/` bị xóa hoàn toàn khỏi đĩa cứng.
- **Xóa Metadata (MongoDB):** Bản ghi metadata chứa `_id` tương ứng với `document_id` bị xóa sạch khỏi MongoDB.
- **Xóa Vector (Qdrant):** Gửi lệnh xóa toàn bộ các điểm vector (points) trong collection Qdrant có điều kiện lọc payload `document_id` bằng ID tài liệu bị xóa.
- **Đảm bảo tính nhất quán:** Hệ thống được thiết lập cơ chế xử lý lỗi ngoại lệ (exception handling) để ngay cả khi tệp vật lý bị xóa thủ công trước đó, bản ghi trong MongoDB và vector trên Qdrant vẫn được dọn sạch hoàn toàn khi gọi API.

---

## V. Sơ đồ hoạt động và luồng dữ liệu (System Flows)
Để minh họa trực quan cách thức hoạt động của hệ thống, dưới đây là các sơ đồ luồng chính nằm trong thư mục `docs/`:

### 1. Sơ đồ tổng quan hệ thống (Overall System Flow)
Sơ đồ này mô tả cấu trúc tổng thể và các kết nối giữa các thực thể: Người dùng, API Gateway (FastAPI), cơ sở dữ liệu MongoDB (metadata), Qdrant Vector DB (vector chunks) và LLM Service (Gemini API) để tạo nên hệ thống chatbot hỗ trợ học tập Machine Learning.

![Sơ đồ tổng quan hệ thống](../docs/system-flow.png)

### 2. Sơ đồ luồng nạp dữ liệu (Ingestion Flow)
Sơ đồ này chi tiết hóa từng bước xử lý tài liệu khi được đưa vào hệ thống: Tải lên -> Trích xuất văn bản thô -> Chia nhỏ đoạn (chunking) -> Tạo vector nhúng -> Lưu trữ vector và metadata vào cơ sở dữ liệu.

![Sơ đồ luồng nạp dữ liệu](../docs/ingestion-flow.png)

### 3. Sơ đồ luồng trò chuyện hỏi đáp (Chat Flow)
Sơ đồ này mô tả quy trình tiếp nhận câu hỏi của học viên, mã hóa câu hỏi thành vector, thực hiện tìm kiếm tương đồng trên Qdrant để trích xuất các đoạn tài liệu Machine Learning phù hợp nhất, xây dựng ngữ cảnh và chuyển tới Gemini LLM sinh câu trả lời chính xác nhất.

![Sơ đồ luồng trò chuyện](../docs/chat-flow.png)

---

## VI. Chi tiết Giao diện Web Chat UI
Để hỗ trợ việc tương tác thực tế một cách thuận tiện nhất, hệ thống tích hợp sẵn giao diện Web Chat UI hoạt động dưới dạng SPA (Single Page Application). Giao diện này được phục vụ tĩnh tại đường dẫn `/web/` trên máy chủ FastAPI.

Các thành phần giao diện chính gồm:
1. **Thanh chỉ báo trạng thái (Status Indicator):**
   - Nằm ở góc trên bên phải thanh tiêu đề, định kỳ gửi yêu cầu kiểm tra sức khỏe hệ thống (Health Check) tới backend mỗi 10 giây.
   - Hiển thị màu xanh lá cây ("Đang trực tuyến") khi kết nối hoạt động bình thường, và màu đỏ nhấp nháy ("Mất kết nối API") nếu backend ngưng hoạt động hoặc lỗi mạng, giúp chẩn đoán sự cố nhanh chóng.
2. **Thanh bên Quản lý tài liệu (Sidebar):**
   - **Khu vực tải lên (Upload Zone):** Hỗ trợ kéo thả trực tiếp tệp hoặc click để duyệt tải lên các file `.pdf`, `.docx`, `.txt`, `.md`.
   - **Thanh tiến trình (Progress Bar):** Theo dõi phần trăm tải lên tệp tin và hiển thị các trạng thái phân tích tài liệu theo thời gian thực.
   - **Cơ sở tri thức (Knowledge Base):** Hiển thị danh sách các tài liệu hiện đang lưu trữ kèm chỉ số phiên bản và kích thước tệp được tính toán tự động. Cho phép người dùng xóa bất kỳ tài liệu nào trực tiếp từ giao diện với hộp thoại cảnh báo an toàn.
   - **Nút đóng/mở sidebar:** Cho phép thu gọn/mở rộng sidebar linh hoạt để tối ưu hóa không gian trò chuyện trên các thiết bị màn hình nhỏ.
3. **Cửa sổ Trò chuyện (Chat Window):**
   - **Bong bóng tin nhắn của người dùng & Bot:** Phân biệt rõ ràng màu sắc và biểu tượng. Tin nhắn của bot có chỉ báo đang gõ (Typing indicator) dưới dạng dấu 3 chấm chuyển động trước khi kết quả thực tế xuất hiện.
   - **Hộp nhập văn bản thông minh (Input Panel):** Tự động thay đổi chiều cao (giãn dòng) theo nội dung nhập vào. Hỗ trợ phím tắt gửi tin nhanh (`Enter`) và xuống dòng (`Shift + Enter`).
   - **Trích dẫn nguồn tài liệu tham khảo (Citations):** Các file tài liệu nguồn tham chiếu dùng để trả lời câu hỏi được đính kèm trực quan dưới dạng các badge có chứa ID phân đoạn (chunk_id) ở cuối câu trả lời của chatbot.
   - **Biên dịch định dạng hiển thị nâng cao:** Hỗ trợ hiển thị đầy đủ văn bản định dạng Markdown (tiêu đề, in đậm, danh sách...) và tô sáng các khối code (syntax highlighting) thông qua Prism.js.

---

## VII. Đánh giá và định hướng tiếp theo
- Hệ thống hiện tại hoạt động rất ổn định với đầy đủ luồng nghiệp vụ RAG hỗ trợ học tập Machine Learning từ khâu nhập giáo trình đến khâu hỏi đáp thông minh.
- Bộ unit test hỗ trợ tốt cho việc phát triển và bảo trì liên tục.
- **Kế hoạch tiếp theo:** Nghiên cứu cải tiến kỹ thuật tìm kiếm (ví dụ: Hybrid Search kết hợp Keyword Search và Vector Search, tích hợp Re-ranking để nâng cao độ chính xác của ngữ cảnh trước khi đưa vào LLM).
