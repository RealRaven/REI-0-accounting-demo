from typing import AsyncIterator

from openai import AsyncOpenAI

from app.config import get_settings


class VLLMClient:
    """Thin wrapper over the OpenAI-compatible vLLM endpoint."""

    def __init__(self) -> None:
        s = get_settings()
        self._client = AsyncOpenAI(base_url=s.vllm_base_url, api_key=s.vllm_api_key)
        self._model = s.llm_model

    async def complete(self, system: str, user: str, temperature: float = 0.2) -> str:
        r = await self._client.chat.completions.create(
            model=self._model,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            temperature=temperature,
        )
        return r.choices[0].message.content or ""

    async def stream(self, system: str, user: str, temperature: float = 0.2) -> AsyncIterator[str]:
        stream = await self._client.chat.completions.create(
            model=self._model,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            temperature=temperature,
            stream=True,
        )
        async for chunk in stream:
            delta = chunk.choices[0].delta.content
            if delta:
                yield delta