import re


def chunk_text(text: str, max_chars: int = 900, overlap: int = 120) -> list[str]:
    """Simple paragraph-aware chunker with character fallback."""
    text = re.sub(r"\r\n?", "\n", text).strip()
    if not text:
        return []

    paragraphs = re.split(r"\n\s*\n", text)
    chunks: list[str] = []
    buf = ""
    for p in paragraphs:
        p = p.strip()
        if not p:
            continue
        if len(buf) + len(p) + 2 <= max_chars:
            buf = f"{buf}\n\n{p}" if buf else p
        else:
            if buf:
                chunks.append(buf)
            if len(p) <= max_chars:
                buf = p
            else:
                # hard split long paragraph
                start = 0
                while start < len(p):
                    end = min(start + max_chars, len(p))
                    chunks.append(p[start:end])
                    start = end - overlap
                buf = ""
    if buf:
        chunks.append(buf)
    return chunks


LAW_PARA_RE = re.compile(r"(§\s*\d+[a-zA-Z]?)")


def chunk_law_text(text: str, pdf_path: str = "") -> list[dict]:
    """Split statute text by § and return payload dicts."""
    text = re.sub(r"\r\n?", "\n", text).strip()
    parts = LAW_PARA_RE.split(text)
    out: list[dict] = []
    # parts comes as [pre, "§ X", body, "§ Y", body, ...]
    i = 1
    while i < len(parts) - 1:
        para = parts[i].strip()
        body = parts[i + 1].strip()
        if body:
            out.append({
                "para": para,
                "text": f"{para}\n{body}",
                "pdf_path": pdf_path,
                "page": 1,
            })
        i += 2
    if not out:
        out.append({"para": "", "text": text, "pdf_path": pdf_path, "page": 1})
    return out