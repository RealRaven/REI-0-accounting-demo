import shutil
import uuid
from pathlib import Path

from fastapi import APIRouter, File, UploadFile

from app.config import get_settings
from app.ingestion.pdf_parser import parse_pdf
from app.core.rag.chunking import chunk_text
from app.core.vector.collections import COLL_DOCS
from app.api.deps import get_qdrant
from app.core.llm.embeddings import embed_texts

router = APIRouter()


@router.post("/upload")
async def upload_document(file: UploadFile = File(...)):
    s = get_settings()
    inbox = Path(s.inbox_dir)
    inbox.mkdir(parents=True, exist_ok=True)
    dest = inbox / file.filename
    with dest.open("wb") as f:
        shutil.copyfileobj(file.file, f)

    text = parse_pdf(dest)
    chunks = chunk_text(text, max_chars=900, overlap=120)
    vectors = await embed_texts(chunks)

    doc_id = uuid.uuid4().hex[:10]
    points = []
    for i, (chunk, vec) in enumerate(zip(chunks, vectors)):
        points.append({
            "id": f"{doc_id}-{i}",
            "vector": vec,
            "payload": {
                "doc_id": doc_id,
                "page": 1,
                "chunk_idx": i,
                "text": chunk,
                "source": str(dest),
            },
        })
    if points:
        await get_qdrant().upsert(collection_name=COLL_DOCS, points=points)
    return {"doc_id": doc_id, "chunks": len(points)}