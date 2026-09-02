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

logger = logging.getLogger(__name__)
router = APIRouter()

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
        if event.event_type == "payment.dispute.created":
            dispute_data = payload.get("payload", {}).get("dispute", {}).get("entity", {})
            razorpay_dispute_id = dispute_data.get("id")
            razorpay_payment_id = dispute_data.get("payment_id")
            amount = dispute_data.get("amount", 0)
            reason = dispute_data.get("reason_code", "unknown")
            
            if not razorpay_payment_id:
                raise ValueError("Missing payment_id in webhook payload")

            # Check if case exists for this payment_id/dispute_id
            # Using transaction_id mapping to payment_id for simplicity
            case = db.query(Case).filter(Case.transaction_id == razorpay_payment_id).first()
            if not case:
                case = Case(
                    transaction_id=razorpay_payment_id,
                    dispute_reason=reason,
                    customer_claim=f"Webhook event: {event.event_type}",
                    merchant_id="merchant_webhook_123", # default or derived
                    amount=amount / 100.0, # DB stores as float (numeric) for frontend compatibility
                    status="new"
                )
                db.add(case)
                db.commit()
                db.refresh(case)
                
                # Audit Case Creation
                db.add(AuditLog(
                    case_id=case.id,
                    step="webhook_case_created",
                    detail={"event_id": str(event.id), "event_type": event.event_type}
                ))
            else:
                # Update existing case
                case.status = "new" # Reset status for re-investigation
                db.add(AuditLog(
                    case_id=case.id,
                    step="webhook_case_updated",
                    detail={"event_id": str(event.id), "event_type": event.event_type}
                ))
            db.commit()

            # Link event to case
            event.case_id = case.id
            db.commit()

            # Trigger investigation
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
            # Just update the case status for lifecycle events
            dispute_data = payload.get("payload", {}).get("dispute", {}).get("entity", {})
            razorpay_payment_id = dispute_data.get("payment_id")
            
            case = db.query(Case).filter(Case.transaction_id == razorpay_payment_id).first()
            if case:
                event.case_id = case.id
                db.add(AuditLog(
                    case_id=case.id,
                    step="webhook_lifecycle_update",
                    detail={"event_id": str(event.id), "event_type": event.event_type}
                ))
                # For demo, just log it. A robust system might update the status directly.
            
            event.status = "PROCESSED"
            db.commit()
        else:
            event.status = "PROCESSED" # Unsupported but valid event
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
