import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.core.vector.collections import ensure_collections


async def main() -> None:
    await ensure_collections()
    print("collections ensured.")


if __name__ == "__main__":
    asyncio.run(main())