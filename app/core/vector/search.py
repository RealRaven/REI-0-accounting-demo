from qdrant_client import AsyncQdrantClient
from qdrant_client.models import Filter

from app.config import get_settings
from app.core.llm.embeddings import embed_one


async def dense_search(
    collection: str,
    query: str,
    k: int = 8,
    flt: Filter | None = None,
) -> list[dict]:
    s = get_settings()
    q = AsyncQdrantClient(url=s.qdrant_url, api_key=s.qdrant_api_key or None)
    vec = await embed_one(query)
    
    # Updated from q.search(...) to q.query_points(...)
    response = await q.query_points(
        collection_name=collection,
        query=vec,          # Parameter changed from query_vector to query
        limit=k,
        query_filter=flt,
        with_payload=True,
    )
    await q.close()
    
    # Extract the points list from the response object
    hits = response.points
    
    return [
        {"id": str(h.id), "score": h.score, "payload": h.payload or {}}
        for h in hits
        if h.score >= s.rag_min_score
    ]