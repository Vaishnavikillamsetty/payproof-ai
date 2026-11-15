"""
DisputeInvestigationAgent — bounded AI agent.

Architecture:
  - Primary LLM: Claude 3.5 Sonnet (via Anthropic SDK)
  - Secondary LLM: OpenRouter (if OPENROUTER_API_KEY is configured)
  - Mock Mode: Deterministic mock agent for tests and demos (settings.mock_verifier)
  - Evidence is gathered directly in Python via tool functions and structured into
    the 4 canonical categories: TRANSACTION, CUSTOMER, DELIVERY, MERCHANT.
  - LLM receives complete dispute context and responds with a JSON recommendation.
  - Safe error handling: If the API call fails, explicitly records AI_ANALYSIS_UNAVAILABLE
    or deterministic fallback without fabricating silent fake live recommendations.
  - Never stores chain-of-thought; only evidence-grounded findings.
  - Never overwrites recorded human decisions.
"""

import json
import logging
from typing import Optional
import httpx
from sqlalchemy.orm import Session
from pydantic import ValidationError

from app.config import settings
from app.agents.schemas import (
    AgentRecommendation,
    Finding,
    RecommendedAction,
    RiskLevel,
    EvidenceStrength,
    SourceStatus,
)
from app.agents.tools import execute_tool
from app.evidence_categories import map_to_canonical_category, CANONICAL_CATEGORIES

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """\
You are PayProof AI — a dispute investigation agent for payment risk analysis.

GOAL: Investigate a payment dispute by reviewing the provided dispute details and evidence categorized into:
1. TRANSACTION EVIDENCE (gateway records, amounts, timestamps, refund status)
2. CUSTOMER EVIDENCE (customer communications, authentication, OTP logs)
3. DELIVERY / FULFILMENT EVIDENCE (tracking, delivery confirmations, proof of receipt)
4. MERCHANT EVIDENCE (refund policy, merchant notes, invoices, receipts)

RULES:
1. Base your recommendation ONLY on actual evidence data provided in the user prompt.
2. Do NOT invent evidence or claim that an unprovided document exists.
3. If evidence is missing or insufficient for a safe decision, recommend REQUEST_MORE_EVIDENCE.
4. If valid evidence contradicts the customer claim, explain the contradiction and recommend CONTEST.
5. If evidence shows customer claim is justified (e.g. refund owed, cancelled before charge, duplicate charge), recommend APPROVE.
6. Always set human_approval_required to true. AI recommendation is advisory only.

Respond with ONLY a valid JSON object matching this exact schema (no markdown formatting, no backticks):
{
  "recommended_action": "APPROVE" | "CONTEST" | "REQUEST_MORE_EVIDENCE",
  "confidence": <float 0.0-1.0>,
  "risk_level": "LOW" | "MEDIUM" | "HIGH",
  "evidence_strength": "LOW" | "MEDIUM" | "HIGH",
  "summary": "<clear, factual explanation of findings and rationale>",
  "key_findings": [
    {"finding": "<factual observation>", "source": "<data source>", "importance": "high"|"medium"|"low"}
  ],
  "missing_evidence": ["<specific missing evidence type or category>"],
  "contradictions": ["<description of contradiction, if any>"],
  "human_approval_required": true,
  "source_status": "COMPLETE" | "PARTIAL" | "LIMITED"
}
"""


def _parse_final_json(text: str) -> AgentRecommendation:
    """Parse and validate the agent's final JSON output."""
    clean = text.strip()
    if clean.startswith("```"):
        lines = clean.split("\n")
        lines = [l for l in lines if not l.strip().startswith("```")]
        clean = "\n".join(lines).strip()

    start = clean.find("{")
    end = clean.rfind("}")
    if start != -1 and end != -1 and end > start:
        clean = clean[start:end + 1]

    data = json.loads(clean)
    return AgentRecommendation(**data)


