import pytest

from app.core.rag.chunking import chunk_text
from app.core.rag.retriever import retrieve_multi


def test_chunk_text_respects_max_chars():
    text = "para one.\n\n" * 200
    chunks = chunk_text(text, max_chars=500)
    for c in chunks:
        assert len(c) <= 520


@pytest.mark.asyncio
async def test_retrieve_multi_empty_collections(monkeypatch):
    async def fake(coll, q, k=8):
        return []

    monkeypatch.setattr("app.core.rag.retriever.retrieve_collection", fake)
    hits = await retrieve_multi("anything", ["invoices", "law"])
    assert hits == []