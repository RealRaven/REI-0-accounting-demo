import asyncio
import csv
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from qdrant_client import AsyncQdrantClient

from app.config import get_settings
from app.core.llm.embeddings import embed_texts
from app.core.vector.collections import COLL_BANK, COLL_INVOICES

ROOT = Path(__file__).resolve().parents[1]
FIX = ROOT / "data" / "fixtures"


async def main() -> None:
    s = get_settings()
    q = AsyncQdrantClient(url=s.qdrant_url, api_key=s.qdrant_api_key or None)

    invoices = json.loads((FIX / "invoices.json").read_text(encoding="utf-8"))
    inv_texts = [
        f"{i.get('vendor')} {i.get('category')} {i.get('invoice_date')} {i.get('amount_gross')}"
        for i in invoices
    ]
    inv_vecs = await embed_texts(inv_texts)
    if invoices:
        await q.upsert(
            collection_name=COLL_INVOICES,
            points=[
                {"id": i["doc_id"], "vector": v, "payload": i}
                for i, v in zip(invoices, inv_vecs)
            ],
        )

    bank_rows = []
    with (FIX / "bank_2024.csv").open("r", encoding="utf-8") as f:
        for i, row in enumerate(csv.DictReader(f)):
            bank_rows.append({
                "tx_id": f"tx-{i:05d}",
                "date": row["date"],
                "amount": float(row["amount"]),
                "purpose": row["purpose"].strip(),
                "counterparty": row["counterparty"].strip(),
            })
    bank_texts = [f"{r['counterparty']} {r['purpose']}" for r in bank_rows]
    bank_vecs = await embed_texts(bank_texts)
    if bank_rows:
        await q.upsert(
            collection_name=COLL_BANK,
            points=[
                {"id": r["tx_id"], "vector": v, "payload": r}
                for r, v in zip(bank_rows, bank_vecs)
            ],
        )

    await q.close()
    print(f"fixtures indexed: {len(invoices)} invoices, {len(bank_rows)} bank tx.")


if __name__ == "__main__":
    asyncio.run(main())