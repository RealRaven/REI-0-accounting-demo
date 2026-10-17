# REI-0 Accounting Demo

> Offline, self-hosted accounting assistant that reads invoices, watches your bank feed, chats with your books via RAG, finds hidden costs, and cites the actual tax law PDFs.

Everything runs **locally**. No OpenAI. No cloud.  
Stack: **vLLM** (LLM), **Qdrant** (vector DB), **Postgres** (ledger), local CPU embeddings via `sentence-transformers`, and your own EStG / UStG / AO PDFs on disk.

---

## Screenshots

### Chat with your books
![Chat UI](docs/chat-ui.png)

### AI-powered Law Search
![Law Search](docs/law-search.png)

---

## What it does

- **Chats with your books** — RAG across all local collections (invoices, bank, law, tax tips, documents). Answers include citations such as `[invoice#42 p.1]` or `[§ 15 UStG]`. Default language: English.
- **Reads invoices & documents** — Drop a PDF → OCR → structured extraction (vendor, date, amount, VAT, category) with a local LLM → stored in Qdrant + Postgres.
- **Watches banking** — Imports CSV / CAMT / MT940 and matches every transaction against invoices (fuzzy on amount + date + vendor).
- **Finds hidden costs** — Deterministic rules + RAG surface duplicate vendors, fee creep, unclaimed Vorsteuer, forgotten Werbungskosten, and forgotten subscriptions.
- **Tax tips DB** — Curated tips per branch / year / §, retrievable alongside the law.
- **Direct File RAG for Law PDFs** — Upload PDFs in the UI. The server extracts text with `PyMuPDF` (memory-safe) and runs in-memory cosine similarity search. No second embedding container required.

---

## Architecture (30 seconds)

```
┌──────────────┐     ┌──────────────┐
│  Invoices    │     │  Bank feed   │
│  PDFs / OCR  │     │  CSV / CAMT  │
└──────┬───────┘     └──────┬───────┘
       │                    │
       ▼                    ▼
┌────────────────────────────────────┐
│        Ingestion + Extraction      │
│   (pypdf → LLM structured output)  │
└────────────────┬───────────────────┘
                 │
     ┌───────────┼───────────┬──────────────┐
     ▼           ▼           ▼              ▼
┌─────────┐ ┌──────────┐ ┌─────────┐ ┌───────────┐
│ Qdrant  │ │ Qdrant   │ │ Local   │ │ Qdrant    │
│invoices │ │ bank_tx  │ │ .txt    │ │ tax_tips  │
└────┬────┘ └────┬─────┘ └────┬────┘ └─────┬─────┘
     └───────────┴──────┬─────┴────────────┘
                        ▼
              ┌──────────────────┐     ┌─────────────┐
              │   RAG pipeline   │◄───►│    vLLM     │
              │ retrieve→rerank  │     │ (local LLM) │
              │ →generate→cite   │     └─────────────┘
              └────────┬─────────┘
                       ▼
              ┌──────────────────┐
              │  Chat UI / SSE   │
              │  + Hidden costs  │
              └──────────────────┘
```

| Component   | Implementation                                      |
|-------------|-----------------------------------------------------|
| LLM         | vLLM serving any OpenAI-compatible model (default: `Qwen2.5-7B-Instruct`) |
| Embeddings  | `bge-m3` on CPU via `sentence-transformers` (keeps GPU VRAM free for the chat model) |
| Vector DB   | Qdrant – one collection per domain, hybrid dense + payload filters |
| Relational  | Postgres – invoices, bank rows, matches, audit log |
| Workers     | Celery + Redis – ingestion, embedding, nightly reconcile |

---

## Quickstart

```bash
cp .env.example .env
make install
make up          # vllm + qdrant + postgres + redis
make seed        # index fixtures and tax tips
```

First run pulls the model (~15 GB). Later starts are fast.

### Manual (no Make)

```bash
cp .env.example .env
docker compose up -d vllm qdrant postgres redis
python scripts/seed_qdrant.py
python scripts/index_tax_tips.py
python scripts/index_fixtures.py
uvicorn app.main:app --reload   # → http://localhost:8000
```

---

## Requirements

| Component | Minimum    | Notes |
|-----------|------------|-------|
| GPU       | 12 GB VRAM | Qwen2.5-7B-Instruct in bf16; 8 GB works with 4-bit quant |
| RAM       | 16 GB      | Local embeddings use ~2 GB |
| Disk      | 40 GB      | Model weights + law PDFs + vector store |
| Docker    | 24+        | With `nvidia-container-toolkit` |
| Python    | 3.11+      | When running outside Docker |

No GPU? Replace the vLLM service with `llama.cpp` in `docker-compose.yml` and point `VLLM_BASE_URL` at it. Everything else stays the same.

---

## Configuration

All settings live in `.env`:

