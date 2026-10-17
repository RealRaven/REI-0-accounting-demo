# app/services/matching_service.py
from rapidfuzz import fuzz


def match_invoice(tx: dict, invoices: list[dict]) -> str | None:
    """Return doc_id of best matching invoice for a bank tx, or None."""
    best, best_score = None, 0.0
    for inv in invoices:
        if round(abs(tx.get("amount", 0)), 2) != round(inv.get("amount_gross") or 0, 2):
            continue
        v_score = fuzz.token_set_ratio(
            (tx.get("counterparty") or "").lower(),
            (inv.get("vendor") or "").lower(),
        )
        if v_score > best_score:
            best_score, best = v_score, inv.get("doc_id")
    return best if best_score > 70 else None