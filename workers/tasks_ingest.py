from pathlib import Path

from app.config import get_settings
from app.core.llm.embeddings import embed_texts
from app.ingestion.invoice_extractor import extract_invoice
from app.ingestion.pdf_parser import parse_pdf
from workers.celery_app import app


@app.task
def ingest_invoice(path: str) -> dict:
    text = parse_pdf(path)
    import asyncio

    inv = asyncio.run(extract_invoice(text))
    inv["pdf_path"] = path
    return inv