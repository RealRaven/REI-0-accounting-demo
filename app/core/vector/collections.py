from qdrant_client import AsyncQdrantClient
from qdrant_client.models import Distance, PayloadSchemaType, VectorParams

from app.config import get_settings

COLL_INVOICES = "invoices"
COLL_BANK = "bank_tx"
COLL_LAW = "law"
COLL_TIPS = "tax_tips"
COLL_DOCS = "documents"

ALL_COLLECTIONS = [COLL_INVOICES, COLL_BANK, COLL_LAW, COLL_TIPS, COLL_DOCS]


async def ensure_collections() -> None:
    s = get_settings()
    q = AsyncQdrantClient(url=s.qdrant_url, api_key=s.qdrant_api_key or None)
    existing = {c.name for c in (await q.get_collections()).collections}

    for name in ALL_COLLECTIONS:
        if name not in existing:
            await q.create_collection(
                collection_name=name,
                vectors_config=VectorParams(size=s.embed_dim, distance=Distance.COSINE),
            )

    # payload indexes (idempotent — ignore errors if they already exist)
    async def _idx(coll: str, field: str, schema: PayloadSchemaType) -> None:
        try:
            await q.create_payload_index(coll, field_name=field, field_schema=schema)
        except Exception:
            pass

    await _idx(COLL_INVOICES, "vendor", PayloadSchemaType.KEYWORD)
    await _idx(COLL_INVOICES, "category", PayloadSchemaType.KEYWORD)
    await _idx(COLL_INVOICES, "invoice_date", PayloadSchemaType.KEYWORD)
    await _idx(COLL_BANK, "counterparty", PayloadSchemaType.KEYWORD)
    await _idx(COLL_BANK, "date", PayloadSchemaType.KEYWORD)
    await _idx(COLL_LAW, "law", PayloadSchemaType.KEYWORD)
    await _idx(COLL_LAW, "para", PayloadSchemaType.KEYWORD)
    await _idx(COLL_TIPS, "branch", PayloadSchemaType.KEYWORD)
    await _idx(COLL_TIPS, "year", PayloadSchemaType.INTEGER)

    await q.close()