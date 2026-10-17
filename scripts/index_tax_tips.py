import uuid
from pathlib import Path

import yaml

from app.core.llm.embeddings import embed_texts


def read_tips_dir(dir_path: str | Path) -> list[dict]:
    out: list[dict] = []
    for p in Path(dir_path).glob("*.yaml"):
        try:
            data = yaml.safe_load(p.read_text(encoding="utf-8")) or []
        except Exception:
            continue
        for tip in data:
            tip.setdefault("source_file", p.name)
            out.append(tip)
    return out


async def embed_tips(tips: list[dict]) -> list[tuple[str, list[float], dict]]:
    if not tips:
        return []
    texts = [f"{t.get('title', '')}. {t.get('body', '')}" for t in tips]
    vecs = await embed_texts(texts)
    
    out = []
    for i, (t, v) in enumerate(zip(tips, vecs)):
        raw_id = t.get("id", f"tip-{i}")
        pid = str(uuid.uuid5(uuid.NAMESPACE_DNS, raw_id))
        out.append((pid, v, t))
    return out