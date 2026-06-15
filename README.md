# ChatML - Machine Learning Learning Assistant (RAG & Chatbot Service)

ChatML is a modern Retrieval-Augmented Generation (RAG) backend and chatbot service designed to assist users in learning Machine Learning. The system allows users to ingest study materials (such as textbooks or documents in `.pdf`, `.docx`, `.txt`, and `.md` formats) and interact with an intelligent chatbot that answers questions using context retrieved from those documents.

Built with **FastAPI**, ChatML manages document ingestion, parsing, chunking, local vector embedding generation, metadata tracking, and semantic search. It leverages **MongoDB** for metadata storage, **Qdrant** for vector storage and retrieval, and the **Google Gemini API** (`gemini-2.5-flash-lite`) to generate accurate, context-aware explanations.

---

## 🚀 Key Features

* **Interactive Web Chat UI (`/web/`):** A sleek, modern Single Page Application (SPA) designed with a premium dark theme and glassmorphism. It provides:
    * **Connection Status Indicator:** Real-time API server online/offline tracking.
    * **Document Knowledge Base:** Dynamic list displaying all ingested document names, versions, and sizes. Includes document delete controls that automatically synchronize with the MongoDB and Qdrant backends.
    * **Drag-and-Drop Uploader:** Supports `.pdf`, `.docx`, `.txt`, and `.md` files up to 50MB with an interactive upload and parsing progress bar.
    * **Advanced Chat Window:** Supports streaming/typing indicators, source citations (linking response elements back to source document chunks), Markdown parsing (via marked.js), and syntax-highlighted code blocks (via Prism.js).
* **AI Chatbot (`/chat/chat`):** Contextual Q&A using Google Gemini API (`gemini-2.5-flash-lite`), utilizing retrieved document snippets to answer user queries with reference citations.
* **Multi-Format Parsing:** Extracts raw text from `.pdf`, `.docx`, `.txt`, and `.md` files using `unstructured`.
* **Smart Text Chunking:** Splits text into overlapping segments using LangChain's `RecursiveCharacterTextSplitter` to preserve context.
* **Local Vector Embeddings:** Encodes text chunks into 384-dimensional vector embeddings locally using `sentence-transformers` (`BAAI/bge-small-en-v1.5`).
* **Semantic Search Retrieval:** Performs fast and accurate cosine similarity search in `Qdrant` to retrieve relevant document chunks.
* **Metadata & File Storage:** Tracks document metadata, versions, and statuses in MongoDB, while saving original files in local storage.
* **Robust Data Lifecycle Management:** Full CRUD operations for document management (upload, update, retrieve, delete) with synchronized database updates.
* **Full Unit Test Suite:** High coverage offline testing (fully mocked) for all API routers, repositories, and services without requiring live databases or external APIs.

---

## 🛠️ Project Structure

```text
ChatML/
├── app/                       # Application source code
│   ├── api/                   # Router endpoints
│   │   ├── chat.py            # Chatbot API (`/chat/chat`)
│   │   └── document.py        # Document upload, update, deletion, and retrieval APIs
│   ├── core/                  # Configuration & settings management
│   │   └── config.py          # App settings mapping to .env
│   ├── database/              # Database connections
│   │   ├── mongodb.py         # MongoDB client
│   │   └── qdrant.py          # Qdrant vector client
│   ├── models/                # Pydantic schemas/models
│   │   ├── chat.py            # Chat request & response schemas
│   │   ├── document.py        # Document schemas
│   │   └── retrieved_chunk.py # Search result schemas
│   ├── prompts/               # System and user prompt templates
│   │   ├── base.py            # Abstract base prompt
│   │   ├── blank.py           # Fallback prompt for empty context
│   │   └── simple.py          # Standard prompt combining context and question
│   ├── repositories/          # Data access layer
│   │   ├── document_repository.py # MongoDB CRUD repository
│   │   └── qdrant_repository.py   # Qdrant vector points repository
│   ├── services/              # Core business logic
│   │   ├── chat_service.py    # Orchestrates retrieval and LLM answering
│   │   ├── chunking_service.py# Text chunking logic
│   │   ├── document_service.py# Coordinates CRUD lifecycle
│   │   ├── embedding_service.py # Generates vector embeddings
│   │   ├── ingestion_service.py # Coordinates parse -> chunk -> embed -> store
│   │   ├── llm_service.py     # Connects to Google Gemini API
│   │   ├── parsing_service.py # Parses text from files
│   │   └── retrieval_service.py # Performs vector similarity search
│   ├── storage/               # Physical document storage layer
│   │   └── document_storage.py # Local disk storage driver
│   └── main.py                # FastAPI application entrypoint
├── data/                      # Local folder for physical document files
├── docs/                      # Architectural diagrams and documents
│   ├── api_contract.md        # API endpoints contract
│   ├── architechture.md       # High-level architecture text description
│   ├── database_schema.md     # MongoDB collection structures and Qdrant payloads
│   ├── system-flow.png        # Overall system diagram
│   ├── ingestion-flow.png     # Ingestion pipeline diagram
│   └── chat-flow.png          # Chatbot Q&A pipeline diagram
├── reports/                   # Project status reports
│   └── report_0.md            # Detailed project report
├── tests/                     # Unit testing suite (fully mocked)
│   ├── test_api_document.py
│   ├── test_chat_service.py
│   ├── test_chunking_service.py
│   ├── test_document_service.py
│   ├── test_embedding_service.py
│   ├── test_ingestion_service.py
│   ├── test_parsing_service.py
│   └── test_retrieval_service.py
├── web/                       # Frontend Web Chat UI (HTML, CSS, JS)
│   ├── index.html             # Main interface structure
│   ├── style.css              # Custom styling with glassmorphism & dark theme
│   └── app.js                 # API handler, event listeners & UI logic
├── .env                       # Environment configurations (ignored by git)
├── docker-compose.yml         # Docker configuration for MongoDB & Qdrant
├── requirements.txt           # Python library dependencies
└── README.md                  # Project documentation (this file)
```

