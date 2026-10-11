# REI-0-accounting-demo

> An offline, self-hosted accounting assistant that reads your invoices, watches your bank feed, chats with your books via RAG, finds hidden costs, and cites the actual tax law PDF at the exact page.

Everything runs **locally**. No OpenAI. No cloud. Just `vLLM` for the LLM, `Qdrant` for the vector DB, `Postgres` for the ledger, and your own PDFs of EStG/UStG/AO on disk.

---

## What it does

- **Reads invoices & documents** — drops a PDF in, OCRs it, extracts structured fields (vendor, date, amount, VAT, category) with a local LLM, and stores it in Qdrant + Postgres.
- **Watches banking** — imports CSV / CAMT / MT940 exports and matches every bank transaction against an invoice (fuzzy on amount + date + vendor).
- **Chats with your books** — a chat window backed by RAG across *all* local collections (invoices, bank, law, tax tips, documents). Answers come back with citations like `[invoice#42 p.1]` or `[§ 15 UStG]`.
- **Finds hidden costs** — deterministic rules + a RAG pass spot duplicate vendors, fee creep, unclaimed Vorsteuer, forgotten Werbungskosten, subscriptions nobody remembers signing up for.
- **Tax tips DB** — curated tips per branch / year / §, retrievable alongside the law.
- **PDF connection to the law** — the actual law PDFs (EStG, UStG, AO) are chunked by `§`/`Absatz` and stored with `pdf_path` + `page`, so clicking a citation jumps straight into the statute.

---

## Architecture (30 seconds)

```
       ┌──────────────┐        ┌──────────────┐
       │  Invoices    │        │  Bank feed   │
       │  PDFs/OCR    │        │  CSV/CAMT    │
       └──────┬───────┘        └──────┬───────┘
              │                       │
              ▼                       ▼
      ┌────────────────────────────────────┐
      │     Ingestion + Extraction         │
      │  (pypdf → LLM struct. output)      │
      └────────────────┬───────────────────┘
                       │
        ┌──────────────┼──────────────┬──────────────┐
        ▼              ▼              ▼              ▼
   ┌─────────┐   ┌──────────┐   ┌─────────┐   ┌───────────┐
   │ Qdrant  │   │ Qdrant   │   │ Qdrant  │   │  Qdrant   │
   │invoices │   │ bank_tx  │   │  law    │   │tax_tips   │
   └────┬────┘   └────┬─────┘   └────┬────┘   └─────┬─────┘
        └─────────────┴──────┬───────┴──────────────┘
                             ▼
                    ┌──────────────────┐      ┌─────────────┐
                    │   RAG pipeline   │◄────►│    vLLM     │
                    │ retrieve→rerank  │      │ (local LLM) │
                    │ →generate→cite   │      └─────────────┘
                    └────────┬─────────┘
                             ▼
                    ┌──────────────────┐
                    │  Chat UI / SSE   │
                    │  + Hidden costs  │
                    └──────────────────┘
```

- **LLM** — `vLLM` serving any OpenAI-compatible model (default: `Qwen2.5-7B-Instruct`).
- **Embeddings** — `bge-m3` served from the same vLLM `/embeddings` endpoint.
- **Vector DB** — `Qdrant` with one collection per domain, hybrid dense + payload filters.
- **Relational** — `Postgres` for invoices, bank rows, matches, audit log.
- **Workers** — `Celery` + `Redis` for ingestion, embedding, nightly reconcile.

---

## Quickstart

Three commands. That's it.

```bash
make up      # vllm + qdrant + postgres + redis + app + ui
make seed    # index fixtures, law PDFs, tax tips
make demo    # opens http://localhost:8000/ui/chat.html
```

First run will pull the model (~15 GB) and the embedding model. Subsequent starts are fast.

### Manual (no make)

```bash
cp .env.example .env               # set VLLM_BASE_URL, QDRANT_URL, etc.
docker compose up -d vllm qdrant postgres redis
python scripts/seed_qdrant.py      # create collections + payload indexes
python scripts/index_law.py        # data/law/*.pdf → qdrant:law
python scripts/index_tax_tips.py   # data/tax_tips/*.yaml → qdrant:tax_tips
python scripts/index_fixtures.py   # demo invoices + bank csv
uvicorn app.main:app --reload      # http://localhost:8000
```

---

## Requirements

| Component | Minimum | Notes |
|---|---|---|
| GPU | 12 GB VRAM | for Qwen2.5-7B-Instruct in bf16; 8 GB works with a 4-bit quant |
| RAM | 16 GB | |
| Disk | 40 GB | model weights + law PDFs + vector store |
| Docker | 24+ | with `nvidia-container-toolkit` |
| Python | 3.11+ | if running outside Docker |

