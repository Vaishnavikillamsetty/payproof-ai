"""
Case Orchestrator — runs the full pipeline for a single case.

Pipeline order:
  1. Fetch external evidence       (DB query / RazorpayProvider)
  2. Collect evidence              (DB query, deterministic)
  3. Run rule engine               (deterministic if/else checks)
  4. Completeness score            (deterministic)
  5. DisputeInvestigationAgent     (bounded AI tool-calling agent)
  6. Policy gate                   (deterministic threshold check)
  7. Write every step to audit_log

The AI agent (step 5) investigates the case using controlled tools,
gathers evidence-grounded findings, and recommends an action.
The policy gate (step 6) constrains the recommendation using numeric
thresholds and can override unsafe AI outputs.

Every step is written to audit_log before the next step begins, so the
trail is complete even if the orchestrator crashes mid-run.
"""

import json
import logging
from uuid import UUID

from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.db.models import AuditLog, Case, Claim, Evidence, RuleFlag
from app.agents.evidence_collector import collect_evidence
from app.agents.external_systems import fetch_external_evidence
from app.agents.investigation_agent import investigate
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


def _derive_claims_from_evidence(evidence_list, rule_results) -> list[str]:
    """
    Dynamically derive verifiable claims from actual collected evidence
    and deterministic rule results — NOT from hardcoded dispute-reason strings.

    Each claim is a factual statement about what evidence EXISTS (or doesn't).
    """
    claims = []
    present_types = {e.evidence_type for e in evidence_list}

    if "payment" in present_types:
        payment_ev = next(e for e in evidence_list if e.evidence_type == "payment")
        amount = payment_ev.content.get("amount", "unknown")
        status = payment_ev.content.get("status", "unknown")
        claims.append(f"Payment of {amount} was found with status '{status}'.")

    if "delivery" in present_types:
        delivery_ev = next(e for e in evidence_list if e.evidence_type == "delivery")
        d_status = delivery_ev.content.get("status", "unknown")
        signed_by = delivery_ev.content.get("signed_by", "unknown")
        claims.append(f"Delivery record shows status '{d_status}', signed by '{signed_by}'.")

    if "otp" in present_types:
        otp_ev = next(e for e in evidence_list if e.evidence_type == "otp")
        verified = otp_ev.content.get("verified", False)
        claims.append(f"OTP/authentication verification: {'completed successfully' if verified else 'not verified'}.")

    if "communication" in present_types:
        comm_ev = next(e for e in evidence_list if e.evidence_type == "communication")
        channel = comm_ev.content.get("channel", "unknown")
        claims.append(f"Customer communication via {channel} is available.")

    # Record any triggered rules as factual claims
    triggered_rules = [(name, detail) for name, trig, detail in rule_results if trig]
    for rule_name, detail in triggered_rules:
        claims.append(f"Rule '{rule_name}' triggered: {detail}")

    if not claims:
        claims.append("No evidence records were found for this case.")

    return claims


# --------------------------------------------------------------------------- #
# Main pipeline                                                               #
# --------------------------------------------------------------------------- #

