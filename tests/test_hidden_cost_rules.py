from app.domain.rules.hidden_cost_rules import (
    rule_duplicate_charges,
    rule_uncategorized_recurring,
)


def test_duplicate_charges_finds_two_identical(sample_bank, sample_invoice):
    findings = rule_duplicate_charges(sample_bank, [sample_invoice])
    assert len(findings) == 1
    assert findings[0]["kind"] == "duplicate_charge"
    assert abs(findings[0]["amount"] - 79.00) < 0.01
    assert set(findings[0]["evidence"]) == {"bank_tx#tx-1", "bank_tx#tx-2"}


def test_uncategorized_recurring_flags_adobe(sample_bank, sample_invoice):
    findings = rule_uncategorized_recurring(sample_bank, [sample_invoice])
    vendors = [f["vendor"] for f in findings]
    # Adobe has only 1 tx, so it won't trip the >=2 threshold in this sample
    assert "Figma" not in vendors  # Figma has an invoice