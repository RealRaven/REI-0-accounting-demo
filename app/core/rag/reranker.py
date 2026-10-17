def rerank(hits: list[dict], top_k: int = 12) -> list[dict]:
    """Placeholder: keep current ordering, truncate.

    Replace with a cross-encoder call (e.g. bge-reranker served via vLLM) if
    you need higher precision. The reciprocal-rank fusion in `retriever.py`
    already gives decent results for a demo.
    """
    return hits[:top_k]