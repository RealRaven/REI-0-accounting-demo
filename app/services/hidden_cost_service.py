from qdrant_client import AsyncQdrantClient

from app.config import get_settings
from app.core.vector.collections import COLL_BANK, COLL_INVOICES
from app.domain.rules.hidden_cost_rules import run_all_rules


class HiddenCostService:
    async def _fetch(self, collection: str, limit: int = 500) -> list[dict]:
        s = get_settings()
        q = AsyncQdrantClient(url=s.qdrant_url, api_key=s.qdrant_api_key or None)
        res, _ = await q.scroll(collection_name=collection, limit=limit, with_payload=True)
        await q.close()
        return [p.payload or {} for p in res]

    async def find_all(self) -> list[dict]:
        invoices = await self._fetch(COLL_INVOICES)
        bank = await self._fetch(COLL_BANK)
        return run_all_rules(bank, invoices)