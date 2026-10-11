import csv
import io

from fastapi import APIRouter, File, UploadFile

from app.core.vector.collections import COLL_BANK
from app.api.deps import get_qdrant
from app.core.llm.embeddings import embed_texts

router = APIRouter()


@router.post("/import")
async def import_bank(file: UploadFile = File(...)):
    raw = (await file.read()).decode("utf-8")
    reader = csv.DictReader(io.StringIO(raw))
    rows = []
    for i, r in enumerate(reader):
        rows.append({
            "tx_id": f"tx-{i:05d}",
            "date": r.get("date", ""),
            "amount": float(r.get("amount", 0) or 0),
            "purpose": r.get("purpose", ""),
            "counterparty": r.get("counterparty", "").strip(),
        })

    texts = [f"{r['counterparty']} {r['purpose']}" for r in rows]
    vectors = await embed_texts(texts)

    q = get_qdrant()
    points = [
        {"id": r["tx_id"], "vector": v, "payload": r}
        for r, v in zip(rows, vectors)
    ]
    if points:
        await q.upsert(collection_name=COLL_BANK, points=points)
    return {"imported": len(points)}


@router.get("")
async def list_bank(limit: int = 200):
    q = get_qdrant()
    res, _ = await q.scroll(collection_name=COLL_BANK, limit=limit, with_payload=True)
    return {"items": [p.payload for p in res]}