from pathlib import Path

import pytesseract
from PIL import Image
from pdf2image import convert_from_path

from app.config import get_settings


def ocr_pdf(path: str | Path) -> str:
    if not get_settings().ocr_enabled:
        return ""
    try:
        images = convert_from_path(str(path), dpi=200)
    except Exception:
        return ""
    out = []
    for img in images:
        try:
            out.append(pytesseract.image_to_string(img, lang="deu+eng"))
        except Exception:
            out.append("")
    return "\n".join(out)