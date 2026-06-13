# ChatML - Document Ingestion & RAG Retrieval Service

ChatML is a modern document ingestion and Retrieval-Augmented Generation (RAG) retrieval backend built with **FastAPI**. It provides a robust pipeline to upload, parse, chunk, embed, store, and semantically retrieve document sections using MongoDB for metadata storage and Qdrant for vector embeddings.

---

## 🚀 Key Features

* **Multi-Format Parsing:** Extracts text and page numbers from `.pdf`, `.docx`, `.txt`, and `.md` files using `unstructured`.
* **Smart Text Chunking:** Splits parsed text into overlapping pieces using LangChain's `RecursiveCharacterTextSplitter`.
* **Local Embeddings:** Embeds text chunks locally using the `sentence-transformers` library (defaulting to `BAAI/bge-small-en-v1.5`).
* **Vector Search Database:** Stores embedded chunks in `Qdrant` for fast and accurate cosine similarity searches.
* **Metadata & Files Management:** Tracks document details in MongoDB and manages underlying files locally.
* **REST API Endpoints:** CRUD operations for documents and a retrieval API to run semantic search queries.
* **Full Unit Test Suite:** High coverage mock tests for all services and router endpoints, allowing test execution offline without loading heavy models or database instances.

---

## 🛠️ Project Structure

```
ChatML/
├── app/                       # Application source code
│   ├── api/                   # Router endpoints (e.g., document.py)
│   ├── core/                  # Configuration & settings management
│   ├── database/              # Database clients (MongoDB and Qdrant)
│   ├── models/                # Pydantic schemas/models (Chunk, Document, etc.)
│   ├── repositories/          # DB access layer (MongoDocumentRepository, QdrantRepository)
│   ├── services/              # Core business logic (chunking, embedding, ingestion, retrieval)
│   ├── storage/               # Local file storage layer
│   └── main.py                # FastAPI app entrypoint
├── data/                      # Local document files storage directory
├── docs/                      # Diagrams and architectural documents
├── tests/                     # Unit test suite (fully mocked)
├── .env                       # Environment configurations
├── docker-compose.yml         # Container configuration for databases (MongoDB & Qdrant)
├── requirements.txt           # Python package dependencies
└── README.md                  # Project documentation
```

---

## ⚙️ Requirements & Setup

### 1. Prerequisites
* **Python 3.10+**
* **Docker & Docker Compose**

### 2. Configure Environment Variables
Create a `.env` file in the root directory (or use the existing one) and configure the variables:
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
```

### 3. Start Database Services
Spin up **MongoDB** and **Qdrant** using Docker Compose:
```bash
docker compose up -d
```

### 4. Install Dependencies
Initialize your virtual environment and install the required Python packages:
```bash
python -m venv venv
source venv/Scripts/activate # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 5. Run the Application
Start the FastAPI server using Uvicorn:
```bash
uvicorn app.main:app --reload
```
Once running, you can access the Swagger UI documentation at: [http://localhost:8000/docs](http://localhost:8000/docs).

---

## 🧪 Running Unit Tests

A comprehensive suite of unit tests is included in the `tests/` directory. All unit tests use unittest mock capabilities to avoid making real database queries or downloading heavy models.

To run the entire test suite, simply run:
```bash
pytest tests/
```

Or execute individual test files:
* `python -m pytest tests/test_chunking_service.py`
* `python -m pytest tests/test_parsing_service.py`
* `python -m pytest tests/test_embedding_service.py`
* `python -m pytest tests/test_ingestion_service.py`
* `python -m pytest tests/test_document_service.py`
* `python -m pytest tests/test_retrieval_service.py`
* `python -m pytest tests/test_api_document.py`

---

## 📡 API Contract (Document Routing)

| Method | Endpoint | Description |
|---|---|---|
| **POST** | `/document/upload-document` | Uploads a file, saves it, chunks it, encodes it, and ingests it into Qdrant. |
| **POST** | `/document/update-document/{document_id}` | Replaces an existing document's file, deletes old chunks/points, and re-ingests new content. |
| **GET** | `/document/get-document/{document_id}` | Retrieves metadata for a document from MongoDB. |
| **GET** | `/document/get-list-document` | Lists all documents loaded into the service. |
| **DELETE** | `/document/delete-document/{document_id}` | Deletes document files from disk, its metadata from MongoDB, and its vector points from Qdrant. |
| **GET** | `/document/retrieval` | Runs a similarity search in Qdrant based on a query parameter. |
