import os
import logging
from pathlib import Path

logger = logging.getLogger("bwiki.config")

# Zentrale Laufzeit-Konfiguration: Alle Werte sind per ENV ueberschreibbar.
# Support both OLLAMA_BASE_URL (preferred) and legacy OLLAMA_API
OLLAMA_BASE_URL: str = os.getenv("OLLAMA_BASE_URL") or os.getenv(
    "OLLAMA_API", "http://localhost:11434"
)
EMBEDDING_MODEL: str = os.getenv("EMBEDDING_MODEL", "nomic-embed-text")
CHAT_MODEL: str = os.getenv("CHAT_MODEL", "qwen3:8b")
DATABASE_URL: str = os.getenv(
    "DATABASE_URL", "postgresql://raguser:ragpass@postgres:5432/ragdb"
)

# LDAP Configuration
LDAP_SERVER: str = os.getenv("LDAP_SERVER", "ldap://ldap.local")
LDAP_DOMAIN: str = os.getenv("LDAP_DOMAIN", "bwi.local")

CHUNK_SIZE: int = int(os.getenv("CHUNK_SIZE", "1000"))
CHUNK_OVERLAP: int = int(os.getenv("CHUNK_OVERLAP", "100"))
RAG_TOP_K: int = int(os.getenv("RAG_TOP_K", "20"))

COLLECTION_NAME = "documents"

# Prompt-Dateien liegen unter backend/prompts/.
PROMPTS_DIR = Path(__file__).parent / "prompts"

def load_prompt(name: str) -> str:
    """Lädt einen Prompt aus dem prompts/ Ordner mit Fallback."""
    path = PROMPTS_DIR / f"{name}.md"
    if not path.exists():
        logger.warning(f"Prompt nicht gefunden: {path}, nutze Fallback")
        return f"Du bist ein hilfreicher Assistent für {name}."
    
    try:
        return path.read_text(encoding="utf-8").strip()
    except Exception as e:
        logger.error(f"Fehler beim Laden des Prompts {name}: {e}")
        return f"Du bist ein hilfreicher Assistent für {name}."


# Beim Import einmal laden, damit der Prompt spaeter nicht pro Request gelesen wird.
SYSTEM_PROMPT = load_prompt("system")