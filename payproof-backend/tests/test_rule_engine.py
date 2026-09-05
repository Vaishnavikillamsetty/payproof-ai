"""
Rule engine tests.

Existing tests: delivery_evidence_exists_but_disputed rule.
New tests (added to cover the amount_mismatch bug):
  - amount_mismatch fires when case.amount differs from payment evidence by more than ₹0.01
  - amount_mismatch does NOT fire when amounts match exactly
  - amount_mismatch does NOT fire when amounts differ only by float representation (<= ₹0.01)
  - amount_mismatch fires when user enters 0 but payment evidence has a real amount
"""
from types import SimpleNamespace

from app.rules.engine import check_timeline_rules


# ─── Delivery contradiction rule ────────────────────────────────────────────

def test_delivery_evidence_delivered():
    """product not received + delivery status=delivered => triggers"""
    case = SimpleNamespace(dispute_reason="product not received", amount=49.99)
    evidence_list = [
        SimpleNamespace(evidence_type="delivery", content={"status": "delivered"},
                        event_timestamp=None)
    ]
    flags = check_timeline_rules(case, evidence_list)
    assert any(f[0] == "delivery_evidence_exists_but_disputed" for f in flags)


def test_delivery_evidence_lost_in_transit():
    """product not received + delivery status=lost_in_transit => no trigger"""
    case = SimpleNamespace(dispute_reason="product not received", amount=49.99)
    evidence_list = [
        SimpleNamespace(evidence_type="delivery", content={"status": "lost_in_transit"},
                        event_timestamp=None)
    ]
    flags = check_timeline_rules(case, evidence_list)
    assert not any(f[0] == "delivery_evidence_exists_but_disputed" for f in flags)


def test_delivery_evidence_no_delivery():
    """product not received + no delivery evidence => no trigger"""
    case = SimpleNamespace(dispute_reason="product not received", amount=49.99)
    flags = check_timeline_rules(case, [])
    assert not any(f[0] == "delivery_evidence_exists_but_disputed" for f in flags)


def test_conflicting_otp_evidence_is_a_security_contradiction():
    case = SimpleNamespace(dispute_reason="unauthorized transaction", amount=1100.00)
    evidence_list = [
        SimpleNamespace(evidence_type="otp", content={"verified": True, "ip_address": "192.168.1.5"}, event_timestamp=None),
        SimpleNamespace(evidence_type="otp", content={"verified": False, "ip_address": "203.0.113.42"}, event_timestamp=None),
    ]
    flags = check_timeline_rules(case, evidence_list)
    conflict = next(flag for flag in flags if flag[0] == "conflicting_otp_verification")
    assert conflict[1] is True
    assert "both verified and unverified" in conflict[2]


# ─── Amount mismatch rule ────────────────────────────────────────────────────

def _payment_ev(amount):
    return SimpleNamespace(
        evidence_type="payment",
        content={"amount": amount},
        event_timestamp=None,
    )


def _case(amount, reason="product not as described"):
    return SimpleNamespace(dispute_reason=reason, amount=amount)


def test_amount_mismatch_fires_on_large_difference():
    """case.amount=0.0, payment_evidence=299.99 => amount_mismatch fires."""
    flags = check_timeline_rules(_case(0.0), [_payment_ev(299.99)])
    assert any(f[0] == "amount_mismatch" and f[1] is True for f in flags), \
        "Expected amount_mismatch to fire when case.amount=0 and payment=299.99"


def test_amount_mismatch_fires_when_user_enters_wrong_amount():
    """case.amount=499.0, payment_evidence=299.99 => amount_mismatch fires."""
    flags = check_timeline_rules(_case(499.0), [_payment_ev(299.99)])
    assert any(f[0] == "amount_mismatch" and f[1] is True for f in flags)


def test_amount_mismatch_does_not_fire_when_amounts_match():
    """case.amount=299.99, payment_evidence=299.99 => no amount_mismatch."""
    flags = check_timeline_rules(_case(299.99), [_payment_ev(299.99)])
    assert not any(f[0] == "amount_mismatch" for f in flags), \
        "amount_mismatch should NOT fire when amounts match exactly"


def test_amount_mismatch_tolerates_float_rounding():
    """case.amount=299.99, payment_evidence=299.9900001 (float noise) => no trigger."""
    flags = check_timeline_rules(_case(299.99), [_payment_ev(299.9900001)])
    assert not any(f[0] == "amount_mismatch" for f in flags), \
        "amount_mismatch should NOT fire for sub-cent float differences"


def test_amount_mismatch_does_not_fire_when_no_payment_evidence():
    """No payment evidence => no amount_mismatch rule applies."""
    flags = check_timeline_rules(_case(49.99), [])
    assert not any(f[0] == "amount_mismatch" for f in flags)
