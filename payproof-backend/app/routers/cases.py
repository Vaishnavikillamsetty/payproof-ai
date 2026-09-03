import logging
from typing import List
from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.models import AuditLog, Case, Evidence
from app.db.session import get_db
from app.agents.external_systems import get_demo_expected_amount
from app.orchestrator import run_pipeline
from app.schemas import AuditLogResponse, CaseCreate, CaseDetailResponse, CaseResponse, HumanReviewRequest

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/cases", tags=["cases"])


@router.post("/", response_model=CaseResponse, status_code=201)
def create_case(
    case_in: CaseCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    """
    Submit a new dispute.
    """
    final_amount = case_in.amount

    # For seeded demo transactions, the backend is authoritative.
    # Automatically override the user's amount with the exact seeded amount.
    demo_amount = get_demo_expected_amount(db, case_in.transaction_id)
    if demo_amount is not None:
        final_amount = demo_amount
    else:
        # For arbitrary/dynamic transactions, the user must provide a valid amount > 0.
        if final_amount <= 0:
            raise HTTPException(status_code=400, detail="Amount must be greater than 0.")

    db_case = Case(
        transaction_id=case_in.transaction_id,
        dispute_reason=case_in.dispute_reason,
        customer_claim=case_in.customer_claim,
        merchant_id=case_in.merchant_id,
        amount=final_amount,
        status="new",
    )
    db.add(db_case)
    db.commit()
    db.refresh(db_case)

    background_tasks.add_task(run_pipeline, db_case.id)

    return db_case


@router.get("/demo-info/{transaction_id}")
def get_demo_info(transaction_id: str, db: Session = Depends(get_db)):
    """
    Check if a transaction ID corresponds to a seeded demo case,
    and return its authoritative expected amount.
    """
    expected_amount = get_demo_expected_amount(db, transaction_id)
    if expected_amount is not None:
        return {"is_demo": True, "expected_amount": expected_amount}
    return {"is_demo": False}


@router.get("/", response_model=List[CaseResponse])
def get_cases(db: Session = Depends(get_db)):
    """
    Return all cases for the dashboard list view.

    Performance: Instead of joinedload(Case.evidence) which pulls every
    evidence row just to extract type strings, we run a single lightweight
    query for distinct evidence_types per case and attach them in Python.
    This avoids transmitting large JSONB content columns over the wire.
    """
    cases = (
        db.query(Case)
        .order_by(Case.created_at.desc())
        .all()
    )

    if cases:
        case_ids = [c.id for c in cases]
        # Single query: get distinct evidence types grouped by case_id
        ev_rows = (
            db.query(Evidence.case_id, Evidence.evidence_type)
            .filter(Evidence.case_id.in_(case_ids))
            .distinct()
            .all()
        )
        # Build a lookup: case_id -> list of evidence type strings
        ev_map: dict[UUID, list[str]] = {}
        for case_id, ev_type in ev_rows:
            ev_map.setdefault(case_id, []).append(ev_type)

        # Attach to each case so the schema validator can read them
        for c in cases:
            c.__dict__["evidence_types"] = ev_map.get(c.id, [])

    return cases


@router.get("/{id}", response_model=CaseDetailResponse)
def get_case(id: UUID, db: Session = Depends(get_db)):
    db_case = db.query(Case).filter(Case.id == id).first()
    if not db_case:
        raise HTTPException(status_code=404, detail="Case not found")
    return db_case


@router.get("/{id}/audit", response_model=List[AuditLogResponse])
def get_audit(id: UUID, db: Session = Depends(get_db)):
    """Return the full, immutable audit trail for a case in chronological order."""
    # Query audit logs directly — if none exist, the case either doesn't exist
    # or simply has no audit entries yet. Both are fine to return as [].
    return (
        db.query(AuditLog)
        .filter(AuditLog.case_id == id)
        .order_by(AuditLog.timestamp)
        .all()
    )


@router.post("/{id}/review", response_model=CaseDetailResponse)
def review_case(id: UUID, req: HumanReviewRequest, db: Session = Depends(get_db)):
    """
    Record a human review decision without taking immediate financial action.
    This sets the case status to reflect the decision.
    """
    case = db.query(Case).filter(Case.id == id).first()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")

    if req.action not in ["approve", "request_more_evidence", "escalate"]:
        raise HTTPException(status_code=400, detail="Invalid action")

    # Map the UI action to a valid case status
    # Note: approve will resolve the case, request_more_evidence / escalate match the DB status enum
    if req.action == "escalate":
        case.status = "escalate"
    elif req.action == "request_more_evidence":
        case.status = "request_more_evidence"
    elif req.action == "approve":
        case.status = "resolved"

    db.add(AuditLog(
        case_id=case.id,
        step="human_review_decision",
        detail={"action": req.action, "notes": req.notes}
    ))
    db.commit()
    db.refresh(case)
    
    return case
