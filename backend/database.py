import asyncpg
from langchain_ollama import OllamaEmbeddings
from langchain_postgres import PGVector

from config import (
    COLLECTION_NAME,
    DATABASE_URL,
    EMBEDDING_MODEL,
    OLLAMA_BASE_URL,
)

# Gemeinsamer Async-Pool fuer direkte SQL-Operationen.
_pool: asyncpg.Pool | None = None


def async_psycopg_url() -> str:
    """Convert a standard postgresql:// URL to psycopg3 format."""
    return DATABASE_URL.replace("postgresql://", "postgresql+psycopg://", 1)




def get_vector_store(collection_name: str = None) -> PGVector:
    """
    Erstellt ein PGVector Objekt.
    Wenn collection_name übergeben wird, nutzt es diese spezifische Collection (z.B. session_id).
    Ansonsten nutzt es die globale Standard-Collection für das K-Laufwerk.
    """
    embeddings = OllamaEmbeddings(
        model=EMBEDDING_MODEL,
        base_url=OLLAMA_BASE_URL,
    )
    
    # Entscheide, welche Collection genutzt werden soll
    target_collection = collection_name if collection_name else COLLECTION_NAME
    
    # Wir instanziieren PGVector hier dynamisch. 
    # Das ist performant, da die eigentlichen DB-Verbindungen 
    # im Hintergrund über den async_psycopg Treiber / Connection Pool laufen.
    return PGVector(
        embeddings=embeddings,
        collection_name=target_collection,
        connection=async_psycopg_url(),
        use_jsonb=True,
        async_mode=True,
    )


async def get_pool() -> asyncpg.Pool:
    """Liefert (und cached) den asyncpg Connection-Pool."""
    global _pool
    if _pool is None:
        _pool = await asyncpg.create_pool(DATABASE_URL, min_size=2, max_size=10)
    return _pool


async def init_db() -> None:
    """Create extension and initialize PGVector tables asynchronously."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        # 1. Ensure the vector extension exists
        await conn.execute("CREATE EXTENSION IF NOT EXISTS vector;")
    
    # 2. Get the vector store instance for the default collection
    vs = get_vector_store()
    
    # 4. Safely create tables and the collection asynchronously
    await vs.acreate_tables_if_not_exists()
    await vs.acreate_collection()


# --- NEUE FUNKTIONEN FÜR DIE CHAT-HISTORIE ---

async def close_db() -> None:
    """Release shared resources."""
    global _pool
    if _pool:
        # Beim Shutdown aktive Verbindungen sauber schliessen.
        await _pool.close()
        _pool = None