from types import SimpleNamespace
from app.rules.engine import check_timeline_rules

def test_delivery_evidence_delivered():
    """Test 1: product not received + delivery status delivered => triggers"""
    case = SimpleNamespace(dispute_reason="product not received")
    evidence_list = [
        SimpleNamespace(evidence_type="delivery", content={"status": "delivered"})
    ]
    flags = check_timeline_rules(case, evidence_list)
    assert any(f[0] == "delivery_evidence_exists_but_disputed" for f in flags)

def test_delivery_evidence_lost_in_transit():
    """Test 2: product not received + delivery status lost_in_transit => no trigger"""
    case = SimpleNamespace(dispute_reason="product not received")
    evidence_list = [
        SimpleNamespace(evidence_type="delivery", content={"status": "lost_in_transit"})
    ]
    flags = check_timeline_rules(case, evidence_list)
    assert not any(f[0] == "delivery_evidence_exists_but_disputed" for f in flags)

def test_delivery_evidence_no_delivery():
    """Test 3: product not received + no delivery evidence => no trigger"""
    case = SimpleNamespace(dispute_reason="product not received")
    evidence_list = []
    flags = check_timeline_rules(case, evidence_list)
    assert not any(f[0] == "delivery_evidence_exists_but_disputed" for f in flags)
