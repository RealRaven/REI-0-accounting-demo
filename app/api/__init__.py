from functools import lru_cache

from qdrant_client import AsyncQdrantClient

from app.config import get_settings
from app.core.llm.vllm_client import VLLMClient


@lru_cache
def get_qdrant() -> AsyncQdrantClient:
    s = get_settings()
    return AsyncQdrantClient(url=s.qdrant_url, api_key=s.qdrant_api_key or None)


@lru_cache
def get_llm() -> VLLMClient:
    return VLLMClient()