def _deterministic_fallback(
    evidence_types: list[str],
    contradictions_found: bool,
    completeness: int,
    duplicate_payment_detected: bool = False,
    error_reason: str = "Deterministic safety fallback",
) -> AgentRecommendation:
    """Pure rule-based fallback recommendation."""
    if duplicate_payment_detected:
        action = RecommendedAction.APPROVE
        risk = RiskLevel.LOW
        strength = EvidenceStrength.HIGH
        summary = "Multiple successful payments detected for duplicate charge claim. Recommending APPROVE/refund."
        confidence = 0.90
    elif contradictions_found:
        action = RecommendedAction.ESCALATE
        risk = RiskLevel.HIGH
        strength = EvidenceStrength.MEDIUM
        summary = "Contradicting evidence detected. Deterministic fallback recommends escalation."
        confidence = 0.40
    elif "refund" in evidence_types:
        action = RecommendedAction.ACCEPT
        risk = RiskLevel.LOW
        strength = EvidenceStrength.HIGH
        summary = "Refund already processed. Deterministic fallback recommends accepting."
        confidence = 0.80
    elif completeness >= 50:
        action = RecommendedAction.CONTEST
        risk = RiskLevel.LOW
        strength = EvidenceStrength.HIGH
        summary = "Sufficient verified evidence available. Deterministic fallback recommends contesting."
        confidence = 0.70
    else:
        action = RecommendedAction.REQUEST_MORE_EVIDENCE
        risk = RiskLevel.MEDIUM if completeness >= 30 else RiskLevel.HIGH
        strength = EvidenceStrength.LOW
        summary = "Insufficient or missing evidence. Deterministic fallback recommends gathering more before contesting."
        confidence = 0.50 if completeness >= 30 else 0.20

    missing = []
    for et in ["payment", "delivery", "otp", "communication"]:
        if et not in evidence_types:
            missing.append(et)

    return AgentRecommendation(
        recommended_action=action,
        confidence=confidence,
        risk_level=risk,
        evidence_strength=strength,
        summary=summary,
        key_findings=[Finding(
            finding=f"Evidence types present: {', '.join(evidence_types) or 'none'}. {error_reason}",
            source="deterministic_fallback",
            importance="high",
            verified=False,
        )],
        missing_evidence=missing,
        contradictions=["Contradiction detected by rule engine"] if contradictions_found else [],
        human_approval_required=True,
        source_status=SourceStatus.COMPLETE if completeness >= 50 else SourceStatus.PARTIAL if completeness >= 30 else SourceStatus.LIMITED,
        ai_status="FALLBACK",
    )


def _mock_investigate(
    case_id: str,
    db: Session,
    evidence_types: list[str],
    contradictions_found: bool,
    completeness: int,
    duplicate_payment_detected: bool = False,
) -> AgentRecommendation:
    """Deterministic mock agent for demos and mock verification tests."""
    findings = []
    if "payment" in evidence_types:
        findings.append(Finding(finding="Payment record found and verified", source="payment_provider", importance="high", verified=True))
    if "delivery" in evidence_types:
        findings.append(Finding(finding="Delivery confirmation exists", source="merchant_delivery_system", importance="high", verified=False))
    if "otp" in evidence_types:
        findings.append(Finding(finding="OTP/authentication verification completed", source="auth_system", importance="medium", verified=False))
    if "communication" in evidence_types:
        findings.append(Finding(finding="Customer communication records available", source="communication_log", importance="medium", verified=False))

    if not findings:
        findings.append(Finding(finding="No evidence records found", source="evidence_search", importance="high", verified=False))

    missing = [et for et in ["payment", "delivery", "otp", "communication"] if et not in evidence_types]

    if contradictions_found:
        return AgentRecommendation(
            recommended_action=RecommendedAction.ESCALATE,
            confidence=0.45,
            risk_level=RiskLevel.HIGH,
            evidence_strength=EvidenceStrength.MEDIUM,
            summary="Contradicting evidence detected between customer claim and available records. Manual review recommended before any action.",
            key_findings=findings,
            missing_evidence=missing,
            contradictions=["Customer claim conflicts with available evidence records"],
            human_approval_required=True,
            source_status=SourceStatus.PARTIAL,
            ai_status="OK",
        )
    elif completeness >= 50:
        return AgentRecommendation(
            recommended_action=RecommendedAction.CONTEST,
            confidence=0.85,
            risk_level=RiskLevel.LOW,
            evidence_strength=EvidenceStrength.HIGH,
            summary="Strong evidence supports contesting this dispute. Payment, delivery, and supporting records are consistent.",
            key_findings=findings,
            missing_evidence=missing,
            contradictions=[],
            human_approval_required=True,
            source_status=SourceStatus.COMPLETE,
            ai_status="OK",
        )
    else:
        return AgentRecommendation(
            recommended_action=RecommendedAction.REQUEST_MORE_EVIDENCE,
            confidence=0.55 if completeness >= 30 else 0.20,
            risk_level=RiskLevel.MEDIUM if completeness >= 30 else RiskLevel.HIGH,
            evidence_strength=EvidenceStrength.LOW,
            summary="Insufficient evidence to safely recommend contesting. Recommend gathering delivery confirmation and communication records.",
            key_findings=findings,
            missing_evidence=missing,
            contradictions=[],
            human_approval_required=True,
            source_status=SourceStatus.PARTIAL if completeness >= 30 else SourceStatus.LIMITED,
            ai_status="OK",
        )


