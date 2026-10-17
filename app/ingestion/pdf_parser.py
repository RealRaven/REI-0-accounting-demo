from pathlib import Path

from pypdf import PdfReader


def parse_pdf(path: str | Path) -> str:
    path = Path(path)
    try:
        reader = PdfReader(str(path))
        parts = []
        for page in reader.pages:
            try:
                parts.append(page.extract_text() or "")
            except Exception:
                parts.append("")
        text = "\n".join(parts)
    except Exception:
        text = ""

    if not text.strip():
        try:
            from app.ingestion.ocr import ocr_pdf

            text = ocr_pdf(path)
        except Exception:
            text = ""
    return text