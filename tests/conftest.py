import os

os.environ.setdefault("VLLM_BASE_URL", "http://localhost:1/v1")
os.environ.setdefault("QDRANT_URL", "http://localhost:1")


import pytest


@pytest.fixture
def sample_invoice():
    return {
        "doc_id": "inv-001",
        "vendor": "Figma",
        "invoice_date": "2024-09-14",
        "amount_net": 66.39,
        "vat_rate": 19,
        "vat_amount": 12.61,
        "amount_gross": 79.00,
        "category": "software",
    }


@pytest.fixture
def sample_bank():
    return [
        {"tx_id": "tx-1", "date": "2024-09-14", "amount": -79.00,
         "counterparty": "Figma", "purpose": "FIGMA MONTHLY"},
        {"tx_id": "tx-2", "date": "2024-09-14", "amount": -79.00,
         "counterparty": "Figma", "purpose": "FIGMA MONTHLY"},
        {"tx_id": "tx-3", "date": "2024-09-30", "amount": -19.99,
         "counterparty": "Adobe", "purpose": "ADOBE MONTHLY"},
        {"tx_id": "tx-4", "date": "2024-10-05", "amount": -12.99,
         "counterparty": "Spotify", "purpose": "Spotify Premium"},
    ]