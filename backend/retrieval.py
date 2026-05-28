import logging

from database import get_vector_store
from config import RAG_TOP_K

from langchain.retrievers import ContextualCompressionRetriever
from langchain.retrievers.document_compressors import CrossEncoderReranker
from langchain_community.cross_encoders import HuggingFaceCrossEncoder

logger = logging.getLogger("bwiki.retrieval")

compressor = None  

logger.info("Lade Reranker-Modell (BAAI/bge-reranker-v2-m3)... Dies dauert beim ersten Start etwas.")
try:
    reranker_model = HuggingFaceCrossEncoder(model_name="BAAI/bge-reranker-v2-m3")
    compressor = CrossEncoderReranker(model=reranker_model, top_n=RAG_TOP_K)
    logger.info("✅ Reranker erfolgreich geladen.")
except Exception as e:
    logger.error(f"❌ Fehler beim Laden des Rerankers: {e}")


async def rag_search_async(query: str) -> str:
    """Führt eine asynchrone RAG-Suche durch (mit Reranker, falls verfügbar)."""
    vs = get_vector_store()

    try:
        logger.info(f"🔍 Suche gestartet für: '{query}'")

        # 1. Base Retriever: Wir holen großzügig 50 Dokumente
        base_retriever = vs.as_retriever(search_kwargs={"k": 50})
        base_docs = await base_retriever.ainvoke(query)

        if not base_docs:
            logger.warning("⚠️ Keine Dokumente in der Vektor-DB gefunden.")
            return ""

        # 2. Reranking anwenden (Aber nur, wenn der Reranker erfolgreich geladen wurde!)
        if compressor is not None:
            # Wir rufen den Reranker hier manuell auf, um Score-Probleme zu umgehen
            docs = compressor.compress_documents(base_docs, query)
            logger.info("✅ Dokumente erfolgreich gereranked.")
        else:
            # NOTFALL-PLAN: Wenn der Reranker kaputt ist, nehmen wir einfach die Top K der normalen Suche
            logger.warning("⚠️ Reranker nicht aktiv! Falle auf normale Vektorsuche zurück.")
            docs = base_docs[:RAG_TOP_K]

        # 3. Formatierung der Quellen
        kontext_bloecke = []
        for doc in docs:
            path = doc.metadata.get("file_path", "Unbekannter Pfad")
            quelle = doc.metadata.get("filename", doc.metadata.get("source", "Unbekannt"))

            block = f"--- QUELLE: {quelle} ---\n{doc.page_content}"
            kontext_bloecke.append(block)

            # Relevanz-Score loggen (falls vorhanden)
            score = doc.metadata.get("relevance_score", "N/A")
            logger.info(f"📄 Gefunden: {quelle} | Relevanz-Score: {score}")

        return "\n\n".join(kontext_bloecke)

    except Exception as e:
        logger.error(f"❌ Vektor-Suche/Reranking fehlgeschlagen: {e}")
        return ""