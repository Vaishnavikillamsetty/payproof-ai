"""
external_systems.py — Mock external evidence lookup.

Primary path: queries 4 seeded DB tables by transaction_id (ext_payment_gateway,
ext_delivery, ext_otp_log, ext_communication_log).

Dynamic fallback: if no seeded records exist for a transaction_id, uses a
deterministic hash of the ID to generate a realistic evidence profile, so that
any arbitrary transaction ID entered in the UI produces a meaningful, varied outcome
rather than always defaulting to human_review.

Scenario distribution (deterministic by hash):
  hash % 10 in 0-3  (40%) → full evidence  → strong_case  (payment+delivery+otp+comms)
  hash % 10 in 4-6  (30%) → sparse evidence → weak_case    (payment only)
  hash % 10 in 7-8  (20%) → contradiction   → human_review (payment+delivery vs "not received")
  hash % 10 == 9    (10%) → zero evidence   → human_review (no records at all)
"""

import hashlib
from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from app.db.models import (
    CommunicationLog,
    DeliveryRecord,
    Evidence,
    OtpLog,
    PaymentGatewayRecord,
)

DEMO_NOTE = "[DEMO] Retrieved from seeded external system mock"
FALLBACK_NOTE = "[DEMO] Dynamically generated for demonstration"


# --------------------------------------------------------------------------- #
# Helpers
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
        
    # Check if it has a seeded payment record first
    payment = db.query(PaymentGatewayRecord).filter_by(transaction_id=base_id).first()
    if payment:
        return float(payment.amount)
        
    # Hardcoded overrides for specific empty/edge-case demo IDs that deliberately lack payment records
    if transaction_id == "DEMO_TXN_EMPTY_1":
        return 150.0
        
    # If it starts with DEMO_TXN_ but isn't seeded and isn't EMPTY_1, 
    # it's an unknown/invalid demo ID. We don't have an expected amount.
    return None


def _add_evidence(db: Session, case, ev_type: str, source_id, content: dict,
                  event_timestamp: datetime, note: str) -> None:
    db.add(Evidence(
        case_id=case.id,
        evidence_type=ev_type,
        source_id=source_id,
        content={**content, "note": note},
        event_timestamp=event_timestamp,
    ))


# --------------------------------------------------------------------------- #
# Seeded DB lookup (primary path)
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
                      rec.timestamp or base_date, DEMO_NOTE)
        created += 1

    for rec in db.query(DeliveryRecord).filter(
        DeliveryRecord.transaction_id == base_id
    ).all():
        _add_evidence(db, case, "delivery", rec.tracking_number,
                      {"status": rec.status, "signed_by": rec.signed_by,
                       "address_match": rec.address_match, "notes": rec.notes},
                      rec.timestamp or base_date, DEMO_NOTE)
        created += 1

    for rec in db.query(OtpLog).filter(
        OtpLog.transaction_id == base_id
    ).all():
        _add_evidence(db, case, "otp", None,
                      {"verified": rec.verified, "ip_address": rec.ip_address},
                      rec.timestamp or base_date, DEMO_NOTE)
        created += 1

    for rec in db.query(CommunicationLog).filter(
        CommunicationLog.transaction_id == base_id
    ).all():
        _add_evidence(db, case, "communication", None,
                      {"channel": rec.channel, "message": rec.message,
                       "has_attachments": rec.has_attachments},
                      rec.timestamp or base_date, DEMO_NOTE)
        created += 1

    if created:
        db.commit()
    return created


# --------------------------------------------------------------------------- #
# Dynamic fallback (any unknown transaction_id)
# --------------------------------------------------------------------------- #

def _fetch_dynamic(case, db: Session, base_date: datetime) -> int:
    """
    Generate a deterministic evidence profile based on a hash of the
    transaction_id so demo/test runs always produce the same scenario for
    the same ID, but different IDs produce varied outcomes.
    """
    bucket = _hash_scenario(case.transaction_id)
    amount = float(case.amount)
    created = 0

    if bucket <= 3:
        # ── Scenario A (40%): Full evidence → strong_case ──────────────────
        _add_evidence(db, case, "payment", case.transaction_id,
                      {"amount": amount, "currency": "INR", "status": "success"},
                      base_date, FALLBACK_NOTE)
        _add_evidence(db, case, "delivery", f"TRK-{case.transaction_id[-6:].upper()}",
                      {"status": "delivered", "signed_by": "Customer",
                       "address_match": True, "notes": "Delivered on time"},
                      base_date + timedelta(days=2), FALLBACK_NOTE)
        _add_evidence(db, case, "otp", None,
                      {"verified": True, "ip_address": "192.168.1.1"},
                      base_date, FALLBACK_NOTE)
        # Message intentionally includes "cancel" so the cancellation rule doesn't
        # fire for subscription disputes that have clear evidence.
        _add_evidence(db, case, "communication", None,
                      {"channel": "email",
                       "message": "Please cancel my subscription — I am disputing this charge.",
                       "has_attachments": False},
                      base_date + timedelta(days=1), FALLBACK_NOTE)
        created = 4

    elif bucket <= 6:
        # ── Scenario B (30%): Payment only → weak_case ─────────────────────
        _add_evidence(db, case, "payment", case.transaction_id,
                      {"amount": amount, "currency": "INR", "status": "success"},
                      base_date, FALLBACK_NOTE)
        created = 1

    elif bucket <= 8:
        # ── Scenario C (20%): Payment + contradicting delivery → human_review
        # Works most dramatically when dispute_reason is "product not received"
        _add_evidence(db, case, "payment", case.transaction_id,
                      {"amount": amount, "currency": "INR", "status": "success"},
                      base_date, FALLBACK_NOTE)
        _add_evidence(db, case, "delivery", f"TRK-{case.transaction_id[-6:].upper()}",
                      {"status": "delivered", "signed_by": "Front Desk",
                       "address_match": True,
                       "notes": "Signed and accepted at reception"},
                      base_date + timedelta(days=3), FALLBACK_NOTE)
        created = 2

    else:
        # ── Scenario D (10%): No evidence → human_review ───────────────────
        created = 0

    if created:
        db.commit()
    return created


# --------------------------------------------------------------------------- #
# Public API called by the orchestrator
# --------------------------------------------------------------------------- #

def fetch_external_evidence(case, db: Session) -> int:
    """
    Queries mock external systems for the given case.transaction_id.
    Copies matching records into the Evidence table.
    Returns the number of evidence records created.

    Strategy:
      1. Try the seeded DB tables first (exact DEMO_TXN_* records).
      2. If the ID is a known DEMO_TXN_* prefix ID, skip the fallback entirely
         (e.g. DEMO_TXN_EMPTY_1 must stay empty even if nothing is seeded).
      3. For any other arbitrary ID, use the deterministic hash-based fallback
         so demos always produce varied, realistic outcomes.
    """
    # IDs that are intentionally seeded (or intentionally empty) — never fallback
    SEEDED_ID_PREFIXES = ("DEMO_TXN_", "DEMO_SCN_")

    base_date = case.created_at or datetime.now(timezone.utc)

    created = _fetch_seeded(case, db, base_date)

    if created == 0:
        txn_id = case.transaction_id
        is_seeded_id = any(txn_id.startswith(p) for p in SEEDED_ID_PREFIXES)
        if not is_seeded_id:
            created = _fetch_dynamic(case, db, base_date)

    return created
