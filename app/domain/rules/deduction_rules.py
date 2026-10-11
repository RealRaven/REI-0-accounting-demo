DEDUCTIBLE_CATEGORIES = {"software", "hosting", "office", "travel", "utilities", "hardware"}


def is_likely_deductible(invoice: dict) -> bool:
    return (invoice.get("category") or "").lower() in DEDUCTIBLE_CATEGORIES