---

## 🔄 Data Lifecycle & System Flow

### 1. Ingestion (CREATE / UPDATE)
* **CREATE (`POST /document/upload-document`):** The file is saved locally to `data/` -> text parsed -> split into chunks -> vector embeddings generated -> metadata saved to MongoDB and vector points stored in Qdrant (with document metadata in payload).
* **UPDATE (`POST /document/update-document/{document_id}`):** The old file is replaced -> existing Qdrant points matching the `document_id` are deleted -> new version is parsed, chunked, embedded, and uploaded -> MongoDB metadata updated (version increments).

### 2. Retrieval & Chat (USE)
* **Retrieval (`POST /document/retrieval`):** Runs a similarity search in Qdrant for a given query and returns top-k chunks.
* **Chat (`POST /chat/chat`):** Query is embedded -> top matching chunks retrieved -> context assembled -> system prompt constructed -> Gemini model generates a response with citations.

### 3. Deletion (DELETE)
* **DELETE (`DELETE /document/delete-document/{document_id}`):** Deletes local file, clears metadata from MongoDB, and purges all corresponding points from Qdrant.

For visual diagrams, see the files located in the `docs/` folder:
- **System Architecture:** [system-flow.png](file:///D:/Projects/ChatML/docs/system-flow.png)
- **Ingestion Pipeline:** [ingestion-flow.png](file:///D:/Projects/ChatML/docs/ingestion-flow.png)
- **Chat/Retrieval Flow:** [chat-flow.png](file:///D:/Projects/ChatML/docs/chat-flow.png)

---

## ⚙️ Requirements & Setup

### 1. Prerequisites
* **Python 3.10+**
* **Docker & Docker Compose**

### 2. Configure Environment Variables
Create a `.env` file in the root directory (or update your existing one) with the following content:
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

# Google Gemini API Key
GEMINI=your_gemini_api_key
```

### 3. Start Database Services
Spin up **MongoDB** and **Qdrant** using Docker Compose:
```bash
docker compose up -d
```

### 4. Install Dependencies
Set up a Python virtual environment and install the package requirements:
```bash
python -m venv venv
source venv/Scripts/activate # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 5. Run the Application
Start the Uvicorn development server:
```bash
uvicorn app.main:app --reload
```
Once running:
* Access the interactive API documentation (Swagger UI) at: [http://localhost:8000/docs](http://localhost:8000/docs).
* Access the **Interactive Web Chat UI** at: [http://localhost:8000/web/index.html](http://localhost:8000/web/index.html) or [http://localhost:8000/web/](http://localhost:8000/web/).

---

## 🧪 Running Unit Tests

Unit tests are located in the `tests/` directory and use mocks to bypass actual model loading and database calls, ensuring speed and reliability.

To run all tests, run:
```bash
pytest tests/
```

To run individual tests:
* `python -m pytest tests/test_api_document.py`
* `python -m pytest tests/test_chat_service.py`
* `python -m pytest tests/test_chunking_service.py`
* `python -m pytest tests/test_document_service.py`
* `python -m pytest tests/test_embedding_service.py`
* `python -m pytest tests/test_ingestion_service.py`
* `python -m pytest tests/test_parsing_service.py`
* `python -m pytest tests/test_retrieval_service.py`

---

## 📡 API Contract

### Document Endpoints
| Method | Endpoint | Description |
|---|---|---|
| **POST** | `/document/upload-document` | Uploads a document file, saves it, chunks it, generates embeddings, and inserts it. |
| **POST** | `/document/update-document/{document_id}` | Replaces a document file, deletes old chunks/points, and re-ingests new content. |
| **GET** | `/document/get-document/{document_id}` | Retrieves document metadata from MongoDB. |
| **GET** | `/document/get-list-document` | Lists all documents ingested in MongoDB. |
| **DELETE** | `/document/delete-document/{document_id}` | Deletes files from disk, metadata from MongoDB, and vectors from Qdrant. |
| **POST** | `/document/retrieval` | Runs a similarity search in Qdrant based on a query parameter. |

### Chat Endpoints
| Method | Endpoint | Description |
|---|---|---|
| **POST** | `/chat/chat` | Receives a user question, retrieves matching chunks, and generates an answer using Gemini API. |

---

## 🔮 Roadmap & Future Improvements
* **Hybrid Search:** Combine sparse vector search (BM25) with dense vector search to enhance keyword matching and semantic context.
* **Context Re-ranking:** Implement a re-ranking model (e.g. Cross-Encoder) to refine the top retrieved chunks before context generation.

