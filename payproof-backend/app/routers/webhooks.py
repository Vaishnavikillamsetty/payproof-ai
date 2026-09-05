from fastapi import APIRouter, Request, Header, HTTPException, Depends, BackgroundTasks
from sqlalchemy.orm import Session
import logging
import hmac
import hashlib
import json
from uuid import UUID

from app.db.session import get_db
from app.db.models import WebhookEvent, Case, AuditLog
from app.services.razorpay.factory import get_razorpay_provider
from app.orchestrator import run_pipeline
from app.lifecycle import lifecycle_for_recommendation

logger = logging.getLogger(__name__)
router = APIRouter()

STATE_PRIORITY = {
    "new": 0,
    "investigating": 1,
    "request_more_evidence": 2,
    "evidence_requested": 2,
    "human_review": 2,
    "escalate": 2,
    "escalated": 2,
    "accept": 2,
    "contest": 2,
    "strong_case": 2,
    "action_required": 3,
    "under_review": 4,
    "won": 5,
    "lost": 5,
    "closed": 6,  # Closed is strictly higher than won/lost for lifecycle events
}

def get_state_priority(status: str) -> int:
    return STATE_PRIORITY.get(status.lower(), -1)

def can_transition(current: str, new: str) -> bool:
    """
    Explicit transition validation.
    """
    if current == new:
        return True
        
    # Explicit rejection rules for contradictory terminal states
    if current == "won" and new == "lost":
        return False
    if current == "lost" and new == "won":
        return False
        
    # Rejections for regressing from CLOSED
    if current == "closed" and new in ["under_review", "action_required", "won", "lost"]:
        return False
        
    # Standard priority check for the rest
    return get_state_priority(new) >= get_state_priority(current)

def process_webhook_background(event_id: UUID, db: Session):
    """
    Background task to process a webhook event safely.
    It creates/updates the case and triggers the investigation.
    """
    event = db.query(WebhookEvent).filter(WebhookEvent.id == event_id).first()
    if not event:
        return

    try:
        event.status = "PROCESSING"
        db.commit()

        payload = event.payload_reference
        dispute_data = payload.get("payload", {}).get("dispute", {}).get("entity", {})
        razorpay_dispute_id = dispute_data.get("id")
        razorpay_payment_id = dispute_data.get("payment_id")
        amount = dispute_data.get("amount", 0)
        reason = dispute_data.get("reason_code", "unknown")
        
        if not razorpay_dispute_id:
            logger.error("Missing dispute ID in webhook payload")
            event.status = "FAILED"
            db.commit()
            return
            
        if not razorpay_payment_id:
            logger.error("Missing payment_id in webhook payload")
            event.status = "FAILED"
            db.commit()
            return

        # 1. Identity lookup via external_dispute_id
        case = db.query(Case).filter(Case.external_dispute_id == razorpay_dispute_id).first()

        if event.event_type == "payment.dispute.created":
            if not case:
                case = Case(
                    transaction_id=razorpay_payment_id,
                    external_dispute_id=razorpay_dispute_id,
                    dispute_reason=reason,
                    customer_claim=f"Webhook event: {event.event_type}",
                    merchant_id="merchant_webhook_123",
                    amount=amount / 100.0,
                    status="new"
                )
                db.add(case)
                db.commit()
                db.refresh(case)
                db.add(AuditLog(
                    case_id=case.id,
                    step="webhook_case_created",
                    detail={"event_id": str(event.id), "event_type": event.event_type}
                ))
            else:
                # Update existing case (might have been created by an out-of-order lifecycle event)
                case.transaction_id = razorpay_payment_id
                case.dispute_reason = reason
                if case.amount == 0:
                    case.amount = amount / 100.0
                
                # State transition check
                if can_transition(case.status, "new"):
                    case.status = "new"
                
                db.add(AuditLog(
                    case_id=case.id,
                    step="webhook_case_updated",
                    detail={"event_id": str(event.id), "event_type": event.event_type}
                ))
            db.commit()
            
            event.case_id = case.id
            db.commit()

            # Trigger investigation if the state allowed it to reset to 'new' or if it was just created
            if case.status == "new":
                db.add(AuditLog(
                    case_id=case.id,
                    step="webhook_processing_started",
                    detail={"event_id": str(event.id)}
                ))
                db.commit()
                run_pipeline(case.id, db)
            
            event.status = "PROCESSED"
            db.commit()

        elif event.event_type in [
            "payment.dispute.action_required",
            "payment.dispute.won",
            "payment.dispute.lost",
            "payment.dispute.closed",
            "payment.dispute.under_review"
        ]:
            if not case:
                # Out-of-order event arriving before 'created'
                # Create a placeholder case
                case = Case(
                    transaction_id=razorpay_payment_id,
                    external_dispute_id=razorpay_dispute_id,
                    dispute_reason=reason,
                    customer_claim=f"Placeholder from {event.event_type}",
                    merchant_id="merchant_webhook_123",
                    amount=amount / 100.0,
                    status="new" # Temp state
                )
                db.add(case)
                db.commit()
                db.refresh(case)
                
            event.case_id = case.id
            
            # Map event type to status
            status_map = {
                "payment.dispute.action_required": "action_required",
                "payment.dispute.under_review": "under_review",
                "payment.dispute.won": "won",
                "payment.dispute.lost": "lost",
                "payment.dispute.closed": "closed"
            }
            new_status = status_map.get(event.event_type)
            if new_status:
                new_status = lifecycle_for_recommendation(case.ai_recommendation, new_status)
            
            if new_status:
                if can_transition(case.status, new_status):
                    old_status = case.status
                    case.status = new_status
                    db.add(AuditLog(
                        case_id=case.id,
                        step="webhook_lifecycle_update",
                        detail={"event_id": str(event.id), "event_type": event.event_type, "new_status": new_status, "actual_case_status": case.status}
                    ))
                else:
                    db.add(AuditLog(
                        case_id=case.id,
                        step="webhook_transition_rejected",
                        detail={
                            "event_id": str(event.id), 
                            "event_type": event.event_type, 
                            "attempted_status": new_status, 
                            "current_status": case.status,
                            "reason": "Transition rejected by state priority rules"
                        }
                    ))
            
            event.status = "PROCESSED"
            db.commit()
        else:
            event.status = "PROCESSED"
            db.commit()

    except Exception as e:
        logger.error("Failed to process webhook event %s: %s", event_id, e)
        event.status = "FAILED"
        db.commit()
        if event.case_id:
            db.add(AuditLog(
                case_id=event.case_id,
                step="webhook_processing_failed",
                detail={"event_id": str(event.id), "error": str(e)}
            ))
            db.commit()