def _build_context(case_id: str, db: Session) -> str:
    """Gather case details and evidence categorized into the 4 canonical categories."""
    evidence_data = {}
    tool_names = ["get_case_details", "search_case_evidence", "get_payment_details", "get_refund_status", "get_rule_flags"]
    for tool_name in tool_names:
        try:
            result = execute_tool(tool_name, {"case_id": str(case_id)}, db)
            evidence_data[tool_name] = result
        except Exception as e:
            evidence_data[tool_name] = {"error": str(e)}

    from app.db.models import Evidence
    ev_rows = db.query(Evidence).filter(Evidence.case_id == case_id).all()
    categorized: dict[str, list] = {
        "transaction": [],
        "customer": [],
        "delivery": [],
        "merchant": [],
        "uncategorized": [],
    }
    for e in ev_rows:
        cat = map_to_canonical_category(e.evidence_type, e.category) or "uncategorized"
        categorized[cat].append({
            "id": str(e.id),
            "evidence_type": e.evidence_type,
            "filename": e.filename,
            "description": e.description,
            "verification_status": e.verification_status,
            "content": e.content,
            "event_timestamp": str(e.event_timestamp) if e.event_timestamp else None,
        })

    payload = {
        "case_details": evidence_data.get("get_case_details"),
        "rule_flags": evidence_data.get("get_rule_flags"),
        "evidence_by_category": categorized,
    }
    return json.dumps(payload, indent=2, default=str)


def _run_claude_agent(case_id: str, db: Session) -> AgentRecommendation:
    """Call Claude 3.5 Sonnet using Anthropic SDK."""
    import anthropic
    client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
    model = settings.anthropic_model or "claude-3-5-sonnet-20241022"

    context_json = _build_context(case_id, db)
    user_prompt = (
        f"Investigate this payment dispute. Here is all available dispute data and categorized evidence:\n\n"
        f"{context_json}\n\n"
        f"Analyze the evidence thoroughly and output your structured JSON recommendation."
    )

    response = client.messages.create(
        model=model,
        max_tokens=1024,
        temperature=0.0,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_prompt}],
    )

    content = response.content[0].text
    rec = _parse_final_json(content)
    rec.ai_status = "OK"
    return rec


def _run_openrouter_agent(case_id: str, db: Session) -> AgentRecommendation:
    """Call OpenRouter API."""
    context_json = _build_context(case_id, db)
    user_prompt = (
        f"Investigate this payment dispute. Here is all available dispute data and categorized evidence:\n\n"
        f"{context_json}\n\n"
        f"Analyze the evidence thoroughly and output your structured JSON recommendation."
    )

    headers = {
        "Authorization": f"Bearer {settings.openrouter_api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://payproof-frontend.vercel.app",
        "X-Title": "PayProof AI",
    }
    payload = {
        "model": settings.openrouter_model or "anthropic/claude-3.5-sonnet",
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
        "max_tokens": 1024,
    }

    with httpx.Client(timeout=45.0) as client:
        resp = client.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=payload)

    if resp.status_code != 200:
        raise RuntimeError(f"OpenRouter returned {resp.status_code}: {resp.text[:200]}")

    choices = resp.json().get("choices", [])
    if not choices:
        raise RuntimeError("OpenRouter returned empty choices")

    content = choices[0].get("message", {}).get("content", "")
    rec = _parse_final_json(content)
    rec.ai_status = "OK"
    return rec


def investigate(
    case_id: str,
    db: Session,
    evidence_types: list[str],
    contradictions_found: bool,
    completeness: int,
    duplicate_payment_detected: bool = False,
) -> AgentRecommendation:
    """
    Run dispute investigation agent.
    1. If ANTHROPIC_API_KEY is configured and mock_verifier is False, call Claude 3.5 Sonnet.
    2. Else if OPENROUTER_API_KEY is configured and mock_verifier is False, call OpenRouter.
    3. If mock_verifier is True, use deterministic mock agent.
    4. Otherwise, use deterministic safety fallback.
    """
    if settings.anthropic_api_key and not settings.mock_verifier:
        try:
            logger.info("Calling Claude 3.5 Sonnet for case %s", case_id)
            return _run_claude_agent(case_id, db)
        except Exception as e:
            logger.warning("Claude API failed for case %s: %s. Using safety fallback.", case_id, e)
            rec = _deterministic_fallback(
                evidence_types, contradictions_found, completeness, duplicate_payment_detected,
                error_reason=f"Claude API unavailable: {str(e)[:100]}"
            )
            rec.ai_status = "AI_ANALYSIS_UNAVAILABLE"
            return rec

    if settings.openrouter_api_key and not settings.mock_verifier:
        try:
            logger.info("Calling OpenRouter for case %s", case_id)
            return _run_openrouter_agent(case_id, db)
        except Exception as e:
            logger.warning("OpenRouter failed for case %s: %s. Using safety fallback.", case_id, e)
            rec = _deterministic_fallback(
                evidence_types, contradictions_found, completeness, duplicate_payment_detected,
                error_reason=f"OpenRouter unavailable: {str(e)[:100]}"
            )
            rec.ai_status = "FALLBACK"
            return rec

    if settings.mock_verifier:
        return _mock_investigate(case_id, db, evidence_types, contradictions_found, completeness, duplicate_payment_detected)

    rec = _deterministic_fallback(
        evidence_types, contradictions_found, completeness, duplicate_payment_detected,
        error_reason="No AI API key configured"
    )
    rec.ai_status = "FALLBACK"
    return rec
