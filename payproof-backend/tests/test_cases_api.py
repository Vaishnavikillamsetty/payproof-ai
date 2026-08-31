"""
Tests for cases API to verify amount handling for seeded vs dynamic demo cases.
"""
from fastapi.testclient import TestClient

from app.main import app
from app.db.session import SessionLocal
from app.db.models import Case, Evidence

client = TestClient(app)

# Note: We rely on the DB already being seeded with DEMO_TXN_STRONG_1 (299.99),
# DEMO_TXN_WEAK_2 (22.00), etc.

def test_seeded_strong_transaction_overrides_incorrect_amount():
    """Input: DEMO_TXN_STRONG_1 with amount=0. Expected: backend overrides to 299.99."""
    resp = client.post("/cases/", json={
        "transaction_id": "DEMO_TXN_STRONG_1",
        "merchant_id": "M1",
        "dispute_reason": "product not received",
        "customer_claim": "test claim",
        "amount": 0  # Invalid amount from user
    })
    assert resp.status_code == 201
    data = resp.json()
    assert data["amount"] == 299.99, f"Expected 299.99, got {data['amount']}"


def test_seeded_weak_transaction_overrides_incorrect_amount():
    """Input: DEMO_TXN_WEAK_2 with amount=500. Expected: backend overrides to 22.00."""
    resp = client.post("/cases/", json={
        "transaction_id": "DEMO_TXN_WEAK_2",
        "merchant_id": "M1",
        "dispute_reason": "product not received",
        "customer_claim": "test claim",
        "amount": 500  # Incorrect amount
    })
    assert resp.status_code == 201
    data = resp.json()
    assert data["amount"] == 22.00


def test_seeded_empty_transaction_uses_default_override():
    """Input: DEMO_TXN_EMPTY_1 with amount=0. Expected: backend overrides to 150.00."""
    resp = client.post("/cases/", json={
        "transaction_id": "DEMO_TXN_EMPTY_1",
        "merchant_id": "M1",
        "dispute_reason": "product not received",
        "customer_claim": "test claim",
        "amount": 0
    })
    assert resp.status_code == 201
    data = resp.json()
    assert data["amount"] == 150.00


def test_random_transaction_uses_submitted_amount():
    """Input: RANDOM_TXN_123 with amount=499.99. Expected: case.amount=499.99."""
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


def test_random_transaction_rejects_invalid_amount():
    """Input: RANDOM_TXN_123 with amount=0. Expected: 400 validation error."""
    resp = client.post("/cases/", json={
        "transaction_id": "RANDOM_TXN_456",
        "merchant_id": "M1",
        "dispute_reason": "product not received",
        "customer_claim": "test claim",
        "amount": 0
    })
    assert resp.status_code == 400
    assert "Amount must be greater than 0" in resp.text


def test_demo_info_endpoint():
    """Verify GET /cases/demo-info returns correct structures."""
    # Seeded case
    r1 = client.get("/cases/demo-info/DEMO_TXN_STRONG_1")
    assert r1.status_code == 200
    assert r1.json() == {"is_demo": True, "expected_amount": 299.99}

    # Edge case (EMPTY)
    r2 = client.get("/cases/demo-info/DEMO_TXN_EMPTY_1")
    assert r2.status_code == 200
    assert r2.json() == {"is_demo": True, "expected_amount": 150.00}

    # Invalid demo ID
    r3 = client.get("/cases/demo-info/DEMO_TXN_INVALID_123")
    assert r3.status_code == 200
    assert r3.json() == {"is_demo": False}

    # Random ID
    r4 = client.get("/cases/demo-info/RANDOM_TXN_123")
    assert r4.status_code == 200
    assert r4.json() == {"is_demo": False}
