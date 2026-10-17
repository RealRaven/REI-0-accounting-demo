import re

def chunk_text(text: str, max_chars: int = 900, overlap: int = 120) -> list[str]:
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
                start = 0
                while start < len(p):
                    end = min(start + max_chars, len(p))
                    chunks.append(p[start:end])
                    start = end - overlap
                buf = ""
    if buf:
        chunks.append(buf)
    return chunks

LAW_PARA_RE = re.compile(r"((?:§|Art\.?|Artikel)\s*\d+[a-zA-Z]*)", re.IGNORECASE)

def chunk_law_text(text: str, pdf_path: str = "", page: int = 1) -> list[dict]:
    text = re.sub(r"\r\n?", "\n", text).strip()
    if not text:
        return []

    parts = LAW_PARA_RE.split(text)
    out: list[dict] = []
    
    if len(parts) > 1:
        i = 1
        while i < len(parts) - 1:
            para = parts[i].strip()
            body = parts[i + 1].strip()
            if body:
                if len(body) > 1500:
                    sub_chunks = chunk_text(body, max_chars=1200, overlap=100)
                    for j, sub in enumerate(sub_chunks):
                        out.append({
                            "para": f"{para} (Part {j+1})",
                            "text": f"{para}\n{sub}",
                            "pdf_path": pdf_path,
                            "page": page, 
                        })
                else:
                    out.append({
                        "para": para,
                        "text": f"{para}\n{body}",
                        "pdf_path": pdf_path,
                        "page": page,
                    })
            i += 2
    else:
        sub_chunks = chunk_text(text, max_chars=1200, overlap=100)
        for sub in sub_chunks:
            out.append({
                "para": "Excerpt",
                "text": sub,
                "pdf_path": pdf_path,
                "page": page,
            })

    return out