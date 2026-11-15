"""
external_systems.py — Mock external evidence lookup.

Primary path: queries 4 seeded DB tables by transaction_id (ext_payment_gateway,
ext_delivery, ext_otp_log, ext_communication_log).

Dynamic fallback: if no seeded records exist for a transaction_id, uses a
deterministic hash of the ID to generate a realistic evidence profile, so that
any arbitrary transaction ID entered in the UI produces a meaningful, varied outcome
rather than always defaulting to human_review.
"""

import hashlib
import logging
from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from app.db.models import (
    CommunicationLog,
    DeliveryRecord,
    Evidence,
    OtpLog,
    PaymentGatewayRecord,
)
from app.evidence_categories import map_to_canonical_category

logger = logging.getLogger(__name__)

DEMO_NOTE = "[DEMO] Retrieved from seeded external system mock"
FALLBACK_NOTE = "[DEMO] Dynamically generated for demonstration"


# --------------------------------------------------------------------------- #
# Helpers                                                                     #
# --------------------------------------------------------------------------- #

def _hash_scenario(transaction_id: str) -> int:
    """Return a stable 0-9 bucket for any transaction_id string."""
    digest = hashlib.sha256(transaction_id.encode()).hexdigest()
    return int(digest[:8], 16) % 10


def _get_base_demo_id(txn_id: str) -> str:
    """Extracts base ID (e.g., DEMO_SCN_05) from DEMO_SCN_05_A1B2C3."""
    if txn_id.startswith("DEMO_SCN_"):
        parts = txn_id.split("_")
        if len(parts) >= 3:
            return f"{parts[0]}_{parts[1]}_{parts[2]}"
    return txn_id


def get_demo_expected_amount(db: Session, transaction_id: str) -> float | None:
    """
    Return the authoritative amount for a seeded demo transaction.
    Returns None if it is not a recognized seeded demo ID.
    """
    base_id = _get_base_demo_id(transaction_id)
    if not base_id.startswith("DEMO_"):
        return None
        
    payment = db.query(PaymentGatewayRecord).filter_by(transaction_id=base_id).first()
    if payment:
        return float(payment.amount)
        
    if transaction_id == "DEMO_TXN_EMPTY_1":
        return 150.0
        
    return None


def _add_evidence(
    db: Session,
    case,
    ev_type: str,
    source_id,
    content: dict,
    event_timestamp: datetime,
    note: str,
    filename: str = None,
    description: str = None
) -> None:
    category = map_to_canonical_category(ev_type)
    
    # Set verification status based on evidence source
    v_status = "unverified"
    if ev_type in ("payment", "transaction"):
        status_val = str(content.get("status", "")).lower()
        if status_val in ("success", "captured", "paid", "settled"):
            v_status = "verified"
    elif ev_type in ("delivery", "fulfillment"):
        if str(content.get("status", "")).lower() == "delivered":
            v_status = "verified"
    elif ev_type in ("otp", "auth"):
        if content.get("verified") is True:
            v_status = "verified"

    clean_txn = str(case.transaction_id)[:14]
    db.add(Evidence(
        case_id=case.id,
        evidence_type=ev_type,
        category=category,
        source_id=source_id,
        filename=filename or f"{ev_type}_{clean_txn}.json",
        description=description or f"{category.capitalize() if category else ev_type.capitalize()} evidence for {clean_txn}",
        verification_status=v_status,
        content={**content, "note": note},
        event_timestamp=event_timestamp,
    ))


# --------------------------------------------------------------------------- #
# Seeded DB lookup (primary path)                                             #
# --------------------------------------------------------------------------- #

def _fetch_seeded(case, db: Session, base_date: datetime) -> int:
    """Query the 4 seeded external-system tables. Returns records created."""
    txn_id = case.transaction_id
    base_id = _get_base_demo_id(txn_id)
    created = 0

    for rec in db.query(PaymentGatewayRecord).filter(
        PaymentGatewayRecord.transaction_id == base_id
    ).all():
        _add_evidence(db, case, "payment", txn_id,
                      {"amount": float(rec.amount), "currency": rec.currency,
                       "status": rec.status},
                      rec.timestamp or base_date, DEMO_NOTE,
                      filename=f"payment_{base_id}.json",
                      description=f"Payment Gateway log for {rec.currency} {rec.amount}")
        created += 1

    for rec in db.query(DeliveryRecord).filter(
        DeliveryRecord.transaction_id == base_id
    ).all():
        _add_evidence(db, case, "delivery", rec.tracking_number,
                      {"status": rec.status, "signed_by": rec.signed_by,
                       "address_match": rec.address_match, "notes": rec.notes},
                      rec.timestamp or base_date, DEMO_NOTE,
                      filename=f"delivery_{rec.tracking_number}.json",
                      description=f"Carrier delivery confirmation for tracking {rec.tracking_number}")
        created += 1

    for rec in db.query(OtpLog).filter(
        OtpLog.transaction_id == base_id
    ).all():
        _add_evidence(db, case, "otp", None,
                      {"verified": rec.verified, "ip_address": rec.ip_address},
                      rec.timestamp or base_date, DEMO_NOTE,
                      filename=f"auth_log_{base_id}.json",
                      description="2FA / OTP verification audit log")
        created += 1

    for rec in db.query(CommunicationLog).filter(
        CommunicationLog.transaction_id == base_id
    ).all():
        _add_evidence(db, case, "communication", None,
                      {"channel": rec.channel, "message": rec.message,
                       "has_attachments": rec.has_attachments},
                      rec.timestamp or base_date, DEMO_NOTE,
                      filename=f"customer_comm_{base_id}.json",
                      description=f"Customer communication transcript via {rec.channel}")
        created += 1

    if created:
        db.commit()
    return created


