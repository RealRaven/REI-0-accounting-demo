from collections import defaultdict
from datetime import datetime

from rapidfuzz import fuzz


def rule_duplicate_charges(bank_tx: list[dict], invoices: list[dict]) -> list[dict]:
    """Flag exact-duplicate bank charges on the same date."""
    seen: dict[tuple, list[dict]] = defaultdict(list)
    for tx in bank_tx:
        if tx["amount"] >= 0:
            continue
        key = (tx.get("date"), tx.get("counterparty"), round(tx["amount"], 2))
        seen[key].append(tx)

    out = []
    for key, txs in seen.items():
        if len(txs) < 2:
            continue
        out.append({
            "kind": "duplicate_charge",
            "confidence": 0.9,
            "amount": abs(txs[0]["amount"]) * (len(txs) - 1),
            "vendor": txs[0].get("counterparty"),
            "evidence": [f"bank_tx#{t['tx_id']}" for t in txs],
            "suggestion": (
                f"{len(txs)} identical charges of {abs(txs[0]['amount']):.2f} "
                f"on {key[0]} — likely double-billed."
            ),
        })
    return out


def rule_uncategorized_recurring(bank_tx: list[dict], invoices: list[dict]) -> list[dict]:
    """Recurring bank charges with no matching invoice → possible forgotten sub."""
    invoice_vendors = [inv.get("vendor", "") for inv in invoices if inv.get("vendor")]
    invoice_amounts = {round(inv.get("amount_gross") or 0, 2) for inv in invoices}

    # group by counterparty
    by_vendor: dict[str, list[dict]] = defaultdict(list)
    for tx in bank_tx:
        if tx["amount"] < 0:
            by_vendor[tx.get("counterparty", "")].append(tx)

    out = []
    for vendor, txs in by_vendor.items():
        if len(txs) < 2:
            continue
        has_invoice = any(
            fuzz.token_set_ratio(vendor.lower(), v.lower()) > 80 for v in invoice_vendors
        )
        matches_amount = any(round(abs(t["amount"]), 2) in invoice_amounts for t in txs)
        if has_invoice or matches_amount:
            continue
        total = sum(abs(t["amount"]) for t in txs)
        out.append({
            "kind": "uncategorized_recurring",
            "confidence": 0.7,
            "amount": round(total, 2),
            "vendor": vendor,
            "evidence": [f"bank_tx#{t['tx_id']}" for t in txs],
            "suggestion": (
                f"{len(txs)} recurring charges from '{vendor}' "
                f"(total {total:.2f} €) with no matching invoice."
            ),
        })
    return out


def rule_vat_not_claimed(invoices: list[dict]) -> list[dict]:
    """Invoices with VAT but flagged category suggesting no deduction."""
    out = []
    for inv in invoices:
        vat = inv.get("vat_amount") or 0
        if vat <= 0:
            continue
        if (inv.get("category") or "").lower() in {"private", "non-deductible"}:
            out.append({
                "kind": "vat_not_claimed",
                "confidence": 0.65,
                "amount": round(vat, 2),
                "vendor": inv.get("vendor"),
                "evidence": [f"invoice#{inv.get('doc_id')}"],
                "suggestion": (
                    f"Invoice shows {vat:.2f} € USt but category is "
                    f"'{inv.get('category')}'. Verify § 15 UStG claim."
                ),
            })
    return out


def run_all_rules(bank_tx: list[dict], invoices: list[dict]) -> list[dict]:
    findings: list[dict] = []
    findings += rule_duplicate_charges(bank_tx, invoices)
    findings += rule_uncategorized_recurring(bank_tx, invoices)
    findings += rule_vat_not_claimed(invoices)
    # stable sort by confidence desc
    findings.sort(key=lambda f: f["confidence"], reverse=True)
    return findings