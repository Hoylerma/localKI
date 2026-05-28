import os
from fastapi import Request
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from langchain_ollama import ChatOllama
from config import CHAT_MODEL, OLLAMA_BASE_URL

def load_prompt(filename: str) -> str:
    """Lädt den Inhalt einer Markdown-Datei aus dem prompts-Ordner."""
    # Ermittelt den Pfad relativ zu dieser Datei (summary.py)
    base_path = os.path.dirname(os.path.dirname(__file__)) # Geht eine Ebene hoch zum backend-root
    file_path = os.path.join(base_path, "prompts", filename)
    
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        print(f"Fehler beim Laden des Prompts {filename}: {e}")
        return "Du bist ein hilfreicher KI-Assistent."

async def summary_agent(messages: list, request: Request):
    """
    Nimmt die OpenAI-kompatiblen Nachrichten von LibreChat entgegen,
    lädt den System-Prompt aus einer MD-Datei und streamt die Antwort.
    """
    llm = ChatOllama(model=CHAT_MODEL, base_url=OLLAMA_BASE_URL)
    
    langchain_messages = []

    # 1. System-Prompt aus der externen Markdown-Datei laden
    prompt_content = load_prompt("summary.md")
    langchain_messages.append(SystemMessage(content=prompt_content))

    # 2. Historie und hochgeladene Dokumenttexte aus LibreChat übernehmen
    for msg in messages:
        # Falls LibreChat die Nachrichten als Objekte mit Attributen sendet:
        role = getattr(msg, 'role', None) or msg.get('role')
        content = getattr(msg, 'content', None) or msg.get('content')

        if role == "user":
            langchain_messages.append(HumanMessage(content=content))
        elif role == "assistant":
            langchain_messages.append(AIMessage(content=content))
        elif role == "system":
            
            pass

    # 3. Stream generieren und an FastAPI zurückgeben
    async for chunk in llm.astream(langchain_messages):
        if await request.is_disconnected():
            break
        yield chunk.content