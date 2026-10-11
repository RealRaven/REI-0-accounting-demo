from typing import AsyncIterator

from app.core.rag.pipeline import answer_stream
from app.core.security.audit import record
from app.logging import log


class ChatService:
    async def stream(self, question: str, trace_id: str) -> AsyncIterator[dict]:
        tokens: list[str] = []
        chips: list[dict] = []
        try:
            async for ev in answer_stream(question):
                if ev["type"] == "token":
                    tokens.append(ev["data"])
                elif ev["type"] == "citations":
                    chips = ev["data"]
                yield ev
        finally:
            await record(trace_id, question, chips, "".join(tokens))
            log.info("chat_done", trace_id=trace_id, tokens=len(tokens))