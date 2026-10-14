import asyncio
import sys
import uuid
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from qdrant_client import AsyncQdrantClient

from app.config import get_settings
from app.core.vector.collections import COLL_TIPS
from app.ingestion.tax_tips_loader import embed_tips, read_tips_dir


async def main() -> None:
    s = get_settings()
    tips = read_tips_dir(s.tips_dir)
    if not tips:
        print(f"no tips found in {s.tips_dir}")
        return

    points = await embed_tips(tips)
    q = AsyncQdrantClient(url=s.qdrant_url, api_key=s.qdrant_api_key or None)
    await q.upsert(
        collection_name=COLL_TIPS,
        points=[
            {
                # Convert string slug into a valid, deterministic UUID for Qdrant
                "id": str(uuid.uuid5(uuid.NAMESPACE_DNS, str(pid))),
                "vector": v,
                "payload": p,
            }
            for pid, v, p in points
        ],
    )
    await q.close()
    print(f"indexed {len(points)} tax tips.")


if __name__ == "__main__":
    asyncio.run(main())