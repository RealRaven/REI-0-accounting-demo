import shutil
from pathlib import Path

from fastapi import APIRouter, File, HTTPException, UploadFile

from app.config import get_settings
from app.ingestion.invoice_extractor import extract_invoice
from app.ingestion.pdf_parser import parse_pdf
from app.core.vector.collections import COLL_INVOICES
from app.api.deps import get_qdrant
from app.core.llm.embeddings import embed_texts

router = APIRouter()


@router.post("/upload")
async def upload_invoice(file: UploadFile = File(...)):
    s = get_settings()
    inbox = Path(s.inbox_dir)
    processed = Path(s.processed_dir)
    inbox.mkdir(parents=True, exist_ok=True)
    processed.mkdir(parents=True, exist_ok=True)

    dest = inbox / file.filename
    with dest.open("wb") as f:
        shutil.copyfileobj(file.file, f)

    text = parse_pdf(dest)
    if not text.strip():
        raise HTTPException(422, "no text extracted from PDF")

    inv = await extract_invoice(text)
    inv["pdf_path"] = str(dest)

    vec = (await embed_texts([text]))[0]
    q = get_qdrant()
    await q.upsert(
        collection_name=COLL_INVOICES,
        points=[{
            "id": inv["doc_id"],
            "vector": vec,
            "payload": inv,
        }],
    )
    return {"doc_id": inv["doc_id"], "invoice": inv}


@router.get("")
async def list_invoices(limit: int = 50):
    q = get_qdrant()
    res, _ = await q.scroll(collection_name=COLL_INVOICES, limit=limit, with_payload=True)
    return {"items": [p.payload for p in res]}