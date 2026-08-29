"""
Case Orchestrator — runs the full pipeline for a single case.

Pipeline order (per build-plan Section 3):
  1. Collect evidence          (DB query, deterministic)
  2. Run rule engine           (deterministic if/else checks)
  3. Derive per-case claims    (one claim per evidence type present)
  4. Verifier agent            (LLM, once per claim, strict JSON)
  5. Completeness score        (deterministic)
  6. Policy gate               (deterministic threshold check)
  7. Write every step to audit_log

Every step is written to audit_log before the next step begins, so the trail
is complete even if the orchestrator crashes mid-run.

The LLM (step 4) decides per-claim confidence only — it never decides
"fraud or not".  The policy gate (step 6) makes the final routing decision
based on numeric thresholds.
"""

import json
import logging
from uuid import UUID

from sqlalchemy.orm import Session

from app.db.models import AuditLog, Case, Claim, RuleFlag
from app.agents.evidence_collector import collect_evidence
from app.agents.verifier import VerifierParseError, verify_claim
from app.policy import completeness_score, policy_decision
from app.rules.engine import check_timeline_rules

logger = logging.getLogger(__name__)


# --------------------------------------------------------------------------- #
# Helpers                                                                     #
# --------------------------------------------------------------------------- #

def _audit(db: Session, case_id: UUID, step: str, detail: dict) -> None:
    """Append one immutable row to audit_log."""
    entry = AuditLog(case_id=case_id, step=step, detail=detail)
    db.add(entry)
    db.commit()


def _derive_claims(case, evidence_list) -> list[str]:
    """
    Build a small set of verifiable claim statements for this case.
    These are plain sentences that the verifier checks against the evidence.
    We keep this simple: one claim per dispute category.
    """
    claims = []

    if case.dispute_reason == "product not received":
        claims.append("The product was delivered to the customer.")

    if case.dispute_reason == "product not as described":
        claims.append("The product received matched the merchant's description.")

    if case.dispute_reason == "duplicate charge":
        claims.append("The customer was charged more than once for this transaction.")

    if case.dispute_reason == "subscription not cancelled":
        claims.append("The customer requested cancellation before the charge date.")

    if case.dispute_reason == "unauthorized transaction":
        claims.append("The transaction was authorized by the account holder.")

    # Universal claim present for every case
    claims.append(f"The disputed amount of {case.amount} matches the payment record.")

    return claims


# --------------------------------------------------------------------------- #
# Main pipeline                                                               #
# --------------------------------------------------------------------------- #

def run_pipeline(case_id: UUID, db: Session) -> None:
    """
    Execute the full evidence-verification pipeline for a case.
    Updates the Case row in-place and writes a complete audit trail.
    """
    case = db.query(Case).filter(Case.id == case_id).first()
    if not case:
        logger.error("run_pipeline: case %s not found", case_id)
        return

    # ------------------------------------------------------------------ #
    # Step 1: Collect evidence                                            #
    # ------------------------------------------------------------------ #
    evidence_list = collect_evidence(case_id, db)
    evidence_summary = [
        {"id": str(e.id), "type": e.evidence_type, "source_id": e.source_id}
        for e in evidence_list
    ]
    _audit(db, case_id, "evidence_collected", {
        "count": len(evidence_list),
        "items": evidence_summary,
    })

    case.status = "investigating"
    db.commit()

    # ------------------------------------------------------------------ #
    # Step 2: Run rule engine                                             #
    # ------------------------------------------------------------------ #
    rule_results = check_timeline_rules(case, evidence_list)

    for rule_name, triggered, detail in rule_results:
        db.add(RuleFlag(
            case_id=case_id,
            rule_name=rule_name,
            triggered=triggered,
            detail=detail,
        ))
    db.commit()

    _audit(db, case_id, "rule_checked", {
        "flags": [
            {"rule": name, "triggered": trig, "detail": det}
            for name, trig, det in rule_results
        ]
    })

    contradictions_found = any(trig for _, trig, _ in rule_results)

    # ------------------------------------------------------------------ #
    # Step 3: Derive claims                                               #
    # ------------------------------------------------------------------ #
    claim_texts = _derive_claims(case, evidence_list)
    _audit(db, case_id, "claims_derived", {"claims": claim_texts})

    # ------------------------------------------------------------------ #
    # Step 4: Verifier agent — one LLM call per claim                    #
    # ------------------------------------------------------------------ #
    evidence_dicts = [
        {
            "evidence_type": e.evidence_type,
            "source_id": e.source_id,
            "content": e.content,
            "event_timestamp": str(e.event_timestamp),
        }
        for e in evidence_list
    ]

    claim_rows = []
    confidence_values = []

    for claim_text in claim_texts:
        try:
            result = verify_claim(claim_text, evidence_dicts)
            verdict = result["verdict"]
            confidence = result["confidence"]
            reasoning = result["reasoning"]
        except VerifierParseError as exc:
            # Hard failure: log it, mark unverifiable, do NOT guess
            logger.error("VerifierParseError for claim %r: %s", claim_text, exc)
            verdict = "unverifiable"
            confidence = 0.0
            reasoning = f"System error during verification: {exc}"
            _audit(db, case_id, "verifier_parse_error", {
                "claim": claim_text,
                "error": str(exc),
            })

        claim_row = Claim(
            case_id=case_id,
            claim_text=claim_text,
            confidence=confidence,
            verdict=verdict,
            # evidence IDs are not split per-claim at this stage; done in Phase 4
            supporting_evidence_ids=[],
            contradicting_evidence_ids=[],
        )
        db.add(claim_row)
        claim_rows.append(claim_row)
        confidence_values.append(confidence)

        _audit(db, case_id, "claim_verified", {
            "claim": claim_text,
            "verdict": verdict,
            "confidence": confidence,
            "reasoning": reasoning,
        })

    db.commit()

    # ------------------------------------------------------------------ #
    # Step 5: Completeness score                                          #
    # ------------------------------------------------------------------ #
    score, missing = completeness_score(evidence_list)
    avg_confidence = (
        sum(confidence_values) / len(confidence_values)
        if confidence_values else 0.0
    )

    _audit(db, case_id, "completeness_scored", {
        "score": score,
        "missing_evidence": missing,
        "avg_confidence": round(avg_confidence, 4),
    })

    # ------------------------------------------------------------------ #
    # Step 6: Policy gate                                                 #
    # ------------------------------------------------------------------ #
    status, reason = policy_decision(score, avg_confidence, contradictions_found)

    _audit(db, case_id, "policy_decision", {
        "status": status,
        "reason": reason,
        "completeness": score,
        "avg_confidence": round(avg_confidence, 4),
        "contradictions_found": contradictions_found,
    })

    # ------------------------------------------------------------------ #
    # Update case with final scores                                       #
    # ------------------------------------------------------------------ #
    case.status = status
    case.completeness_score = score
    case.overall_confidence = round(avg_confidence, 4)
    db.commit()
