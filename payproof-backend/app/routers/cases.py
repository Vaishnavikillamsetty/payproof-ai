import logging
from datetime import datetime, timezone
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, Header, HTTPException, Request
from sqlalchemy.orm import Session

from app.db.models import AuditLog, Case, Evidence, PaymentGatewayRecord
from app.db.session import get_db
from app.agents.external_systems import get_demo_expected_amount, _get_base_demo_id
from app.orchestrator import run_pipeline
from app.lifecycle import lifecycle_after_human_review, lifecycle_after_resolution, lifecycle_after_close
from app.config import settings
from app.auth import get_current_reviewer_id
from app.evidence_categories import (
    map_to_canonical_category,
    compute_category_coverage,
    evaluate_evidence_strength,
)
from app.schemas import (
    AuditLogResponse,
    CaseActionRequest,
    CaseCreate,
    CaseDetailResponse,
    CaseResponse,
    EvidenceResponse,
    EvidenceUploadRequest,
    HumanReviewRequest,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/cases", tags=["cases"])


@router.post("/", response_model=CaseResponse, status_code=201)
def create_case(
    case_in: CaseCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    """
    Submit a new dispute case.
    Initial state is 'OPEN' with bounded automatic investigation queued.
    """
    final_amount = case_in.amount

    # For seeded demo transactions, backend is authoritative
    demo_amount = get_demo_expected_amount(db, case_in.transaction_id)
    base_id = _get_base_demo_id(case_in.transaction_id)
    pmt = db.query(PaymentGatewayRecord).filter_by(transaction_id=base_id).first()
    final_currency = pmt.currency if pmt else "UNKNOWN"

    if demo_amount is not None:
        final_amount = demo_amount
    else:
        if final_amount <= 0:
            raise HTTPException(status_code=400, detail="Amount must be greater than 0.")

    db_case = Case(
        transaction_id=case_in.transaction_id,
        dispute_reason=case_in.dispute_reason,
        customer_claim=case_in.customer_claim,
        merchant_id=case_in.merchant_id,
        amount=final_amount,
        currency=final_currency,
        status="OPEN",
        evidence_strength="NOT_EVALUATED",
    )
    db.add(db_case)
    db.commit()
    db.refresh(db_case)

    # Queue background evidence collection & investigation
    background_tasks.add_task(run_pipeline, db_case.id)

    db_case.__dict__["categories_available"] = []
    db_case.__dict__["category_count"] = 0
    db_case.__dict__["evidence_types"] = []
    return db_case


@router.get("/demo-info/{transaction_id}")
def get_demo_info(transaction_id: str, db: Session = Depends(get_db)):
    expected_amount = get_demo_expected_amount(db, transaction_id)
    if expected_amount is not None:
        return {"is_demo": True, "expected_amount": expected_amount}
    return {"is_demo": False}


@router.get("/", response_model=List[CaseResponse])
def get_cases(db: Session = Depends(get_db)):
    """
    Return all cases for the dashboard list view with accurate category availability.
    """
    cases = (
        db.query(Case)
        .order_by(Case.created_at.desc())
        .all()
    )

    if cases:
        case_ids = [c.id for c in cases]
        # Query all evidence records for these cases to derive canonical categories accurately
        ev_rows = (
            db.query(Evidence.case_id, Evidence.evidence_type, Evidence.category)
            .filter(Evidence.case_id.in_(case_ids))
            .all()
        )

        ev_by_case: dict[UUID, list] = {}
        for row in ev_rows:
            ev_by_case.setdefault(row.case_id, []).append(row)

        for c in cases:
            items = ev_by_case.get(c.id, [])
            cats, count = compute_category_coverage(items)
            c.__dict__["categories_available"] = cats
            c.__dict__["category_count"] = count
            c.__dict__["evidence_types"] = list({r.evidence_type for r in items})
            if not c.evidence_strength:
                c.__dict__["evidence_strength"] = evaluate_evidence_strength(items, cats, c.contradiction_detected)

    return cases


@router.get("/{id}", response_model=CaseDetailResponse)
def get_case(id: UUID, db: Session = Depends(get_db)):
    db_case = db.query(Case).filter(Case.id == id).first()
    if not db_case:
        raise HTTPException(status_code=404, detail="Case not found")

    ev_list = db_case.evidence or []
    cats, count = compute_category_coverage(ev_list)
    db_case.__dict__["categories_available"] = cats
    db_case.__dict__["category_count"] = count
    db_case.__dict__["evidence_types"] = [e.evidence_type for e in ev_list]
    if not db_case.evidence_strength:
        db_case.__dict__["evidence_strength"] = evaluate_evidence_strength(ev_list, cats, db_case.contradiction_detected)

    return db_case


@router.get("/{id}/audit", response_model=List[AuditLogResponse])
def get_audit(id: UUID, db: Session = Depends(get_db)):
    """Return the complete immutable audit trail in chronological order."""
    return (
        db.query(AuditLog)
        .filter(AuditLog.case_id == id)
        .order_by(AuditLog.timestamp)
        .all()
    )


@router.post("/{id}/review", response_model=CaseDetailResponse)
def review_case(
    id: UUID,
    req: HumanReviewRequest,
    reviewer_id: str = Depends(get_current_reviewer_id),
    db: Session = Depends(get_db),
):
    """
    Record a human review decision without conflating it with AI recommendation.
    - APPROVE / CONTEST -> sets human_decision and moves lifecycle to DECISION_RECORDED.
    - REQUEST_MORE_EVIDENCE -> sets human_decision and moves lifecycle to EVIDENCE_REQUESTED.
    - Double-click protection: Rejects duplicate submissions if already reviewed in current cycle.
    - Preserves previous human review decisions in the immutable audit log.
    """
    case = db.query(Case).filter(Case.id == id).first()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")

    action_norm = req.action.strip().lower()
    if action_norm not in ["approve", "contest", "request_more_evidence"]:
        raise HTTPException(status_code=400, detail="Invalid action. Must be approve, contest, or request_more_evidence.")

    # Check for duplicate decision submission in the current review cycle
    last_decision = (
        db.query(AuditLog)
        .filter(AuditLog.case_id == case.id, AuditLog.step == "human_review_decision")
        .order_by(AuditLog.timestamp.desc())
        .first()
    )

    # Check if new evidence was uploaded since the last decision
    has_new_evidence_since_decision = False
    if last_decision:
        new_ev = (
            db.query(Evidence)
            .filter(Evidence.case_id == case.id, Evidence.collected_at > last_decision.timestamp)
            .first()
        )
        if new_ev:
            has_new_evidence_since_decision = True

    # If decision was already made in current cycle and no new evidence was added -> reject duplicate submit
    if last_decision and not has_new_evidence_since_decision and case.status != "EVIDENCE_REQUESTED":
        raise HTTPException(
            status_code=409,
            detail="A human review decision has already been recorded for this case cycle.",
        )

    # Dynamic reviewer ID from auth / headers / request context
    final_reviewer = req.reviewer_id or reviewer_id

    # Update Case fields
    case.human_decision = req.action.upper()
    case.final_action = req.action.upper()
    case.reviewer_id = final_reviewer
    case.decision_timestamp = datetime.now(timezone.utc)
    case.reviewer_notes = req.notes
    case.status = lifecycle_after_human_review(case.ai_recommendation, action_norm)

    # Append to immutable audit log
    db.add(AuditLog(
        case_id=case.id,
        step="human_review_decision",
        detail={
            "action": req.action.upper(),
            "notes": req.notes,
            "reviewer_id": final_reviewer,
            "ai_recommendation": case.ai_recommendation,
            "lifecycle_status": case.status,
            "timestamp": str(case.decision_timestamp),
        }
    ))
    db.commit()
    db.refresh(case)

    # Attach computed fields
    ev_list = case.evidence or []
    cats, count = compute_category_coverage(ev_list)
    case.__dict__["categories_available"] = cats
    case.__dict__["category_count"] = count
    case.__dict__["evidence_types"] = [e.evidence_type for e in ev_list]
    case.__dict__["evidence_strength"] = evaluate_evidence_strength(ev_list, cats, case.contradiction_detected)

    return case


@router.post("/{id}/evidence", response_model=EvidenceResponse, status_code=201)
def upload_evidence(
    id: UUID,
    req: EvidenceUploadRequest,
    background_tasks: BackgroundTasks,
    reviewer_id: str = Depends(get_current_reviewer_id),
    db: Session = Depends(get_db),
):
    """
    Upload and persist additional evidence for a case.
    - Persists metadata and payload inside PostgreSQL to survive Render restarts.
    - Assigns canonical category (keeps unknown types uncategorized).
    - Recalculates category coverage and evidence strength.
    - If case was in EVIDENCE_REQUESTED, triggers AI re-analysis without altering previous human decisions.
    """
    case = db.query(Case).filter(Case.id == id).first()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")

    # Map category strictly according to canonical rules
    # NEVER map unknown types to 'merchant'
    canonical_cat = map_to_canonical_category(req.evidence_type, category_override=req.category)

    # Build persistent content dict surviving Render filesystem restarts
    stored_content = dict(req.content or {})
    if req.file_base64:
        stored_content["file_base64"] = req.file_base64
    stored_content["uploaded_by"] = reviewer_id

    ev = Evidence(
        case_id=case.id,
        evidence_type=req.evidence_type,
        category=canonical_cat,
        filename=req.filename or f"evidence_{len(case.evidence or []) + 1}.json",
        description=req.description or f"Uploaded {canonical_cat or 'uncategorized'} evidence",
        verification_status=req.verification_status or "unverified",
        content=stored_content,
        event_timestamp=datetime.now(timezone.utc),
    )
    db.add(ev)

    # Append to audit log
    db.add(AuditLog(
        case_id=case.id,
        step="evidence_uploaded",
        detail={
            "evidence_type": req.evidence_type,
            "category": canonical_cat,
            "filename": ev.filename,
            "uploaded_by": reviewer_id,
        }
    ))
    db.commit()
    db.refresh(ev)

    # Recalculate case category coverage & strength
    all_ev = db.query(Evidence).filter(Evidence.case_id == case.id).all()
    cats, count = compute_category_coverage(all_ev)
    case.evidence_strength = evaluate_evidence_strength(all_ev, cats, case.contradiction_detected)
    db.commit()

    # Multi-cycle re-investigation: trigger pipeline re-run to allow AI re-analysis
    background_tasks.add_task(run_pipeline, case.id)

    return ev


@router.post("/{id}/resolve", response_model=CaseDetailResponse)
def resolve_case(
    id: UUID,
    req: CaseActionRequest,
    reviewer_id: str = Depends(get_current_reviewer_id),
    db: Session = Depends(get_db),
):
    """
    Explicit authorized workflow to transition a case to RESOLVED.
    Never happens automatically.
    """
    case = db.query(Case).filter(Case.id == id).first()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")

    # Require decision to be recorded or authorized reviewer note
    final_reviewer = req.reviewer_id or reviewer_id
    case.status = lifecycle_after_resolution(case.status)

    db.add(AuditLog(
        case_id=case.id,
        step="case_resolved",
        detail={
            "reviewer_id": final_reviewer,
            "notes": req.notes,
            "human_decision": case.human_decision,
            "resolved_at": str(datetime.now(timezone.utc)),
        }
    ))
    db.commit()
    db.refresh(case)

    ev_list = case.evidence or []
    cats, count = compute_category_coverage(ev_list)
    case.__dict__["categories_available"] = cats
    case.__dict__["category_count"] = count
    case.__dict__["evidence_types"] = [e.evidence_type for e in ev_list]
    case.__dict__["evidence_strength"] = evaluate_evidence_strength(ev_list, cats, case.contradiction_detected)
    return case


@router.post("/{id}/close", response_model=CaseDetailResponse)
def close_case(
    id: UUID,
    req: CaseActionRequest,
    reviewer_id: str = Depends(get_current_reviewer_id),
    db: Session = Depends(get_db),
):
    """
    Explicit authorized workflow to transition a case to CLOSED.
    """
    case = db.query(Case).filter(Case.id == id).first()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")

    final_reviewer = req.reviewer_id or reviewer_id
    case.status = lifecycle_after_close(case.status)

    db.add(AuditLog(
        case_id=case.id,
        step="case_closed",
        detail={
            "reviewer_id": final_reviewer,
            "notes": req.notes,
            "human_decision": case.human_decision,
            "closed_at": str(datetime.now(timezone.utc)),
        }
    ))
    db.commit()
    db.refresh(case)

    ev_list = case.evidence or []
    cats, count = compute_category_coverage(ev_list)
    case.__dict__["categories_available"] = cats
    case.__dict__["category_count"] = count
    case.__dict__["evidence_types"] = [e.evidence_type for e in ev_list]
    case.__dict__["evidence_strength"] = evaluate_evidence_strength(ev_list, cats, case.contradiction_detected)
    return case


@router.delete("/demo-reset")
def reset_demo_cases(db: Session = Depends(get_db)):
    """
    Deletes all demo cases to provide a clean state for testing/demo.
    Does not delete real production cases.
    """
    if settings.environment != "development" and not settings.demo_mode:
        raise HTTPException(status_code=403, detail="Demo reset is disabled in this environment.")
    demo_cases = db.query(Case).filter(
        (Case.transaction_id.like("DEMO_TXN_%")) | 
        (Case.transaction_id.like("DEMO_SCN_%"))
    ).all()
    
    count = len(demo_cases)
    for c in demo_cases:
        db.query(AuditLog).filter(AuditLog.case_id == c.id).delete(synchronize_session=False)
        db.query(Evidence).filter(Evidence.case_id == c.id).delete(synchronize_session=False)
        from app.db.models import RuleFlag, Claim
        db.query(RuleFlag).filter(RuleFlag.case_id == c.id).delete(synchronize_session=False)
        db.query(Claim).filter(Claim.case_id == c.id).delete(synchronize_session=False)
        db.delete(c)
    
    db.commit()
    return {"status": "success", "deleted": count}
