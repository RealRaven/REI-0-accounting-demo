def format_citation(hit: dict) -> str:
    coll = hit.get("collection", "")
    p = hit.get("payload", {})
    if coll == "invoices":
        return f"[invoice#{p.get('doc_id', '?')} p.{p.get('page', 1)}]"
    if coll == "bank_tx":
        return f"[bank_tx#{p.get('tx_id', hit['id'])}]"
    if coll == "law":
        return f"[{p.get('para', '§ ?')}, p.{p.get('page', 1)}]"
    if coll == "tax_tips":
        return f"[tip#{p.get('id', '?')}]"
    if coll == "documents":
        return f"[doc#{p.get('doc_id', '?')} p.{p.get('page', 1)}]"
    return f"[{coll}#{hit['id']}]"


def build_context(hits: list[dict], max_chars: int = 16000) -> tuple[str, list[dict]]:
    """Build a context block + a list of citation chips for the UI."""
    parts: list[str] = []
    chips: list[dict] = []
    used = 0
    for h in hits:
        p = h.get("payload", {})
        text = p.get("text") or _render_payload(h)
        cite = format_citation(h)
        chunk = f"{cite}\n{text}"
        if used + len(chunk) > max_chars:
            break
        parts.append(chunk)
        used += len(chunk)
        chips.append({"cite": cite, "id": h["id"], "collection": h.get("collection")})
    return "\n\n---\n\n".join(parts), chips


def _render_payload(hit: dict) -> str:
    p = hit.get("payload", {})
    coll = hit.get("collection")
    if coll == "invoices":
        return (
            f"Vendor: {p.get('vendor')} | Date: {p.get('invoice_date')} | "
            f"Net: {p.get('amount_net')} | VAT: {p.get('vat_rate')}% "
            f"({p.get('vat_amount')}) | Gross: {p.get('amount_gross')} | "
            f"Category: {p.get('category')}"
        )
    if coll == "bank_tx":
        return (
            f"Date: {p.get('date')} | Amount: {p.get('amount')} | "
            f"Counterparty: {p.get('counterparty')} | Purpose: {p.get('purpose')}"
        )
    return str(p)