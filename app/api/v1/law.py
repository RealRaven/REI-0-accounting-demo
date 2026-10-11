from fastapi import APIRouter, Query

from app.core.rag.retriever import retrieve_collection
from app.core.vector.collections import COLL_LAW

router = APIRouter()


@router.get("/search")
async def search_law(q: str = Query(..., min_length=2), k: int = 5):
    hits = await retrieve_collection(COLL_LAW, q, k=k)
    return {"query": q, "items": hits}