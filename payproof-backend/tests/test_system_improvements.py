import pytest
import uuid
import base64
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.main import app
from app.db.session import SessionLocal
from app.db.models import Case, Evidence, AuditLog
from app.evidence_categories import (
    map_to_canonical_category,
    compute_category_coverage,
    evaluate_evidence_strength,
    CANONICAL_CATEGORIES,
)
from app.agents.schemas import RecommendedAction, RiskLevel, EvidenceStrength

client = TestClient(app)


@pytest.fixture
def db():
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


def _create_test_case(db: Session, status: str = "OPEN") -> Case:
    case = Case(
        transaction_id=f"txn_{uuid.uuid4().hex[:8]}",
        dispute_reason="product_not_received",
        customer_claim="Item never received by buyer",
        merchant_id="merch_test_1",
        amount=150.00,
        currency="USD",
        status=status,
    )
    db.add(case)
    db.commit()
    db.refresh(case)
    return case


def test_1_human_approve_overrides_ai_request_more_evidence(db):
    case = _create_test_case(db, status="EVIDENCE_REQUESTED")
    resp = client.post(
        f"/cases/{case.id}/review",
        json={"action": "approve", "notes": "Merchant accepted liability", "reviewer_id": "rev_test1"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "DECISION_RECORDED"
    assert data["human_decision"] == "APPROVE"
    assert data["reviewer_id"] == "rev_test1"


def test_2_human_contest_overrides_ai_request_more_evidence(db):
    case = _create_test_case(db, status="EVIDENCE_REQUESTED")
    resp = client.post(
        f"/cases/{case.id}/review",
        json={"action": "contest", "notes": "Enough manual proof", "reviewer_id": "rev_test2"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "DECISION_RECORDED"
    assert data["human_decision"] == "CONTEST"


def test_3_human_request_more_evidence_overrides_ai_contest(db):
    case = _create_test_case(db, status="INVESTIGATING")
    resp = client.post(
        f"/cases/{case.id}/review",
        json={"action": "request_more_evidence", "notes": "Need carrier signature", "reviewer_id": "rev_test3"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "EVIDENCE_REQUESTED"
    assert data["human_decision"] == "REQUEST_MORE_EVIDENCE"


def test_4_human_contest_overrides_ai_approve(db):
    case = _create_test_case(db, status="INVESTIGATING")
    resp = client.post(
        f"/cases/{case.id}/review",
        json={"action": "contest", "notes": "Found customer signed receipt", "reviewer_id": "rev_test4"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "DECISION_RECORDED"
    assert data["human_decision"] == "CONTEST"


def test_5_approve_never_auto_resolves(db):
    case = _create_test_case(db, status="OPEN")
    resp = client.post(
        f"/cases/{case.id}/review",
        json={"action": "approve", "notes": "Approved but not resolved", "reviewer_id": "rev_test5"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] != "RESOLVED"
    assert data["status"] == "DECISION_RECORDED"


def test_6_resolve_action_sets_status_resolved(db):
    case = _create_test_case(db, status="DECISION_RECORDED")
    resp = client.post(
        f"/cases/{case.id}/resolve",
        json={"notes": "Final payout executed", "reviewer_id": "rev_test6"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "RESOLVED"


def test_7_evidence_with_0_categories():
    cats, count = compute_category_coverage([])
    strength = evaluate_evidence_strength([])
    assert cats == []
    assert count == 0
    assert strength == "NOT_EVALUATED"


def test_8_evidence_with_1_category():
    evidence = [{"evidence_type": "payment", "content": {"status": "paid"}}]
    cats, count = compute_category_coverage(evidence)
    assert "transaction" in cats
    assert count == 1
    strength = evaluate_evidence_strength(evidence, cats)
    assert strength in ("LOW", "MEDIUM")


def test_9_evidence_with_2_categories():
    evidence = [
        {"evidence_type": "payment", "content": {"status": "paid"}},
        {"evidence_type": "delivery", "content": {"status": "in_transit"}},
    ]
    cats, count = compute_category_coverage(evidence)
    assert set(cats) == {"transaction", "delivery"}
    assert count == 2
    strength = evaluate_evidence_strength(evidence, cats)
    assert strength == "MEDIUM"


def test_10_evidence_with_4_categories():
    evidence = [
        {"evidence_type": "payment", "content": {"status": "paid"}},
        {"evidence_type": "otp", "content": {"verified": True}},
        {"evidence_type": "delivery", "content": {"status": "delivered", "signed_by": "J. Doe"}},
        {"evidence_type": "refund_policy", "content": {"policy": "no refunds"}},
    ]
    cats, count = compute_category_coverage(evidence)
    assert count == 4
    strength = evaluate_evidence_strength(evidence, cats)
    assert strength == "HIGH"


def test_11_unknown_evidence_type_never_maps_to_merchant():
    unknowns = ["drone_footage", "random_doc", "social_media", "xyz123"]
    for ut in unknowns:
        cat = map_to_canonical_category(ut)
        assert cat is None, f"Unknown evidence type '{ut}' was mapped to '{cat}', expected None!"


def test_12_duplicate_evidence_of_same_category_deduped():
    evidence = [
        {"evidence_type": "payment"},
        {"evidence_type": "refund"},
        {"evidence_type": "transaction"},
    ]
    cats, count = compute_category_coverage(evidence)
    assert cats == ["transaction"]
    assert count == 1


def test_13_uploaded_evidence_persists_in_jsonb(db):
    case = _create_test_case(db)
    raw_content = b"Tracking ID: 1Z9999999999999999 Delivered on 2026-11-10"
    b64 = base64.b64encode(raw_content).decode("utf-8")

    resp = client.post(
        f"/cases/{case.id}/evidence",
        json={
            "evidence_type": "delivery",
            "filename": "proof_of_delivery.pdf",
            "description": "Courier signed manifest",
            "file_base64": b64,
            "verification_status": "VERIFIED",
        },
    )
    assert resp.status_code == 201
    ev_data = resp.json()
    assert ev_data["category"] == "delivery"
    assert ev_data["filename"] == "proof_of_delivery.pdf"

    ev = db.query(Evidence).filter(Evidence.id == ev_data["id"]).first()
    assert ev is not None
    assert ev.content.get("file_base64") == b64
    assert ev.category == "delivery"


def test_14_evidence_isolation_between_cases(db):
    case_a = _create_test_case(db)
    case_b = _create_test_case(db)

    client.post(
        f"/cases/{case_a.id}/evidence",
        json={"evidence_type": "payment", "filename": "case_a_doc.pdf", "description": "Payment proof"},
    )

    resp_b = client.get(f"/cases/{case_b.id}")
    assert resp_b.status_code == 200
    case_b_data = resp_b.json()
    assert case_b_data["category_count"] == 0
    assert case_b_data["categories_available"] == []


def test_15_ai_reanalysis_preserves_human_decision(db):
    case = _create_test_case(db, status="DECISION_RECORDED")
    case.human_decision = "APPROVE"
    case.reviewer_id = "analyst_sarah"
    case.reviewer_notes = "Customer is in good standing"
    db.commit()

    client.post(
        f"/cases/{case.id}/evidence",
        json={"evidence_type": "communication", "filename": "chat_log.txt", "description": "Support chat"},
    )

    db.refresh(case)
    assert case.human_decision == "APPROVE"
    assert case.reviewer_id == "analyst_sarah"


def test_16_ai_analysis_error_safe_fallback():
    from app.agents.investigation_agent import _deterministic_fallback
    fallback = _deterministic_fallback(
        evidence_types=[],
        contradictions_found=False,
        completeness=0,
        error_reason="Test simulate API outage",
    )
    assert fallback.ai_status == "FALLBACK"
    assert fallback.recommended_action == RecommendedAction.REQUEST_MORE_EVIDENCE
    assert fallback.human_approval_required is True


def test_17_double_click_protection_returns_409(db):
    case = _create_test_case(db, status="OPEN")
    r1 = client.post(
        f"/cases/{case.id}/review",
        json={"action": "approve", "notes": "First submission", "reviewer_id": "rev1"},
    )
    assert r1.status_code == 200

    r2 = client.post(
        f"/cases/{case.id}/review",
        json={"action": "contest", "notes": "Double click accidental", "reviewer_id": "rev1"},
    )
    assert r2.status_code == 409


def test_18_dashboard_metrics_counts_correctly(db):
    c1 = _create_test_case(db, status="DECISION_RECORDED")
    c2 = _create_test_case(db, status="RESOLVED")

    resp = client.get("/cases")
    assert resp.status_code == 200
    cases = resp.json()
    statuses = [c["status"] for c in cases]
    assert "DECISION_RECORDED" in statuses
    assert "RESOLVED" in statuses


def test_19_auth_fallback_derives_reviewer_id(db):
    case = _create_test_case(db, status="OPEN")
    resp = client.post(
        f"/cases/{case.id}/review",
        headers={"X-Reviewer-Email": "analyst@payproof.com"},
        json={"action": "approve", "notes": "Auth derived"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["reviewer_id"] == "analyst@payproof.com"


def test_20_demo_case_creates_with_all_canonical_categories(db):
    demo_resp = client.post(
        "/cases",
        json={
            "transaction_id": "DEMO_SCN_01_TXN",
            "dispute_reason": "product_not_received",
            "customer_claim": "Never arrived",
            "merchant_id": "merch_demo",
            "amount": 299.99,
        },
    )
    assert demo_resp.status_code == 201
    case_id = demo_resp.json()["id"]

    # Fetch case after pipeline execution
    get_resp = client.get(f"/cases/{case_id}")
    assert get_resp.status_code == 200
    case_data = get_resp.json()
    assert case_data["category_count"] > 0
    assert len(case_data["categories_available"]) > 0
