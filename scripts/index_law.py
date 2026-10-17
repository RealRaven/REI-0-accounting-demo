import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from qdrant_client import AsyncQdrantClient

from app.config import get_settings
from app.core.vector.collections import COLL_LAW
from app.ingestion.law_pdf_loader import embed_law_chunks, load_law_pdf


async def main() -> None:
    s = get_settings()
    law_dir = Path(s.law_dir)
    if not law_dir.exists():
        print(f"no law dir at {law_dir}; skipping.")
        return

    files = list(law_dir.glob("*.pdf"))
    if not files:
        print(f"no PDFs in {law_dir}; skipping.")
        return

    q = AsyncQdrantClient(url=s.qdrant_url, api_key=s.qdrant_api_key or None)
    total = 0
    for f in files:
        chunks = await load_law_pdf(f)
        points = await embed_law_chunks(chunks)
        if points:
            await q.upsert(
                collection_name=COLL_LAW,
                points=[{"id": pid, "vector": v, "payload": p} for pid, v, p in points],
            )
        total += len(points)
        print(f"indexed {f.name}: {len(points)} chunks")
    await q.close()
    print(f"law index complete: {total} chunks.")


if __name__ == "__main__":
    asyncio.run(main())