import shutil
from pathlib import Path

from fastapi import APIRouter, File, HTTPException, Query, UploadFile
from qdrant_client import AsyncQdrantClient

from app.config import get_settings
from app.core.rag.retriever import retrieve_collection
from app.core.vector.collections import COLL_LAW
from app.ingestion.law_pdf_loader import embed_law_chunks, load_law_pdf

router = APIRouter()


@router.get("/search")
async def search_law(q: str = Query(..., min_length=2), k: int = 5):
    hits = await retrieve_collection(COLL_LAW, q, k=k)
    return {"query": q, "items": hits}


@router.post("/upload")
async def upload_law_pdf(file: UploadFile = File(...)):
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported.")

    s = get_settings()
    law_dir = Path(s.law_dir)
    law_dir.mkdir(parents=True, exist_ok=True)
    
    dest = law_dir / file.filename
    with dest.open("wb") as f:
        shutil.copyfileobj(file.file, f)

    try:
        # 1. Extract text and chunk by §
        chunks = await load_law_pdf(dest)
        if not chunks:
            raise HTTPException(status_code=400, detail="No text could be extracted from this PDF.")
            
        # 2. Embed and index
        points = await embed_law_chunks(chunks)
        if points:
            # Instantiate directly to bypass deps.py issues
            q = AsyncQdrantClient(url=s.qdrant_url, api_key=s.qdrant_api_key or None)
            await q.upsert(
                collection_name=COLL_LAW,
                points=[{"id": pid, "vector": v, "payload": p} for pid, v, p in points],
            )
            await q.close()
            
        return {"filename": file.filename, "chunks_indexed": len(points)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))