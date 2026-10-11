from sqlalchemy import JSON, Column, Date, Integer, Numeric, String, Text
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class Invoice(Base):
    __tablename__ = "invoices"
    id = Column(Integer, primary_key=True)
    doc_id = Column(String, unique=True, nullable=False)
    vendor = Column(String)
    invoice_date = Column(Date)
    amount_net = Column(Numeric(12, 2))
    vat_rate = Column(Numeric(5, 2))
    vat_amount = Column(Numeric(12, 2))
    amount_gross = Column(Numeric(12, 2))
    currency = Column(String, default="EUR")
    category = Column(String)
    pdf_path = Column(Text)
    raw_text = Column(Text)


class BankTx(Base):
    __tablename__ = "bank_tx"
    id = Column(Integer, primary_key=True)
    iban = Column(String)
    tx_date = Column(Date)
    amount = Column(Numeric(12, 2))
    purpose = Column(Text)
    counterparty = Column(String)
    matched_invoice_doc_id = Column(String)
    raw = Column(JSON)