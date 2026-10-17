from pathlib import Path

import pytesseract
from pdf2image import convert_from_path
from pypdf import PdfReader

from app.config import get_settings


def ocr_pdf(path: str | Path) -> str:
    if not get_settings().ocr_enabled:
        return ""

    try:
        num_pages = len(PdfReader(str(path)).pages)
    except Exception:
        return ""

    out = []
    # Process ONE page at a time to prevent RAM exhaustion
    for i in range(1, num_pages + 1):
        try:
            images = convert_from_path(str(path), dpi=200, first_page=i, last_page=i)
            if images:
                text = pytesseract.image_to_string(images[0], lang="deu+eng")
                out.append(text)
        except Exception:
            continue

    return "\n".join(out)