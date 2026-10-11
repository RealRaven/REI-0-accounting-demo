from fastapi import APIRouter, Query
from qdrant_client.models import FieldCondition, Filter, MatchValue

from app.api.deps import get_qdrant
from app.core.vector.collections import COLL_TIPS

router = APIRouter()


@router.get("")
async def list_tips(
    branch: str | None = Query(None),
    year: int | None = Query(None),
    limit: int = 50,
):
    must = []
    if branch:
        must.append(FieldCondition(key="branch", match=MatchValue(value=branch)))
    if year:
        must.append(FieldCondition(key="year", match=MatchValue(value=year)))

    flt = Filter(must=must) if must else None
    res, _ = await get_qdrant().scroll(
        collection_name=COLL_TIPS, limit=limit, with_payload=True, scroll_filter=flt,
    )
    return {"items": [p.payload for p in res]}