from sqlalchemy.orm import Session
from app.db.models import (
    Evidence, PaymentGatewayRecord, DeliveryRecord, OtpLog, CommunicationLog
)

DEMO_NOTE = "[DEMO] Retrieved from seeded external system mock"

def fetch_external_evidence(case, db: Session) -> int:
    """
    Queries mock external systems for the given case.transaction_id.
    Matches are copied into the Case's Evidence table.
    Returns the number of evidence records created.
    """
    created = 0
    txn_id = case.transaction_id
    base_date = case.created_at

    # 1. Query Payment Gateway
    payment_records = db.query(PaymentGatewayRecord).filter(
        PaymentGatewayRecord.transaction_id == txn_id
    ).all()
    for rec in payment_records:
        db.add(Evidence(
            case_id=case.id,
            evidence_type="payment",
            source_id=txn_id,
            content={
                "amount": float(rec.amount),
                "currency": rec.currency,
                "status": rec.status,
                "note": DEMO_NOTE
            },
            event_timestamp=rec.timestamp or base_date
        ))
        created += 1

    # 2. Query Courier/Delivery
    delivery_records = db.query(DeliveryRecord).filter(
        DeliveryRecord.transaction_id == txn_id
    ).all()
    for rec in delivery_records:
        db.add(Evidence(
            case_id=case.id,
            evidence_type="delivery",
            source_id=rec.tracking_number,
            content={
                "status": rec.status,
                "signed_by": rec.signed_by,
                "address_match": rec.address_match,
                "notes": rec.notes,
                "note": DEMO_NOTE
            },
            event_timestamp=rec.timestamp or base_date
        ))
        created += 1

    # 3. Query OTP Logs
    otp_records = db.query(OtpLog).filter(
        OtpLog.transaction_id == txn_id
    ).all()
    for rec in otp_records:
        db.add(Evidence(
            case_id=case.id,
            evidence_type="otp",
            source_id=None,
            content={
                "verified": rec.verified,
                "ip_address": rec.ip_address,
                "note": DEMO_NOTE
            },
            event_timestamp=rec.timestamp or base_date
        ))
        created += 1

    # 4. Query Communication Logs
    comm_records = db.query(CommunicationLog).filter(
        CommunicationLog.transaction_id == txn_id
    ).all()
    for rec in comm_records:
        db.add(Evidence(
            case_id=case.id,
            evidence_type="communication",
            source_id=None,
            content={
                "channel": rec.channel,
                "message": rec.message,
                "has_attachments": rec.has_attachments,
                "note": DEMO_NOTE
            },
            event_timestamp=rec.timestamp or base_date
        ))
        created += 1

    if created > 0:
        db.commit()

    return created
