from qdrant_client import AsyncQdrantClient
from qdrant_client.models import Filter

from app.config import get_settings
from app.core.llm.embeddings import embed_one


async def dense_search(
    collection: str,
    query: str,
    k: int = 8,
    flt: Filter | None = None,
    min_score: float | None = None,
) -> list[dict]:
    s = get_settings()
    q = AsyncQdrantClient(url=s.qdrant_url, api_key=s.qdrant_api_key or None)
    vec = await embed_one(query)
    
    threshold = min_score if min_score is not None else s.rag_min_score
    
    # Use the new query_points API
    result = await q.query_points(
        collection_name=collection,
        query=vec,
        limit=k,
        query_filter=flt,
        with_payload=True,
    )
    await q.close()
    
    return [
        {"id": str(h.id), "score": h.score, "payload": h.payload or {}}
        for h in result.points
        if h.score >= threshold
    ]