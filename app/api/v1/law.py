import math
import shutil
from pathlib import Path

import fitz  # PyMuPDF
from fastapi import APIRouter, File, HTTPException, Query, UploadFile

from app.config import get_settings
from app.core.llm.prompts import LAW_SYSTEM
from app.core.llm.vllm_client import VLLMClient
from app.core.llm.embeddings import embed_texts, embed_one

router = APIRouter()


def cosine_similarity(v1: list[float], v2: list[float]) -> float:
    """Pure python cosine similarity to avoid loading numpy."""
    dot_product = sum(a * b for a, b in zip(v1, v2))
    norm_a = math.sqrt(sum(a * a for a in v1))
    norm_b = math.sqrt(sum(b * b for b in v2))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot_product / (norm_a * norm_b)


@router.get("/search")
async def search_law(q: str = Query(..., min_length=2), k: int = 5):
    """Read text files directly from disk and do in-memory similarity."""
    s = get_settings()
    law_dir = Path(s.law_dir)
    if not law_dir.exists():
        return {"query": q, "items": []}

    # 1. Read all text files
    all_chunks = []
    for txt_file in law_dir.glob("*.txt"):
        content = txt_file.read_text(encoding="utf-8")
        # Split into paragraphs (blocks separated by double newlines)
        paragraphs = [p.strip() for p in content.split("\n\n") if len(p.strip()) > 50]
        for p in paragraphs:
            all_chunks.append({"text": p, "source": txt_file.name})

    if not all_chunks:
        return {"query": q, "items": []}

    # 2. Embed the query and the chunks (CPU handles this in milliseconds)
    query_vec = await embed_one(q)
    chunk_texts = [c["text"] for c in all_chunks]
    chunk_vecs = await embed_texts(chunk_texts)

    # 3. Score and sort
    scored_chunks = []
    for chunk, vec in zip(all_chunks, chunk_vecs):
        score = cosine_similarity(query_vec, vec)
        if score > 0.3: # Only keep decent matches
            scored_chunks.append({**chunk, "score": score})

    scored_chunks.sort(key=lambda x: x["score"], reverse=True)
    top_chunks = scored_chunks[:k]

    return {"query": q, "items": [{"payload": c} for c in top_chunks]}


@router.get("/ask")
async def ask_law(q: str = Query(..., min_length=2), k: int = 5):
    """Get top chunks and summarize them with the LLM."""
    search_results = await search_law(q, k)
    hits = search_results["items"]
    
    if not hits:
        return {"query": q, "summary": "I couldn't find any relevant text in the uploaded PDFs for your search.", "items": []}

    # Build context from the top chunks
    context = "\n\n---\n\n".join([h["payload"]["text"] for h in hits])
    
    # This prompt forces the LLM to summarize the provided context
    user_prompt = (
        f"Below is text extracted from a PDF document based on the search query '{q}':\n\n"
        f"--- START OF PDF TEXT ---\n"
        f"{context}\n"
        f"--- END OF PDF TEXT ---\n\n"
        f"Please read the text above and summarize what it says about '{q}'. "
        "Explain it simply for a business owner. "
        "Do NOT use outside knowledge. Only summarize what is in the provided text. "
        "You MUST reply in English."
    )

    llm = VLLMClient()
    try:
        # We use LAW_SYSTEM here
        summary = await llm.complete(LAW_SYSTEM, user_prompt, temperature=0.1)
    except Exception as e:
        summary = f"Error generating AI summary: {str(e)}"

    return {"query": q, "summary": summary, "items": hits}


@router.post("/upload")
async def upload_law_pdf(file: UploadFile = File(...)):
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported.")

    s = get_settings()
    law_dir = Path(s.law_dir)
    law_dir.mkdir(parents=True, exist_ok=True)
    
    dest_pdf = law_dir / file.filename
    with dest_pdf.open("wb") as f:
        shutil.copyfileobj(file.file, f)

    try:
        # Extract text using PyMuPDF (very low RAM)
        doc = fitz.open(str(dest_pdf))
        full_text = []
        for page in doc:
            full_text.append(page.get_text("text"))
        doc.close()
        
        text_content = "\n\n".join(full_text)
        
        # Save the raw text to a .txt file so we don't need Qdrant anymore
        dest_txt = law_dir / f"{file.filename}.txt"
        dest_txt.write_text(text_content, encoding="utf-8")
        
        return {"filename": file.filename, "status": "text extracted and saved to disk"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))