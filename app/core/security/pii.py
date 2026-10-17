import re

from app.config import get_settings

IBAN_RE = re.compile(r"\b[A-Z]{2}\d{2}(?:[ ]?[A-Z0-9]{4}){2,7}\b")
TAXID_RE = re.compile(r"\b\d{2,3}/\d{3}/\d{5}\b")  # DE Steuernummer pattern


def mask_pii(text: str) -> str:
    if not get_settings().pii_mask:
        return text
    text = IBAN_RE.sub(lambda m: m.group(0)[:4] + "****" + m.group(0)[-4:], text)
    text = TAXID_RE.sub("***/***/*****", text)
    return text