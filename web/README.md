# ChatML Frontend

A modern, responsive Single Page Application (SPA) designed as the user interface for the ChatML assistant.

## 🚀 Features
* **Interactive Chat Interface:** Supports message streaming, markdown rendering (via marked.js), syntax-highlighted code blocks (via Prism.js), and citation links back to document chunks.
* **Document Knowledge Base:** Displays all ingested document versions, metadata, and sizes. Includes delete controls.
* **Drag-and-Drop Uploader:** Supports file uploads up to 50MB (PDF, DOCX, TXT, MD) with real-time parsing progress feedback.
* **Connection Status Indicator:** Displays online/offline status of the FastAPI backend.
* **Modern Design:** Dark-themed UI with glassmorphism effects and smooth transitions.

---

## 📂 Files
* [index.html](index.html) - Structural layout of the SPA.
* [style.css](style.css) - Vanilla CSS stylesheet detailing design tokens, animations, and layouts.
* [app.js](app.js) - Client-side logic for API integration, DOM updates, and UI event handling.

---

## 🛠️ Usage
The frontend is hosted automatically by the FastAPI backend server when running:
* **URL:** [http://localhost:8000/web/index.html](http://localhost:8000/web/index.html) (or [http://localhost:8000/web/](http://localhost:8000/web/))

Alternatively, it can be served using any standard HTTP server (e.g. `npx serve web/`), provided the backend API endpoints at `/document/` and `/chat/` are accessible and CORS is configured properly.
