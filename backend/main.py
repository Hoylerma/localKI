import asyncio
import json
import logging
import os
import uuid
import time
from typing import List, Optional

from fastapi import FastAPI, File, HTTPException, Request, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, FileResponse
from pydantic import BaseModel

from database import close_db, init_db
from documents import delete_document, list_documents
from file_watcher import ingest_document_with_hash, sync_documents, watch_loop
from agents.rag import stream_response
from agents.summary import summary_agent

# --- NEUE IMPORTE FÜR DIE TITEL-NOTWEICHE ---
from langchain_ollama import ChatOllama
from langchain_core.messages import HumanMessage
from config import CHAT_MODEL, OLLAMA_BASE_URL

app = FastAPI()

# Watcher-Einstellungen: Falls WATCH_DIR gesetzt ist, wird ein Hintergrund-Sync gestartet.
WATCH_DIR = os.getenv("WATCH_DIR", "")
WATCH_INTERVAL = int(os.getenv("WATCH_INTERVAL", "30"))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("bwiki")

# CORS-Origins aus Umgebungsvariable konfigurierbar machen
CORS_ORIGINS = os.getenv(
    "CORS_ORIGINS", 
    "http://localhost,http://127.0.0.1,http://localhost:3080,http://127.0.0.1:3080"
).split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("shutdown")
async def shutdown():
    await close_db()

@app.get("/")
async def root():
    return {"status": "Backend läuft", "engine": "Ollama ready"}


# --- OpenAI kompatible Modelle ---
class OpenAIMessage(BaseModel):
    role: str
    content: str

class OpenAIRequest(BaseModel):
    model: str
    messages: List[OpenAIMessage]
    stream: Optional[bool] = False

@app.post("/v1/chat/completions")
async def openai_chat(req: OpenAIRequest, request: Request):
    # Eindeutige ID und Zeitstempel für diese spezifische Chat-Antwort generieren
    chat_id = f"chatcmpl-{uuid.uuid4().hex}"
    created = int(time.time())
    
    # Die letzte Nachricht des Nutzers auslesen
    user_query = req.messages[-1].content if req.messages else ""
    
    async def generate():
        # 1. INITIAL-CHUNK: Wir sagen LibreChat zwingend, dass jetzt der "assistant" spricht
        initial_payload = {
            "id": chat_id,
            "object": "chat.completion.chunk",
            "created": created,
            "model": req.model,
            "choices": [{"index": 0, "delta": {"role": "assistant"}, "finish_reason": None}]
        }
        yield f"data: {json.dumps(initial_payload)}\n\n"

        # =================================================================
        # 🚨 NOTWEICHE: TITEL-GENERIERUNG ABFANGEN (KEIN RAG ERLAUBT!)
        # =================================================================
        if "Provide a concise, 5-word-or-less title" in user_query:
            logger.info("⚡ Umgehe RAG für LibreChat Titel-Generierung")
            
            # Wir rufen Ollama DIREKT auf, ohne die Datenbank anzufassen
            llm = ChatOllama(model=CHAT_MODEL, base_url=OLLAMA_BASE_URL)
            
            async for chunk in llm.astream([HumanMessage(content=user_query)]):
                if await request.is_disconnected():
                    break
                payload = {
                    "id": chat_id,
                    "object": "chat.completion.chunk",
                    "created": created,
                    "model": req.model,
                    "choices": [{"index": 0, "delta": {"content": chunk.content}, "finish_reason": None}]
                }
                yield f"data: {json.dumps(payload)}\n\n"

        # =================================================================
        # NORMALE ANFRAGEN (MIT RAG ODER AGENTEN)
        # =================================================================
        elif req.model == "BWI-summary-agent":
            # --- ZUSAMMENFASSUNGS AGENT ---
            async for chunk in summary_agent(req.messages, request):
                payload = {
                    "id": chat_id,
                    "object": "chat.completion.chunk",
                    "created": created,
                    "model": req.model,
                    "choices": [{"index": 0, "delta": {"content": chunk}, "finish_reason": None}]
                }
                yield f"data: {json.dumps(payload)}\n\n"
        else:
            # --- STANDARD RAG AGENT ---
            history = "\n".join([f"{m.role}: {m.content}" for m in req.messages[:-1]])
            
            async for chunk in stream_response(user_query, request, history=history):
                payload = {
                    "id": chat_id,
                    "object": "chat.completion.chunk",
                    "created": created,
                    "model": req.model,
                    "choices": [{"index": 0, "delta": {"content": chunk}, "finish_reason": None}]
                }
                yield f"data: {json.dumps(payload)}\n\n"
        
        # 3. ABSCHLUSS-CHUNK: Wir sagen LibreChat offiziell, dass der Stream beendet ist
        final_payload = {
            "id": chat_id,
            "object": "chat.completion.chunk",
            "created": created,
            "model": req.model,
            "choices": [{"index": 0, "delta": {}, "finish_reason": "stop"}]
        }
        yield f"data: {json.dumps(final_payload)}\n\n"
        yield "data: [DONE]\n\n"

    return StreamingResponse(generate(), media_type="text/event-stream")


@app.get("/view")
async def view_document(path: str):
    """Gibt ein Dokument direkt an den Browser zurück, um es anzuzeigen."""
    
    # --- SICHERHEITS-CHECK ---
    # Erlaubt nur Pfade, die mit /mnt/dokumente/ beginnen!
    if not path.startswith("/mnt/dokumente/"):
        raise HTTPException(status_code=403, detail="Zugriff verweigert. Ungültiger Pfad.")
    
    if not os.path.isfile(path):
        raise HTTPException(status_code=404, detail="Datei nicht gefunden oder Pfad falsch.")
    
    return FileResponse(path, content_disposition_type="inline")


@app.on_event("startup")
async def startup():
    await init_db()
    if WATCH_DIR and os.path.isdir(WATCH_DIR):
        asyncio.create_task(watch_loop(WATCH_DIR, WATCH_INTERVAL))

@app.post("/sync")
async def trigger_sync():
    if not WATCH_DIR or not os.path.isdir(WATCH_DIR):
        raise HTTPException(status_code=400, detail="Kein Watch-Verzeichnis konfiguriert")
    stats = await sync_documents(WATCH_DIR)
    return {"status": "synced", **stats}