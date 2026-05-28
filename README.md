# BW-i KI - Librechat + FastAPI + RAG

Dieses Projekt nutzt jetzt Librechat als Benutzeroberflaeche.
Das bisherige React/Vite Frontend und die Chainlit-Integration sind entfernt.

## Architektur

```
Librechat UI
       |
       | HTTP
       v
FastAPI Backend (backend/main.py)
  - /upload
  - /documents
  - /documents/{filename}
  - /v1/chat/completions (OpenAI-kompatibel)

FastAPI verwendet:
  - LangChain + PGVector (Postgres/pgvector)
  - Ollama fuer Chat und Embeddings
  - Librechat fuer die Benutzeroberflaeche
```

## Schnellstart (Docker)

1. Umgebungsvariablen in .env setzen oder pruefen.
2. Stack starten:

```bash
docker compose up --build
```

3. UI im Browser oeffnen:

```text
http://localhost:3080
```

## Wichtige Umgebungsvariablen

| Variable | Default | Beschreibung |
|---|---|---|
| POSTGRES_USER | - | Postgres Benutzer |
| POSTGRES_PASSWORD | - | Postgres Passwort |
| POSTGRES_DB | - | Postgres Datenbank |
| OLLAMA_BASE_URL | http://host.docker.internal:11434 | Ollama URL |
| EMBEDDING_MODEL | nomic-embed-text | Embedding Modell |
| CHAT_MODEL | llama3.1 | Chat Modell |
| BACKEND_PORT | 8000 | Externer FastAPI Port |
| JWT_SECRET | EinSehrLangerZufaelligerStringFuerBWI2026 | JWT Secret fuer Librechat |
| JWT_REFRESH_SECRET | NochEinZufaelligerString123! | JWT Refresh Secret fuer Librechat |
| DOMAIN_CLIENT | http://localhost:3080 | Librechat Client Domain |
| DOMAIN_SERVER | http://localhost:3080 | Librechat Server Domain |

## API Endpunkte (Backend)

| Methode | Pfad | Beschreibung |
|---|---|---|
| GET | / | Healthcheck |
| POST | /upload | Dokument ingestieren |
| GET | /documents | Dokumentliste |
| DELETE | /documents/{filename} | Dokument entfernen |
| POST | /v1/chat/completions | OpenAI-kompatibler Chat-Stream |

## Lokale Entwicklung ohne Docker

Abhaengigkeiten installieren:

```bash
pip install -r backend/requirements.txt
```

Backend starten:

```bash
cd backend
uvicorn main:app --host 0.0.0.0 --port 8000
```

Librechat starten:

```bash
docker compose up --build
```
```