@router.post("/razorpay")
async def razorpay_webhook(
    request: Request,
    background_tasks: BackgroundTasks,
    x_razorpay_signature: str = Header(None),
    x_razorpay_event_id: str = Header(None),
    db: Session = Depends(get_db)
):
    """
    Razorpay Webhook handler.
    Requirements:
    1. Read raw body.
    2. Verify HMAC signature.
    3. Read event ID and check idempotency.
    4. Persist event.
    5. Trigger background task.
    6. Return fast success.
    """
    # 1. Read raw body
    raw_body = await request.body()

    if not x_razorpay_signature:
        raise HTTPException(status_code=400, detail="Missing signature header")
    if not x_razorpay_event_id:
        raise HTTPException(status_code=400, detail="Missing event ID header")

    # 2. Verify Signature
    provider = get_razorpay_provider()
    try:
        is_valid = provider.verify_webhook_signature(raw_body, x_razorpay_signature)
        if not is_valid:
            logger.warning("Webhook signature verification failed")
            raise HTTPException(status_code=400, detail="Invalid signature")
    except Exception as e:
        logger.error("Error verifying webhook signature: %s", e)
        raise HTTPException(status_code=400, detail="Invalid signature")
    
    # 3. Idempotency Check
    existing_event = db.query(WebhookEvent).filter(WebhookEvent.provider_event_id == x_razorpay_event_id).first()
    if existing_event:
        logger.info("Duplicate webhook event received: %s", x_razorpay_event_id)
        # 4H: Duplicate event -> return success immediately
        return {"status": "ok", "message": "Duplicate event"}

    # Parse JSON after signature verified
    try:
        payload = json.loads(raw_body)
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON body")

    event_type = payload.get("event", "unknown")

    # 4. Persist Event
    new_event = WebhookEvent(
        provider_event_id=x_razorpay_event_id,
        event_type=event_type,
        status="VERIFIED",
        payload_reference=payload
    )
    db.add(new_event)
    db.commit()
    db.refresh(new_event)

    # 5. Background Processing
    background_tasks.add_task(process_webhook_background, new_event.id, db)

    # 6. Return Fast
    return {"status": "ok"}

@router.post("/retry/{event_id}")
def retry_webhook_processing(
    event_id: UUID,
    background_tasks: BackgroundTasks,
    x_internal_token: str = Header(None),
    db: Session = Depends(get_db)
):
    """
    Internal endpoint to retry processing a FAILED or stuck webhook event.
    For hackathon use/recovery. Protected by internal token.
    """
    import secrets
    from app.config import settings
    
    if not x_internal_token or not secrets.compare_digest(x_internal_token, settings.internal_admin_token):
        raise HTTPException(status_code=401, detail="Unauthorized")

    event = db.query(WebhookEvent).filter(WebhookEvent.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
        
    if event.status not in ["FAILED", "PROCESSING", "VERIFIED"]:
        raise HTTPException(status_code=400, detail=f"Cannot retry event in status {event.status}")
        
    event.status = "VERIFIED" # Reset to trigger processing again safely
    db.commit()
    
    background_tasks.add_task(process_webhook_background, event.id, db)
    
    return {"status": "ok", "message": "Event queued for retry"}