# --------------------------------------------------------------------------- #
# Dynamic fallback (any unknown transaction_id)                               #
# --------------------------------------------------------------------------- #

def _fetch_dynamic(case, db: Session, base_date: datetime) -> int:
    """Generate deterministic evidence for unknown transaction IDs."""
    bucket = _hash_scenario(case.transaction_id)
    amount = float(case.amount)
    created = 0

    if bucket <= 3:
        # Scenario A (40%): Full 4-category evidence
        _add_evidence(db, case, "payment", case.transaction_id,
                      {"amount": amount, "currency": case.currency, "status": "success"},
                      base_date, FALLBACK_NOTE, filename=f"gateway_{case.transaction_id[:8]}.json")
        _add_evidence(db, case, "delivery", f"TRK-{case.transaction_id[-6:].upper()}",
                      {"status": "delivered", "signed_by": "Customer",
                       "address_match": True, "notes": "Delivered on time"},
                      base_date + timedelta(days=2), FALLBACK_NOTE, filename=f"proof_of_delivery_{case.transaction_id[-6:]}.json")
        _add_evidence(db, case, "otp", None,
                      {"verified": True, "ip_address": "192.168.1.1"},
                      base_date, FALLBACK_NOTE, filename="otp_auth_log.json")
        _add_evidence(db, case, "communication", None,
                      {"channel": "email",
                       "message": "Please cancel my subscription — I am disputing this charge.",
                       "has_attachments": False},
                      base_date + timedelta(days=1), FALLBACK_NOTE, filename="customer_chat.json")
        created = 4

    elif bucket <= 6:
        # Scenario B (30%): Payment only (1 category)
        _add_evidence(db, case, "payment", case.transaction_id,
                      {"amount": amount, "currency": case.currency, "status": "success"},
                      base_date, FALLBACK_NOTE, filename=f"gateway_{case.transaction_id[:8]}.json")
        created = 1

    elif bucket <= 8:
        # Scenario C (20%): Payment + Delivery contradiction
        _add_evidence(db, case, "payment", case.transaction_id,
                      {"amount": amount, "currency": case.currency, "status": "success"},
                      base_date, FALLBACK_NOTE, filename=f"gateway_{case.transaction_id[:8]}.json")
        _add_evidence(db, case, "delivery", f"TRK-{case.transaction_id[-6:].upper()}",
                      {"status": "delivered", "signed_by": "Front Desk",
                       "address_match": True,
                       "notes": "Signed and accepted at reception"},
                      base_date + timedelta(days=3), FALLBACK_NOTE, filename="delivery_reception.json")
        created = 2

    else:
        # Scenario D (10%): No evidence (0/4)
        created = 0

    if created:
        db.commit()
    return created


# --------------------------------------------------------------------------- #
# Public API called by the orchestrator                                       #
# --------------------------------------------------------------------------- #

def fetch_external_evidence(case, db: Session) -> int:
    """Queries external systems or seed records for the given case."""
    SEEDED_ID_PREFIXES = ("DEMO_TXN_", "DEMO_SCN_")

    base_date = case.created_at or datetime.now(timezone.utc)
    created = _fetch_seeded(case, db, base_date)

    # If demo tables were empty when DEMO_SCN_* was queried, auto-seed and retry
    if created == 0 and case.transaction_id.startswith("DEMO_SCN_"):
        count = db.query(PaymentGatewayRecord).count()
        if count == 0:
            try:
                from scripts.seed_evidence_db import seed_db
                seed_db()
                created = _fetch_seeded(case, db, base_date)
            except Exception as e:
                logger.warning("Could not auto-seed demo records: %s", e)

    if created == 0:
        txn_id = case.transaction_id
        is_seeded_id = any(txn_id.startswith(p) for p in SEEDED_ID_PREFIXES)
        if not is_seeded_id:
            created = _fetch_dynamic(case, db, base_date)

    return created