def run_pipeline(case_id: UUID, db: Session | None = None) -> None:
    """
    Execute the full evidence-verification pipeline for a case.
    Updates the Case row in-place and writes a complete audit trail.
    """
    _owns_session = db is None
    if _owns_session:
        db = SessionLocal()

    try:
        case = db.query(Case).filter(Case.id == case_id).first()
        if not case:
            logger.error("run_pipeline: case %s not found", case_id)
            return

        # -------------------------------------------------------------- #
        # Step 0: Fetch external evidence if none exists                  #
        # -------------------------------------------------------------- #
        existing_evidence_count = (
            db.query(Evidence).filter(Evidence.case_id == case_id).count()
        )
        if existing_evidence_count == 0:
            logger.info("case %s: no existing evidence. Querying external systems...", case_id)
            created = fetch_external_evidence(case, db)
            _audit(db, case_id, "external_evidence_fetched", {"records_created": created})
            if created > 0:
                logger.info("case %s: retrieved %d evidence records.", case_id, created)
            else:
                logger.info("case %s: no external records found.", case_id)

        # ------------------------------------------------------------------ #
        # Step 1: Collect evidence                                            #
        # ------------------------------------------------------------------ #
        evidence_list = collect_evidence(case_id, db)
        evidence_types = list({e.evidence_type for e in evidence_list})
        logger.info(
            "case %s: collected %d evidence record(s) — types: [%s]",
            case_id, len(evidence_list), ", ".join(evidence_types),
        )

        evidence_summary = [
            {"id": str(e.id), "type": e.evidence_type, "source_id": e.source_id}
            for e in evidence_list
        ]
        _audit(db, case_id, "evidence_collected", {
            "count": len(evidence_list),
            "types": evidence_types,
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

        _audit(db, case_id, "rules_checked", {
            "flags": [
                {"rule": name, "triggered": trig, "detail": det}
                for name, trig, det in rule_results
            ]
        })

        contradictions_found = any(trig for _, trig, _ in rule_results)

        # ------------------------------------------------------------------ #
        # Step 3: Completeness score                                          #
        # ------------------------------------------------------------------ #
        score, missing = completeness_score(evidence_list)

        _audit(db, case_id, "completeness_scored", {
            "score": score,
            "missing_evidence": missing,
        })

        # ------------------------------------------------------------------ #
        # Step 4: Dynamic claim derivation (evidence-driven, not hardcoded)   #
        # ------------------------------------------------------------------ #
        claim_texts = _derive_claims_from_evidence(evidence_list, rule_results)
        _audit(db, case_id, "claims_derived", {"claims": claim_texts})

        for claim_text in claim_texts:
            db.add(Claim(
                case_id=case_id,
                claim_text=claim_text,
                confidence=None,
                verdict=None,
                supporting_evidence_ids=[],
                contradicting_evidence_ids=[],
            ))
        db.commit()

        # ------------------------------------------------------------------ #
        # Step 5: DisputeInvestigationAgent                                   #
        # ------------------------------------------------------------------ #
        _audit(db, case_id, "agent_investigation_started", {
            "evidence_types": evidence_types,
            "completeness": score,
            "contradictions_found": contradictions_found,
        })

        recommendation = investigate(
            case_id=str(case_id),
            db=db,
            evidence_types=evidence_types,
            contradictions_found=contradictions_found,
            completeness=score,
        )

        _audit(db, case_id, "agent_recommendation_created", {
            "recommended_action": recommendation.recommended_action.value,
            "confidence": recommendation.confidence,
            "risk_level": recommendation.risk_level.value,
            "evidence_strength": recommendation.evidence_strength.value,
            "summary": recommendation.summary,
            "missing_evidence": recommendation.missing_evidence,
            "contradictions": recommendation.contradictions,
            "ai_status": recommendation.ai_status,
            "source_status": recommendation.source_status.value,
        })

        if recommendation.ai_status == "FALLBACK":
            _audit(db, case_id, "agent_fallback_used", {
                "reason": "AI agent failed — used deterministic fallback",
            })

        # ------------------------------------------------------------------ #
        # Step 6: Policy gate — constrains the agent recommendation           #
        # ------------------------------------------------------------------ #
        avg_confidence = recommendation.confidence
        status, reason = policy_decision(score, avg_confidence, contradictions_found)

        _audit(db, case_id, "policy_decision", {
            "status": status,
            "reason": reason,
            "completeness": score,
            "agent_confidence": avg_confidence,
            "agent_recommendation": recommendation.recommended_action.value,
            "contradictions_found": contradictions_found,
        })

        # ------------------------------------------------------------------ #
        # Update case with final scores                                       #
        # ------------------------------------------------------------------ #
        case.status = status
        case.completeness_score = score
        case.overall_confidence = round(avg_confidence, 4)
        db.commit()

        logger.info(
            "case %s: pipeline complete — status=%s completeness=%d confidence=%.3f agent_action=%s ai_status=%s",
            case_id, status, score, avg_confidence,
            recommendation.recommended_action.value,
            recommendation.ai_status,
        )

    finally:
        if _owns_session:
            db.close()
