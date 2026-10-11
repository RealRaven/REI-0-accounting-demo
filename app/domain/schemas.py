# app/domain/models.py
from pydantic import BaseModel


class Invoice(BaseModel):
    doc_id: str
    vendor: str | None = None
    invoice_date: str | None = None
    amount_net: float | None = None
    vat_rate: float | None = None
    vat_amount: float | None = None
    amount_gross: float | None = None
    currency: str = "EUR"
    category: str | None = None


class BankTx(BaseModel):
    tx_id: str
    date: str | None = None
    amount: float
    purpose: str | None = None
    counterparty: str | None = None


class HiddenCost(BaseModel):
    kind: str
    confidence: float
    amount: float
    vendor: str | None = None
    evidence: list[str] = []
    suggestion: str = ""