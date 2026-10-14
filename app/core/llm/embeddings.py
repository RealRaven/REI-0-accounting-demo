from typing import Iterable
from sentence_transformers import SentenceTransformer
from app.config import get_settings

_model = None

def _get_model():
    global _model
    if _model is None:
        s = get_settings()
        # Loads BAAI/bge-m3 locally using sentence-transformers
        _model = SentenceTransformer(s.embed_model)
    return _model

async def embed_texts(texts: Iterable[str]) -> list[list[float]]:
    """Generate embeddings locally using sentence-transformers."""
    texts = list(texts)
    if not texts:
        return []
    model = _get_model()
    # Encode texts locally
    embeddings = model.encode(texts, normalize_embeddings=True)
    return embeddings.tolist()

async def embed_one(text: str) -> list[float]:
    return (await embed_texts([text]))[0]