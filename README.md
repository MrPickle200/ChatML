# ChatML - Machine Learning Learning Assistant

ChatML is a Retrieval-Augmented Generation (RAG) assistant designed to help users learn Machine Learning. It allows users to ingest study documents (`.pdf`, `.docx`, `.txt`, `.md`) and interact with a chatbot that answers questions using retrieved context.

---

## 🛠️ Project Structure

* **[app/](app/) (Backend Service):** Built with FastAPI, MongoDB, Qdrant, and NVIDIA AI Endpoints. Manages ingestion, chunking, hosted NVIDIA embeddings, and retrieval. See [app/README.md](app/README.md) for backend details.
* **[web/](web/) (Frontend Web UI):** A single-page application (SPA) with a modern dark theme and glassmorphism for document management and chat. See [web/README.md](web/README.md) for UI details.
* **[docs/](docs/) (Architecture & Design):** Contains workflow diagrams and technical specifications.
* **[tests/](tests/) (Unit Tests):** Offline unit testing suite for all services and routers.

---

## ⚡ Quick Start

### 1. Configure Environment
Copy `.env.example` to `.env`, then set the NVIDIA API key:
```env
MONGODB_URI=mongodb://localhost:27017
MONGODB_DATABASE=chatml

QDRANT_HOST=localhost
QDRANT_PORT=6333
QDRANT_COLLECTION_NAME=document_chunks
QDRANT_VECTOR_SIZE=1024

CHUNK_SIZE=500
CHUNK_OVERLAP=100

EMBEDDING_MODEL=nvidia/nv-embedqa-e5-v5
NVIDIA_API_KEY=your_key_here
```

The optional comma-separated `NVIDIA_MODELS` value controls the model fallback order.
The default order prioritizes `meta/llama-3.1-8b-instruct`, then falls back to
`nvidia/nemotron-mini-4b-instruct` for low-latency responses.

`nv-embedqa-e5-v5` produces 1024-dimensional vectors. Existing collections created
with a different dense-vector size must be recreated and their documents re-ingested.
Back up any required data first; this migration does not re-embed stored vectors.

### 2. Launch Databases
Ensure Docker is running, then start MongoDB and Qdrant:
```bash
docker compose up -d
```

### 3. Start Application
Install dependencies and run the server:
```bash
python -m venv venv
source venv/Scripts/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

* **Interactive Web UI:** [http://localhost:8000/web/](http://localhost:8000/web/)
* **API Swagger Docs:** [http://localhost:8000/docs](http://localhost:8000/docs)

---

## 🧪 Run Tests
```bash
pytest tests/
```
