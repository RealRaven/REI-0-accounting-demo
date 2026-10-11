from pathlib import Path

from app.core.llm.embeddings import embed_texts
from app.core.rag.chunking import chunk_law_text
from app.ingestion.pdf_parser import parse_pdf


async def load_law_pdf(path: str | Path) -> list[dict]:
    path = Path(path)
    text = parse_pdf(path)
    if not text.strip():
        return []
    chunks = chunk_law_text(text, pdf_path=str(path))
    law_name = path.stem  # e.g. "estg", "ustg"
    for c in chunks:
        c["law"] = law_name.upper()
    return chunks


async def embed_law_chunks(chunks: list[dict]) -> list[tuple[str, list[float], dict]]:
    if not chunks:
        return []
    texts = [c["text"] for c in chunks]
    vecs = await embed_texts(texts)
    out = []
    for i, (c, v) in enumerate(zip(chunks, vecs)):
        pid = f"{c['law']}-{c.get('para', 'x')}-{i}"
        out.append((pid, v, c))
    return out