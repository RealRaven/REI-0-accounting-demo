import hashlib
import json

from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

from app.config import get_settings

_engine = create_async_engine(get_settings().database_url, pool_pre_ping=True)


async def record(trace_id: str, question: str, retrieved: list[dict], answer: str) -> None:
    try:
        h = hashlib.sha256(answer.encode("utf-8")).hexdigest()[:16]
        async with _engine.begin() as conn:
            await conn.execute(
                text(
                    "INSERT INTO audit (trace_id, question, retrieved, answer_hash) "
                    "VALUES (:t, :q, CAST(:r AS JSONB), :h)"
                ),
                {"t": trace_id, "q": question, "r": json.dumps(retrieved, default=str), "h": h},
            )
    except Exception:
        # audit must never break the request
        pass