No GPU? Swap the vLLM service for `llama.cpp` in `docker-compose.yml` and point `VLLM_BASE_URL` at it — everything else works unchanged.

---

## Configuration

All settings live in `.env`:

```dotenv
# LLM
VLLM_BASE_URL=http://vllm:8001/v1
VLLM_API_KEY=not-needed
LLM_MODEL=Qwen/Qwen2.5-7B-Instruct
EMBED_MODEL=BAAI/bge-m3

# Vector DB
QDRANT_URL=http://qdrant:6333
QDRANT_API_KEY=

# Relational
DATABASE_URL=postgresql+asyncpg://rei:rei@postgres:5432/rei

# Ingestion
INBOX_DIR=./data/inbox
PROCESSED_DIR=./data/processed
OCR_ENABLED=true
PII_MASK=true          # mask IBANs / tax IDs before they hit the LLM

# Retrieval
RAG_TOP_K=12
RAG_RERANK=true
RAG_MIN_SCORE=0.35
```

---

## Using it

### 1. Drop documents in the inbox

```bash
cp ~/Downloads/rechnung_2024_03.pdf data/inbox/
```

The watcher picks it up, OCRs if needed, extracts fields, and files it into `data/processed/2024-03_acme_1290.00.pdf`.

### 2. Import a bank statement

```bash
curl -F "file=@data/banking/konto_2024.csv" http://localhost:8000/api/v1/banking/import
```

Every row is inserted as a `BankTx`. Matching against invoices runs automatically and again nightly.

### 3. Chat with your books

Open `http://localhost:8000/ui/chat.html`.

> **You:** How much did I spend on software subscriptions last quarter, and is any of it deductible?
>
> **REI-0:** €1,842 across 14 transactions — mostly JetBrains (€684) and Figma (€468). Under § 4 Abs. 4 EStG these are Betriebsausgaben; the Figma charge on 2024-09-14 looks like a duplicate (`[invoice#87 p.1]`, `[bank_tx#4421]`). Your accountant may want the €79 back. See `[§ 4 EStG, p.12]` and tip `[software-subscriptions]`.

Every answer carries **citations**. Click a citation chip:

- `[invoice#87 p.1]` → opens the invoice PDF at page 1.
- `[§ 4 EStG, p.12]` → opens the law PDF at page 12.
- `[tip#software-subscriptions]` → opens the tip card.

### 4. Look for hidden costs

Open `/ui/hidden_costs.html` or:

```bash
curl http://localhost:8000/api/v1/hidden-costs
```

You'll get a list like:

```json
[
  {
    "kind": "duplicate_charge",
    "confidence": 0.93,
    "amount": 79.00,
    "vendor": "Figma",
    "evidence": ["bank_tx#4421", "bank_tx#4388"],
    "suggestion": "Two identical charges on 2024-09-14. Likely double-billed."
  },
  {
    "kind": "vat_not_claimed",
    "confidence": 0.81,
    "amount": 214.30,
    "evidence": ["invoice#112 p.1"],
    "suggestion": "Invoice shows 19% USt but no Vorsteuer claim recorded. § 15 UStG."
  }
]
```

### 5. Search the law directly

```bash
curl "http://localhost:8000/api/v1/law/search?q=%C2%A7%2015%20UStG%20Vorsteuer"
```

Returns the exact `§` chunk, its `pdf_path`, and the `page` to open.

---

## API surface (v1)

| Method | Path | Purpose |
|---|---|---|
| `POST` | `/api/v1/chat` | SSE stream; RAG over all collections |
| `POST` | `/api/v1/invoices/upload` | upload + extract |
| `GET`  | `/api/v1/invoices` | list / filter |
| `POST` | `/api/v1/banking/import` | CSV/CAMT upload |
| `GET`  | `/api/v1/banking` | list transactions |
| `POST` | `/api/v1/documents/upload` | generic doc → chunk → embed |
| `GET`  | `/api/v1/hidden-costs` | rule + RAG findings |
| `GET`  | `/api/v1/tax-tips` | filter by `branch`, `year`, `§` |
| `GET`  | `/api/v1/law/search` | § lookup with PDF pointers |
| `GET`  | `/api/v1/health/vllm` | is the LLM alive? |
| `GET`  | `/api/v1/health/qdrant` | are the collections ready? |

Full OpenAPI at `http://localhost:8000/docs`.

---

## Qdrant collections

