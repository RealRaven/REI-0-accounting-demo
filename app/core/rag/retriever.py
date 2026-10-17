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


async def retrieve_multi(query: str, collections: list[str], k_each: int = 8) -> list[dict]:
    """Fan out across collections and merge with reciprocal rank fusion."""
    all_hits: list[dict] = []
    
    for coll in collections:
        hits = await retrieve_collection(coll, query, k=k_each)
        # Calculate RRF per collection so one collection doesn't hog the ranks
        for rank, h in enumerate(hits):
            h["rrf"] = h["weighted_score"] / (rank + 1)
        all_hits.extend(hits)

    # Sort globally by the computed RRF score
    ranked = sorted(all_hits, key=lambda x: x["rrf"], reverse=True)
    return ranked