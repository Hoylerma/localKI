import io
import logging
from docx import Document as DocxDocument
from pypdf import PdfReader
from pypdf.errors import PdfReadError, PdfStreamError

logger = logging.getLogger("bwiki.parsers")

def _parse_pdf(file_bytes: bytes) -> str:
    try:
        reader = PdfReader(io.BytesIO(file_bytes))
        text = ""
        for page in reader.pages:
            extracted = page.extract_text()
            if extracted:
                text += extracted + "\n"
        return text
        
    except (PdfReadError, PdfStreamError, Exception) as e:
        # Fängt kaputte Header, unerwartete Dateiendungen und Lesefehler ab
        logger.error(f"❌ PDF konnte nicht gelesen werden (kaputt oder falsches Format). Fehler: {e}")
        return ""  # Gibt leeren Text zurück


def _parse_docx(file_bytes: bytes) -> str:
    doc = DocxDocument(io.BytesIO(file_bytes))
    return "\n".join(p.text for p in doc.paragraphs if p.text.strip())


def _parse_txt(file_bytes: bytes) -> str:
    return file_bytes.decode("utf-8", errors="replace")


def parse_document(filename: str, file_bytes: bytes) -> str:
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    if ext == "pdf":
        return _parse_pdf(file_bytes)
    elif ext == "docx":
        return _parse_docx(file_bytes)
    elif ext in ("txt", "md", "csv", "json", "xml", "html"):
        return _parse_txt(file_bytes)
    else:
        raise ValueError(f"Nicht unterstütztes Dateiformat: .{ext}")
