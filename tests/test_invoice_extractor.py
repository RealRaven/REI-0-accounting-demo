from app.ingestion.invoice_extractor import _safe_json


def test_safe_json_extracts_object():
    s = 'blah blah {"vendor": "Acme", "amount_gross": 12.5} trailing'
    assert _safe_json(s)["vendor"] == "Acme"


def test_safe_json_returns_empty_on_garbage():
    assert _safe_json("no json here") == {}