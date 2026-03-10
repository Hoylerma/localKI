# bwiki – LangChain RAG Backend

A FastAPI backend that uses **LangChain** for document ingestion, retrieval-augmented generation (RAG), and chat.  
Documents are stored as embeddings in **Postgres + pgvector**.  
The LLM and embedding model are served by **Ollama**.

---

## Architecture

```
Frontend (Vite/React)
       │
       ▼
FastAPI (main.py)
  ├─ /upload  → langchain_rag.ingest_document
  ├─ /documents  → langchain_rag.list_documents
  ├─ /documents/{filename}  DELETE → langchain_rag.delete_document
  └─ /chat  → rag_search_async → ChatOllama (streaming)

langchain_rag.py
  ├─ OllamaEmbeddings  (EMBEDDING_MODEL)
  ├─ PGVector  (langchain-postgres)
  ├─ RecursiveCharacterTextSplitter
  └─ rag_search Tool  (LangChain @tool)

Postgres + pgvector  ←→  langchain_pg_collection / langchain_pg_embedding
```

---

## Quick Start

### 1. Copy and configure environment variables

```bash
cp .env.example .env   # or create .env manually (see below)
```

### 2. Start all services

```bash
docker compose up --build
```

### 3. Upload a document

```bash
curl -F "file=@my-document.pdf" http://localhost:8000/upload
```

### 4. Chat

```bash
curl -X POST http://localhost:8000/chat \
     -H "Content-Type: application/json" \
     -d '{"message": "Was steht im Dokument?"}'
```

---

## Required Environment Variables

| Variable | Default | Description |
|---|---|---|
| `POSTGRES_USER` | – | Postgres username |
| `POSTGRES_PASSWORD` | – | Postgres password |
| `POSTGRES_DB` | – | Postgres database name |
| `OLLAMA_BASE_URL` | `http://host.docker.internal:11434` | Ollama base URL (preferred) |
| `OLLAMA_API` | – | Legacy alias for `OLLAMA_BASE_URL` (still supported) |
| `EMBEDDING_MODEL` | `nomic-embed-text` | Ollama model used for embeddings |
| `CHAT_MODEL` | `llama3.2` | Ollama model used for chat |
| `BACKEND_PORT` | – | Host port for the backend (e.g. `8000`) |
| `FRONTEND_PORT` | – | Host port for the frontend (e.g. `5173`) |
| `VITE_API_BASE_URL` | – | API URL visible to the browser (e.g. `http://localhost:8000`) |

### Optional / Tuning

| Variable | Default | Description |
|---|---|---|
| `CHUNK_SIZE` | `1000` | Characters per chunk |
| `CHUNK_OVERLAP` | `200` | Overlap between consecutive chunks |
| `MAX_CONTEXT_CHARS` | `4000` | Maximum total context characters sent to the LLM |
| `RAG_TOP_K` | `5` | Number of chunks retrieved per query |
| `MIN_SIMILARITY` | `0.3` | Minimum relevance score (0–1) to include a chunk |

---

## LangSmith Tracing

Set the following variables to enable [LangSmith](https://smith.langchain.com/) tracing:

| Variable | Description |
|---|---|
| `LANGSMITH_API_KEY` | Your LangSmith API key |
| `LANGSMITH_TRACING` | Set to `true` to enable tracing |
| `LANGSMITH_PROJECT` | Project name shown in LangSmith (default: `bwiki`) |

LangChain automatically picks up these variables – no code changes needed.

---

## Document Ingestion

Supported file formats: `pdf`, `docx`, `txt`, `md`, `csv`, `json`, `xml`, `html`.

Documents are:
1. Parsed to plain text.
2. Split into overlapping chunks with `RecursiveCharacterTextSplitter`.
3. Embedded via `OllamaEmbeddings`.
4. Stored in the `documents` collection in Postgres/pgvector.

Re-uploading the same filename replaces all previous chunks for that document.

---

## RAG Tool

`langchain_rag.rag_search` is a LangChain `@tool` that:

1. Takes a query string.
2. Performs a cosine-similarity search against the vector store.
3. Filters results below `MIN_SIMILARITY`.
4. Returns a formatted string containing the top-k chunks, each annotated with its source filename and relevance score.
5. Truncates the total context to `MAX_CONTEXT_CHARS`.

The chat endpoint currently uses **deterministic RAG** (Option B): it always calls the tool before generating a response, and instructs the LLM to cite sources.

---

## API Endpoints

| Method | Path | Description |
|---|---|---|
| `GET` | `/` | Health check |
| `POST` | `/upload` | Upload and ingest a document |
| `GET` | `/documents` | List all ingested documents |
| `DELETE` | `/documents/{filename}` | Delete a document and its chunks |
| `POST` | `/chat` | Streaming chat with RAG context |
