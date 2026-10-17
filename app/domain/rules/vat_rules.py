def vorsteuer_claimable(invoice: dict) -> bool:
    """§ 15 UStG: Vorsteuer abziehbar wenn ordnungsgemäße Rechnung."""
    return bool(invoice.get("vat_amount")) and (invoice.get("category") or "") != "private"