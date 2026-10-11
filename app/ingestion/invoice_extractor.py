import json
import re
import uuid
from datetime import date

from app.core.llm.vllm_client import VLLMClient

SYSTEM = """You extract structured invoice fields from raw text.
Return ONLY a JSON object with keys:
  vendor, invoice_date (YYYY-MM-DD), amount_net, vat_rate, vat_amount,
  amount_gross, currency, category.
Numbers are floats. If a field is unknown, use null. Never add prose."""


async def extract_invoice(text: str) -> dict:
    llm = VLLMClient()
    raw = await llm.complete(SYSTEM, text[:4000], temperature=0.0)
    data = _safe_json(raw)
    data.setdefault("doc_id", uuid.uuid4().hex[:10])
    data.setdefault("currency", "EUR")
    data.setdefault("invoice_date", date.today().isoformat())
    data["raw_text"] = text[:2000]
    return data


def _safe_json(s: str) -> dict:
    m = re.search(r"\{.*\}", s, re.DOTALL)
    if not m:
        return {}
    try:
        return json.loads(m.group(0))
    except Exception:
        return {}