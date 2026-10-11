from app.core.vector.search import dense_search

# per-intent weights; default is 1.0 for every collection
DEFAULT_WEIGHTS = {
    "invoices": 1.0,
    "bank_tx": 0.85,
    "law": 0.9,
    "tax_tips": 0.7,
    "documents": 0.8,
}


async def retrieve_collection(collection: str, query: str, k: int = 8) -> list[dict]:
    hits = await dense_search(collection, query, k=k)
    for h in hits:
        h["collection"] = collection
        h["weighted_score"] = h["score"] * DEFAULT_WEIGHTS.get(collection, 1.0)
    return hits


async def retrieve_multi(query: str, collections: list[str], k_each: int = 6) -> list[dict]:
    """Fan out across collections and merge with reciprocal rank fusion."""
    all_hits: list[dict] = []
    for coll in collections:
        hits = await retrieve_collection(coll, query, k=k_each)
        all_hits.extend(hits)

    # reciprocal rank fusion (weighted)
    by_id: dict[str, dict] = {}
    for rank, h in enumerate(all_hits):
        key = f"{h['collection']}:{h['id']}"
        if key not in by_id:
            by_id[key] = {**h, "rrf": 0.0}
        by_id[key]["rrf"] += h["weighted_score"] / (rank + 1)

    ranked = sorted(by_id.values(), key=lambda x: x["rrf"], reverse=True)
    return ranked