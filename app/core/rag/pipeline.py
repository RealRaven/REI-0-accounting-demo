from typing import AsyncIterator

from app.core.llm.prompts import ACCOUNTANT_SYSTEM
from app.core.llm.vllm_client import VLLMClient
from app.core.rag.citations import build_context
from app.core.rag.reranker import rerank
from app.core.rag.retriever import retrieve_multi
from app.core.security.pii import mask_pii

ALL = ["invoices", "bank_tx", "law", "tax_tips", "documents"]


async def answer_stream(question: str, collections: list[str] | None = None) -> AsyncIterator[dict]:
    collections = collections or ALL
    hits = await retrieve_multi(question, collections, k_each=8)
    hits = rerank(hits, top_k=20)  # Increased from 12 to 20

    context, chips = build_context(hits, max_chars=16000)
    context = mask_pii(context)

    yield {"type": "citations", "data": chips}

    user_prompt = (
        f"CONTEXT:\n{context}\n\n"
        f"QUESTION: {question}\n\n"
        "Answer with inline citations. Be concise. If the context includes relevant law paragraphs, summarize them."
    )

    llm = VLLMClient()
    async for token in llm.stream(ACCOUNTANT_SYSTEM, user_prompt):
        yield {"type": "token", "data": token}


async def answer(question: str, collections: list[str] | None = None) -> dict:
    chunks: list[str] = []
    chips: list[dict] = []
    async for ev in answer_stream(question, collections):
        if ev["type"] == "token":
            chunks.append(ev["data"])
        elif ev["type"] == "citations":
            chips = ev["data"]
    return {"answer": "".join(chunks), "citations": chips}