| Collection  | Payload filters                                        | Fed by |
|-------------|--------------------------------------------------------|--------|
| `invoices`  | `vendor, date, amount, vat, category, doc_id, page`    | `data/processed/` |
| `bank_tx`   | `iban, date, amount, purpose, matched_invoice`         | `data/banking/` |
| `law`       | `law, §, Absatz, page, pdf_path`                       | `data/law/*.pdf` |
| `tax_tips`  | `branch, year, §_ref, deductibility`                   | `data/tax_tips/` |
| `documents` | `doc_id, page, mime, source`                           | `data/inbox/` |

Hybrid search: dense (bge-m3) + payload filters + optional BM25 side-index. A reciprocal-rank-fusion reranker merges the per-collection result lists before stuffing the context window.

---

## How the RAG pipeline works

```
query
  │
  ├─► classify intent (books? law? tips? mixed?)
  │
  ├─► fan out to N collections with per-intent weights
  │     invoices:1.0  bank:0.8  law:0.9  tips:0.6
  │
  ├─► per-collection top-K  (dense + payload filters)
  │
  ├─► reciprocal-rank fusion  →  top-K global
  │
  ├─► (optional) cross-encoder rerank  (bge-reranker)
  │
  ├─► PII masking on retrieved chunks before prompt assembly
  │
  ├─► prompt: system(accountant) + retrieved chunks + question
  │
  ├─► vLLM generate (streamed)
  │
  └─► citation post-processing → SSE tokens + citation chips
```

Every request writes a row to the `audit` table: `trace_id, question, retrieved doc ids, answer hash`. Compliance people love this.

---

## Repo layout

```
REI-0-accounting-demo/
├── app/           # FastAPI, RAG, ingestion, services, domain rules
├── ui/            # optional Vite + React frontend (chat, hidden costs)
├── workers/       # Celery tasks: ingest, embed, reconcile
├── scripts/       # seed, index law, index tips, demo run
├── data/          # inbox / processed / banking / law / tax_tips / fixtures
├── docker/        # vLLM, Qdrant, Postgres configs
├── tests/
├── docker-compose.yml
└── Makefile
```

See `README_ARCHITECTURE.md` for the full tree.

---

## Demo data

`data/fixtures/` ships with:

- 24 fake invoices (German vendors, EUR, mixed 7% / 19% VAT)
- 1 bank CSV with 60 transactions, ~6 of which have no matching invoice (the "hidden costs")
- Excerpts of EStG §§ 4, 9, 15 and UStG §§ 2, 15 as real PDFs
- 12 tax tips across `IT`, `Handwerk`, `Gastronomie`

So `make demo` always has something to show, even with no real data.

---

## Extending it

- **Add a document type** — drop a parser in `app/ingestion/`, register it, and add a Qdrant collection in `app/core/vector/collections.py`.
- **Add a hidden-cost rule** — one function in `app/domain/rules/hidden_cost_rules.py`. Return `HiddenCost` objects. Rules run alongside the RAG pass.
- **Add a tax tip** — append a YAML file to `data/tax_tips/` and run `python scripts/index_tax_tips.py`. It's searchable immediately.
- **Swap the LLM** — change `LLM_MODEL` in `.env`. Anything OpenAI-compatible works. vLLM, llama.cpp, TGI, Ollama — pick your poison.
- **Add a language** — the prompts and the tax-tip YAMLs are language-tagged. Copy `prompts.py` and `data/tax_tips/de/` to a new locale.

---

## Limitations & honesty

- This is a **demo**, not a tax advisor. It cites the law; it does not replace one. The `deductibility` field is a suggestion, not legal advice.
- The hidden-cost detector is deliberately conservative. It will miss things. It will occasionally flag something that's fine. That's why every finding carries `confidence` and `evidence`.
- OCR quality on scanned invoices depends on `tesseract` + the source scan. Garbage in, garbage out.
- RAG citations are only as good as the law PDFs you feed it. Use official, current versions. The demo ships with **excerpts**, not the full statutes.
- The audit log is append-only but not cryptographically signed. If you need that, wrap `audit_repo.py`.

---

## Testing

```bash
pytest                          # everything
pytest tests/test_rag_pipeline.py -v
pytest -k hidden_cost           # just the rules
```

`conftest.py` spins up an **ephemeral Qdrant** in-memory and a fake LLM that returns deterministic strings, so the suite runs on CI without a GPU.

---

## License

MIT — see `LICENSE`. The bundled law excerpts are public domain; the sample invoices are synthetic.

---

## Acknowledgements

- [vLLM](https://github.com/vllm-project/vllm) for making local inference boring.
- [Qdrant](https://qdrant.tech) for a vector DB that doesn't fight you.
- [BAAI/bge-m3](https://huggingface.co/BAAI/bge-m3) for multilingual embeddings that actually work on German invoices.
- Everyone who's ever spent a weekend reconciling a bank statement. This is for you.
