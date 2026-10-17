CREATE TABLE IF NOT EXISTS invoices (
    id           BIGSERIAL PRIMARY KEY,
    doc_id       TEXT UNIQUE NOT NULL,
    vendor       TEXT,
    invoice_date DATE,
    amount_net   NUMERIC(12,2),
    vat_rate     NUMERIC(5,2),
    vat_amount   NUMERIC(12,2),
    amount_gross NUMERIC(12,2),
    currency     TEXT DEFAULT 'EUR',
    category     TEXT,
    pdf_path     TEXT,
    raw_text     TEXT,
    created_at   TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE IF NOT EXISTS bank_tx (
    id           BIGSERIAL PRIMARY KEY,
    iban         TEXT,
    tx_date      DATE,
    amount       NUMERIC(12,2),
    purpose      TEXT,
    counterparty TEXT,
    matched_invoice_doc_id TEXT,
    raw          JSONB,
    created_at   TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE IF NOT EXISTS hidden_costs (
    id           BIGSERIAL PRIMARY KEY,
    kind         TEXT NOT NULL,
    confidence   NUMERIC(4,3),
    amount       NUMERIC(12,2),
    vendor       TEXT,
    evidence     JSONB,
    suggestion   TEXT,
    created_at   TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE IF NOT EXISTS audit (
    id           BIGSERIAL PRIMARY KEY,
    trace_id     TEXT NOT NULL,
    question     TEXT,
    retrieved    JSONB,
    answer_hash  TEXT,
    created_at   TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_bank_tx_date ON bank_tx(tx_date);
CREATE INDEX IF NOT EXISTS idx_invoices_vendor ON invoices(vendor);
CREATE INDEX IF NOT EXISTS idx_audit_trace ON audit(trace_id);