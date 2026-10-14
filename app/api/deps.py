# app/api/deps.py
from typing import Annotated, AsyncIterator

import httpx
from fastapi import Depends
from openai import AsyncOpenAI
from qdrant_client import AsyncQdrantClient

from app.config import Settings, get_settings


SettingsDep = Annotated[Settings, Depends(get_settings)]


async def get_http_client() -> AsyncIterator[httpx.AsyncClient]:
    async with httpx.AsyncClient(timeout=60.0) as client:
        yield client


HttpClientDep = Annotated[httpx.AsyncClient, Depends(get_http_client)]


async def get_qdrant(settings: SettingsDep) -> AsyncIterator[AsyncQdrantClient]:
    client = AsyncQdrantClient(url=settings.qdrant_url)
    try:
        yield client
    finally:
        await client.close()


QdrantDep = Annotated[AsyncQdrantClient, Depends(get_qdrant)]


def get_llm(settings: SettingsDep) -> AsyncOpenAI:
    """Return an OpenAI-compatible client configured for local vLLM."""
    return AsyncOpenAI(
        base_url=settings.vllm_base_url,
        api_key=settings.vllm_api_key or "not-needed",
    )


LlmDep = Annotated[AsyncOpenAI, Depends(get_llm)]