import httpx
from typing import Iterable
from app.config import get_settings


async def embed_texts(texts: Iterable[str]) -> list[list[float]]:
    """Offload embedding generation via HTTP to the vllm-embed GPU container."""
    texts_list = list(texts)
    if not texts_list:
        return []
    
    s = get_settings()
    all_embeddings = []
    batch_size = 64  # Safe batch size for sending to the GPU container
    
    async with httpx.AsyncClient(timeout=120.0) as client:
        for i in range(0, len(texts_list), batch_size):
            batch = texts_list[i:i + batch_size]
            
            response = await client.post(
                f"{s.embed_base_url}/embeddings",
                json={
                    "model": s.embed_model,
                    "input": batch
                }
            )
            response.raise_for_status()
            data = response.json()
            
            # Sort by index to guarantee correct ordering
            sorted_data = sorted(data["data"], key=lambda x: x["index"])
            all_embeddings.extend([item["embedding"] for item in sorted_data])
            
    return all_embeddings


async def embed_one(text: str) -> list[float]:
    res = await embed_texts([text])
    return res[0] if res else []