# ChatML Backend

This is the FastAPI backend service for ChatML, orchestrating document ingestion, chunking, vector embedding, and context-aware chat generation using Google Gemini.

## 🛠️ Key Components & Technologies
* **Framework:** [FastAPI](https://fastapi.tiangolo.com/) for building APIs.
* **Databases:**
  * [MongoDB](https://www.mongodb.com/) (via motor) for document metadata storage.
  * [Qdrant](https://qdrant.tech/) for vector search retrieval.
* **AI & NLP:**
  * [Sentence-Transformers](https://sbert.net/) (`BAAI/bge-small-en-v1.5`) for local vector embeddings.
  * [Google Gemini API](https://ai.google.dev/) (`gemini-2.5-flash-lite`) for context-aware Q&A.
  * [LangChain](https://python.langchain.com/) (`RecursiveCharacterTextSplitter`) for smart text chunking.
  * [Unstructured](https://unstructured.io/) for parsing `.pdf`, `.docx`, `.txt`, and `.md` files.

---

## ⚙️ Setup & Execution

### 1. Prerequisites & Environment
Ensure you have Python 3.10+ and Docker. Define a `.env` in the project root:
```env
MONGODB_URI=mongodb://localhost:27017
MONGODB_DATABASE=chatml
QDRANT_HOST=localhost
QDRANT_PORT=6333
QDRANT_COLLECTION_NAME=document_chunks
QDRANT_VECTOR_SIZE=384
CHUNK_SIZE=500
CHUNK_OVERLAP=100
EMBEDDING_MODEL=BAAI/bge-small-en-v1.5
GEMINI=your_gemini_api_key
```

### 2. Run Database Services
```bash
docker compose up -d
```

### 3. Run Backend API
From the root directory:
```bash
python -m venv venv
source venv/Scripts/activate # Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```
Access Swagger API Docs at: [http://localhost:8000/docs](http://localhost:8000/docs)

---

## 🧪 Running Unit Tests
Unit tests use mocks for external databases and model loading to run quickly.
```bash
pytest tests/
```

---

## 📡 API endpoints

### Documents
* `POST /document/upload-document`: Upload and ingest file.
* `POST /document/update-document/{document_id}`: Replace file and re-index.
* `GET /document/get-document/{document_id}`: Retrieve metadata.
* `GET /document/get-list-document`: List all documents.
* `DELETE /document/delete-document/{document_id}`: Purge document, MongoDB metadata, and vector points.
* `POST /document/retrieval`: Perform similarity search.

### Chat
* `POST /chat/chat`: Generate answer for a question using retrieved context.
