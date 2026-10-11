from typing import Iterable

import httpx

from app.config import get_settings


async def embed_texts(texts: Iterable[str]) -> list[list[float]]:
    """Call the vLLM /embeddings endpoint with the configured embedding model."""
    s = get_settings()
    texts = list(texts)
    if not texts:
        return []
    async with httpx.AsyncClient(timeout=60.0) as c:
        r = await c.post(
            f"{s.vllm_base_url}/embeddings",
            headers={"Authorization": f"Bearer {s.vllm_api_key}"},
            json={"model": s.embed_model, "input": texts},
        )
        r.raise_for_status()
        data = r.json()
    # sort by index to preserve order
    items = sorted(data["data"], key=lambda d: d["index"])
    return [d["embedding"] for d in items]


async def embed_one(text: str) -> list[float]:
    return (await embed_texts([text]))[0]