```dotenv
# LLM
VLLM_BASE_URL=http://localhost:8001/v1
VLLM_API_KEY=not-needed
LLM_MODEL=Qwen/Qwen2.5-7B-Instruct
EMBED_MODEL=BAAI/bge-m3

# Vector DB
QDRANT_URL=http://localhost:6333
QDRANT_API_KEY=

# Relational
DATABASE_URL=postgresql+asyncpg://rei:rei@localhost:5432/rei

# Ingestion
INBOX_DIR=./data/inbox
PROCESSED_DIR=./data/processed
LAW_DIR=./data/law
TIPS_DIR=./data/tax_tips
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

The watcher picks it up, OCRs if needed, extracts fields, and moves it to `data/processed/`.

### 2. Import a bank statement

```bash
curl -F "file=@data/banking/konto_2024.csv" http://localhost:8000/api/v1/banking/import
```

Every row becomes a `BankTx`. Matching against invoices runs automatically.

### 3. Chat with your books

Open `http://localhost:8000/ui/chat`.

> **You:** How much did I spend on software subscriptions last quarter, and is any of it deductible?  
> **REI-0:** €1,842 across 14 transactions — mostly JetBrains (€684) and Figma (€468). Under § 4 Abs. 4 EStG these are Betriebsausgaben; the Figma charge on 2024-09-14 looks like a duplicate (`[invoice#87 p.1]`, `[bank_tx#4421]`). Your accountant may want the €79 back. See `[§ 4 EStG, p.12]` and tip `[software-subscriptions]`.

Every answer carries **citations**.

### 4. Look for hidden costs

Open `/ui/hidden-costs` or:

```bash
curl http://localhost:8000/api/v1/hidden-costs
```

Returns duplicate charges, unclaimed VAT, and forgotten subscriptions with confidence scores and evidence.

### 5. Upload and search the law

Go to `/ui/law` and drag-and-drop tax law PDFs (e.g. `Swiss tax system.pdf`).

- Text is extracted and stored locally.
- Search any term (e.g. “Zoll” or “Tax”); the AI summarizes the relevant paragraphs in English and cites the source document.

---

## API surface (v1)

| Method | Path                        | Purpose |
|--------|-----------------------------|---------|
| `POST` | `/api/v1/chat`              | SSE stream; RAG over all collections |
| `POST` | `/api/v1/invoices/upload`   | Upload + extract |
| `GET`  | `/api/v1/invoices`          | List / filter |
| `POST` | `/api/v1/banking/import`    | CSV / CAMT upload |
| `GET`  | `/api/v1/banking`           | List transactions |
| `POST` | `/api/v1/documents/upload`  | Generic doc → chunk → embed |
| `GET`  | `/api/v1/hidden-costs`      | Rule + RAG findings |
| `GET`  | `/api/v1/tax-tips`          | Filter by `branch`, `year`, `§` |
| `POST` | `/api/v1/law/upload`        | Upload PDF for Direct File RAG |
| `GET`  | `/api/v1/law/ask`           | Search local PDFs + AI summary |
| `GET`  | `/api/v1/health/vllm`       | Is the LLM alive? |
| `GET`  | `/api/v1/health/qdrant`     | Are the collections ready? |

Full OpenAPI: `http://localhost:8000/docs`

---

## How the RAG pipeline works

```
query
 │
 ├─► classify intent (books? law? tips? mixed?)
 │
 ├─► fan-out to N collections with per-intent weights
 │     invoices:1.0  bank:0.8  law:0.9  tips:0.6
 │
 ├─► per-collection top-K (dense + payload filters)
 │
 ├─► reciprocal-rank fusion → top-K global
 │
 ├─► PII masking on retrieved chunks
 │
 ├─► prompt = system(accountant) + chunks + question
 │
 ├─► vLLM generate (streamed)
 │
 └─► citation post-processing → SSE tokens + citation chips
```

Every request is logged to the `audit` table (`trace_id`, question, retrieved doc IDs, answer hash).

---

## Limitations & honesty

- This is a **demo**, not a tax advisor. It cites the law; it does not replace one. The `deductibility` field is a suggestion only.
- The hidden-cost detector is deliberately conservative — it will miss some issues and occasionally flag benign ones. Every finding includes `confidence` and `evidence`.
- OCR quality depends on `tesseract` and the source scan.
- Local CPU embeddings keep the GPU free for the LLM; large PDFs take a few extra seconds to embed.
- The audit log is append-only but not cryptographically signed. Add signing in `audit_repo.py` if needed.

---

## License

MIT — see `LICENSE`.  
Bundled law excerpts are public domain; sample invoices are synthetic.

---

## Acknowledgements

- [vLLM](https://github.com/vllm-project/vllm) – local inference that just works  
- [Qdrant](https://qdrant.tech) – vector DB that stays out of the way  
- [BAAI/bge-m3](https://huggingface.co/BAAI/bge-m3) – multilingual embeddings that handle German invoices  
- Everyone who has ever spent a weekend reconciling a bank statement