import csv
from pathlib import Path


def read_bank_csv(path: str | Path) -> list[dict]:
    out = []
    with Path(path).open("r", encoding="utf-8") as f:
        for i, row in enumerate(csv.DictReader(f)):
            out.append({
                "tx_id": f"tx-{i:05d}",
                "date": row.get("date", ""),
                "amount": float(row.get("amount", 0) or 0),
                "purpose": row.get("purpose", ""),
                "counterparty": (row.get("counterparty") or "").strip(),
            })
    return out