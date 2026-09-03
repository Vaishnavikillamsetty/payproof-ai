"""
Tests for cases API to verify amount handling for seeded vs dynamic demo cases.
"""
from fastapi.testclient import TestClient

from app.main import app
from app.db.session import SessionLocal
from app.db.models import Case, Evidence

client = TestClient(app)

def test_seeded_strong_transaction_overrides_incorrect_amount():
    resp = client.post("/cases/", json={
        "transaction_id": "DEMO_SCN_01_TESTSUFFIX",
        "merchant_id": "M1",
        "dispute_reason": "product not received",
        "customer_claim": "test claim",
        "amount": 0  # Invalid amount from user
    })
    assert resp.status_code == 201
    data = resp.json()
    assert data["amount"] == 299.99, f"Expected 299.99, got {data['amount']}"

def test_seeded_weak_transaction_overrides_incorrect_amount():
    resp = client.post("/cases/", json={
        "transaction_id": "DEMO_SCN_05",
        "merchant_id": "M1",
        "dispute_reason": "product not received",
        "customer_claim": "test claim",
        "amount": 500  # Incorrect amount
    })
    assert resp.status_code == 201
    data = resp.json()
    assert data["amount"] == 120.00

def test_random_transaction_uses_submitted_amount():
    resp = client.post("/cases/", json={
        "transaction_id": "RANDOM_TXN_123",
        "merchant_id": "M1",
        "dispute_reason": "product not received",
        "customer_claim": "test claim",
        "amount": 499.99
    })
    assert resp.status_code == 201
    data = resp.json()
    assert data["amount"] == 499.99

def test_demo_info_endpoint():
    r1 = client.get("/cases/demo-info/DEMO_SCN_01_ABCD")
    assert r1.status_code == 200
    assert r1.json() == {"is_demo": True, "expected_amount": 299.99}

    r3 = client.get("/cases/demo-info/DEMO_TXN_INVALID_123")
    assert r3.status_code == 200
    assert r3.json() == {"is_demo": False}

    r4 = client.get("/cases/demo-info/RANDOM_TXN_123")
    assert r4.status_code == 200
    assert r4.json() == {"is_demo": False}

def test_human_review_endpoint():
    # create case
    resp = client.post("/cases/", json={
        "transaction_id": "RANDOM_TXN_REVIEW_1",
        "merchant_id": "M1",
        "dispute_reason": "product not received",
        "customer_claim": "test claim",
        "amount": 100.00
    })
    case_id = resp.json()["id"]

    # call review
    r_review = client.post(f"/cases/{case_id}/review", json={
        "action": "request_more_evidence",
        "notes": "Testing human review endpoint."
    })
    assert r_review.status_code == 200
    assert r_review.json()["status"] == "request_more_evidence"

    # fetch audit log to verify event
    r_audit = client.get(f"/cases/{case_id}/audit")
    assert r_audit.status_code == 200
    logs = r_audit.json()
    
    review_log = next((log for log in logs if log["step"] == "human_review_decision"), None)
    assert review_log is not None
    assert review_log["detail"]["action"] == "request_more_evidence"
    assert review_log["detail"]["notes"] == "Testing human review endpoint."
