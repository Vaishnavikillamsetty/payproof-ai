import json
from uuid import uuid4
import pytest
from tests.test_razorpay_webhooks import (
    generate_signature, 
    WEBHOOK_SECRET, 
    client, 
    mock_live_provider, 
    db_session
)

def _create_webhook(client, db_session, event_type, dispute_id, payment_id):
    payload = json.dumps({
        "event": event_type,
        "payload": {
            "dispute": {
                "entity": {
                    "id": dispute_id,
                    "payment_id": payment_id,
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
    return response, event_id

def test_webhook_dispute_identity_updates_same_case(mock_live_provider, db_session):
    from app.db.models import Case
    # First event
    _create_webhook(client, db_session, "payment.dispute.created", "disp_111", "pay_111")
    cases = db_session.query(Case).filter_by(external_dispute_id="disp_111").all()
    assert len(cases) == 1
    
    # Second event with same dispute ID
    _create_webhook(client, db_session, "payment.dispute.action_required", "disp_111", "pay_111")
    
    db_session.expire_all() # Clear cache
    cases = db_session.query(Case).filter_by(external_dispute_id="disp_111").all()
    assert len(cases) == 1  # Still 1 case
    assert cases[0].status == "action_required"

def test_webhook_different_dispute_ids_create_different_cases(mock_live_provider, db_session):
    from app.db.models import Case
    _create_webhook(client, db_session, "payment.dispute.created", "disp_111_new", "pay_shared")
    _create_webhook(client, db_session, "payment.dispute.created", "disp_222_new", "pay_shared") # same payment, different dispute
    count1 = db_session.query(Case).filter_by(external_dispute_id="disp_111_new").count()
    count2 = db_session.query(Case).filter_by(external_dispute_id="disp_222_new").count()
    assert count1 == 1
    assert count2 == 1

def test_webhook_out_of_order_lifecycle_before_created(mock_live_provider, db_session):
    from app.db.models import Case
    # WON arrives first
    _create_webhook(client, db_session, "payment.dispute.won", "disp_ooo", "pay_ooo")
    case = db_session.query(Case).filter_by(external_dispute_id="disp_ooo").first()
    assert case.status == "won"
    
    # CREATED arrives later
    _create_webhook(client, db_session, "payment.dispute.created", "disp_ooo", "pay_ooo")
    case = db_session.query(Case).filter_by(external_dispute_id="disp_ooo").first()
    assert case.status == "won" # Must not downgrade to "new"

def test_webhook_terminal_state_protection(mock_live_provider, db_session):
    from app.db.models import Case, AuditLog
    
    uid1 = str(uuid4())[:8]
    disp1 = f"disp_t1_{uid1}"
    pay1 = f"pay_t1_{uid1}"
    
    _create_webhook(client, db_session, "payment.dispute.won", disp1, pay1)
    
    # 1. WON -> LOST is rejected
    _create_webhook(client, db_session, "payment.dispute.lost", disp1, pay1)
    case1 = db_session.query(Case).filter_by(external_dispute_id=disp1).first()
    assert case1.status == "won"
    # Verify audit log
    audit = db_session.query(AuditLog).filter_by(case_id=case1.id, step="webhook_transition_rejected").first()
    assert audit is not None
    assert audit.detail["attempted_status"] == "lost"
    
    # 3. WON -> CLOSED is allowed
    _create_webhook(client, db_session, "payment.dispute.closed", disp1, pay1)
    db_session.refresh(case1)
    assert case1.status == "closed"
    
    # 5. CLOSED -> UNDER_REVIEW is rejected
    _create_webhook(client, db_session, "payment.dispute.under_review", disp1, pay1)
    db_session.refresh(case1)
    assert case1.status == "closed"
    
    # 2. LOST -> WON is rejected
    uid2 = str(uuid4())[:8]
    disp2 = f"disp_t2_{uid2}"
    pay2 = f"pay_t2_{uid2}"
    
    _create_webhook(client, db_session, "payment.dispute.lost", disp2, pay2)
    _create_webhook(client, db_session, "payment.dispute.won", disp2, pay2)
    case2 = db_session.query(Case).filter_by(external_dispute_id=disp2).first()
    assert case2.status == "lost"
    
    # 4. LOST -> CLOSED is allowed
    _create_webhook(client, db_session, "payment.dispute.closed", disp2, pay2)
    db_session.refresh(case2)
    assert case2.status == "closed"
    
    # 6. Out-of-order UNDER_REVIEW after WON does not regress the state
    uid3 = str(uuid4())[:8]
    disp3 = f"disp_t3_{uid3}"
    pay3 = f"pay_t3_{uid3}"
    
    _create_webhook(client, db_session, "payment.dispute.won", disp3, pay3)
    _create_webhook(client, db_session, "payment.dispute.under_review", disp3, pay3)
    case3 = db_session.query(Case).filter_by(external_dispute_id=disp3).first()
    assert case3.status == "won"

def test_webhook_retry_failed_event(mock_live_provider, db_session):
    from app.db.models import WebhookEvent, Case
    # Send a broken webhook missing payment_id to force a failure
    payload = json.dumps({
        "event": "payment.dispute.created",
        "payload": {"dispute": {"entity": {"id": "disp_fail"}}} # Missing payment_id
    }).encode("utf-8")
    event_id = "evt_" + str(uuid4())
    sig = generate_signature(payload, WEBHOOK_SECRET)

    client.post("/webhooks/razorpay", content=payload, headers={"x-razorpay-signature": sig, "x-razorpay-event-id": event_id})
    
    event = db_session.query(WebhookEvent).filter_by(provider_event_id=event_id).first()
    assert event.status == "FAILED"
    
    # Now patch the JSON payload in DB so it can succeed
    event.payload_reference = {
        "payload": {"dispute": {"entity": {"id": "disp_fail", "payment_id": "pay_fail"}}}
    }
    db_session.commit()
    
    # Auth check - missing token
    retry_resp = client.post(f"/webhooks/retry/{event.id}")
    assert retry_resp.status_code == 401
    
    # Auth check - invalid token
    retry_resp = client.post(f"/webhooks/retry/{event.id}", headers={"x-internal-token": "wrong_token"})
    assert retry_resp.status_code == 401

    # Hit retry endpoint
    retry_resp = client.post(f"/webhooks/retry/{event.id}", headers={"x-internal-token": "dev_admin_token"})
    assert retry_resp.status_code == 200
    
    # Ensure it's now PROCESSED
    db_session.refresh(event)
    assert event.status == "PROCESSED"
    case = db_session.query(Case).filter_by(external_dispute_id="disp_fail").first()
    assert case is not None
