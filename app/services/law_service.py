from app.core.rag.retriever import retrieve_collection
from app.core.vector.collections import COLL_LAW


class LawService:
    async def search(self, query: str, k: int = 5) -> list[dict]:
        return await retrieve_collection(COLL_LAW, query, k=k)