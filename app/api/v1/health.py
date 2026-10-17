import httpx
from fastapi import APIRouter
from qdrant_client import AsyncQdrantClient

from app.api.deps import get_llm, get_qdrant
from app.config import get_settings

router = APIRouter()


@router.get("/vllm")
async def health_vllm():
    s = get_settings()
    try:
        async with httpx.AsyncClient(timeout=5.0) as c:
            r = await c.get(f"{s.vllm_base_url}/models")
            return {"ok": r.status_code == 200, "status": r.status_code}
    except Exception as e:
        return {"ok": False, "error": str(e)}


@router.get("/qdrant")
async def health_qdrant():
    q: AsyncQdrantClient = get_qdrant()
    try:
        cols = await q.get_collections()
        return {"ok": True, "collections": [c.name for c in cols.collections]}
    except Exception as e:
        return {"ok": False, "error": str(e)}