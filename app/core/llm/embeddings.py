import asyncio
from typing import Iterable

from sentence_transformers import SentenceTransformer

from app.config import get_settings

_model = None

def get_model() -> SentenceTransformer:
    global _model
    if _model is None:
        s = get_settings()
        print(f"Loading embedding model {s.embed_model} on CPU...")
        _model = SentenceTransformer(s.embed_model, device="cpu")
        print("Embedding model loaded!")
    return _model

def _embed_sync(texts: list[str]) -> list[list[float]]:
    model = get_model()
    embeddings = model.encode(texts, normalize_embeddings=True, batch_size=16)
    return embeddings.tolist()

async def embed_texts(texts: Iterable[str]) -> list[list[float]]:
    texts = list(texts)
    if not texts:
        return []
    return await asyncio.to_thread(_embed_sync, texts)

async def embed_one(text: str) -> list[float]:
    return (await embed_texts([text]))[0]