import pytest
import hmac
import hashlib
import json
from uuid import uuid4
from fastapi.testclient import TestClient

from app.main import app
from app.db.session import get_db
from app.db.models import WebhookEvent, Case, AuditLog
from app.services.razorpay.live_provider import LiveRazorpayProvider

client = TestClient(app)

WEBHOOK_SECRET = "test_secret_123"

def generate_signature(payload: bytes, secret: str) -> str:
    return hmac.new(
        secret.encode("utf-8"),
        payload,
        hashlib.sha256
    ).hexdigest()

@pytest.fixture
def mock_live_provider(monkeypatch):
    monkeypatch.setenv("RAZORPAY_MODE", "LIVE")
    monkeypatch.setenv("RAZORPAY_WEBHOOK_SECRET", WEBHOOK_SECRET)
    monkeypatch.setenv("RAZORPAY_KEY_ID", "rzp_test_123")
    monkeypatch.setenv("RAZORPAY_KEY_SECRET", "test_secret")

from app.db.session import SessionLocal
from app.routers.webhooks import get_db as webhooks_get_db

@pytest.fixture
def db_session():
    db = SessionLocal()
    try:
        yield db
    finally:
        # Clean up events
        db.query(WebhookEvent).delete()
        db.commit()
        db.close()

# Override get_db for TestClient
def override_get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

app.dependency_overrides[webhooks_get_db] = override_get_db

def test_webhook_missing_signature():
    response = client.post("/webhooks/razorpay", content=b"{}", headers={"x-razorpay-event-id": "evt_1"})
    assert response.status_code == 400
    assert "Missing signature header" in response.json()["detail"]

def test_webhook_missing_event_id():
    response = client.post("/webhooks/razorpay", content=b"{}", headers={"x-razorpay-signature": "abc"})
    assert response.status_code == 400
    assert "Missing event ID header" in response.json()["detail"]

def test_webhook_invalid_signature(mock_live_provider):
    response = client.post(
        "/webhooks/razorpay", 
        content=b'{"event":"payment.dispute.created"}', 
        headers={"x-razorpay-signature": "invalid_sig", "x-razorpay-event-id": "evt_1"}
    )
    assert response.status_code == 400
    assert "Invalid signature" in response.json()["detail"]

def test_webhook_valid_signature_payment_dispute_created(mock_live_provider, db_session):
    payload = json.dumps({
        "event": "payment.dispute.created",
        "payload": {
            "dispute": {
                "entity": {
                    "id": "disp_test_123",
                    "payment_id": "pay_test_123",
                    "amount": 10000,
                    "reason_code": "fraud"
                }
            }
        }
    }).encode("utf-8")
    
    event_id = "evt_" + str(uuid4())
    sig = generate_signature(payload, WEBHOOK_SECRET)

    response = client.post(
        "/webhooks/razorpay",
        content=payload,
        headers={"x-razorpay-signature": sig, "x-razorpay-event-id": event_id}
    )
    
    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    
    # Verify event persisted
    event = db_session.query(WebhookEvent).filter_by(provider_event_id=event_id).first()
    assert event is not None
    assert event.event_type == "payment.dispute.created"
    
def test_webhook_duplicate_event_id(mock_live_provider, db_session):
    payload = json.dumps({"event": "payment.dispute.created"}).encode("utf-8")
    event_id = "evt_duplicate"
    sig = generate_signature(payload, WEBHOOK_SECRET)
    
    # First call
    response1 = client.post(
        "/webhooks/razorpay",
        content=payload,
        headers={"x-razorpay-signature": sig, "x-razorpay-event-id": event_id}
    )
    assert response1.status_code == 200
    
    # Second call (duplicate)
    response2 = client.post(
        "/webhooks/razorpay",
        content=payload,
        headers={"x-razorpay-signature": sig, "x-razorpay-event-id": event_id}
    )
    assert response2.status_code == 200
    assert response2.json()["message"] == "Duplicate event"
    
    # Should only be one event in DB
    count = db_session.query(WebhookEvent).filter_by(provider_event_id=event_id).count()
    assert count == 1

def test_webhook_lifecycle_event_unsupported(mock_live_provider, db_session):
    payload = json.dumps({"event": "payment.authorized"}).encode("utf-8")
    event_id = "evt_" + str(uuid4())
    sig = generate_signature(payload, WEBHOOK_SECRET)
    
    response = client.post(
        "/webhooks/razorpay",
        content=payload,
        headers={"x-razorpay-signature": sig, "x-razorpay-event-id": event_id}
    )
    assert response.status_code == 200
    
    event = db_session.query(WebhookEvent).filter_by(provider_event_id=event_id).first()
    assert event.event_type == "payment.authorized"
