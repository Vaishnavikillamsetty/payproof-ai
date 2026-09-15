"""
DisputeInvestigationAgent — bounded AI agent.

Architecture:
  - Uses OpenRouter (openrouter/free) via OpenAI-compatible chat completions
  - Evidence is gathered directly in Python via existing tool functions
  - LLM receives a full-context prompt and responds with a JSON recommendation
  - Falls back to deterministic logic if the LLM fails or returns malformed JSON
  - Outputs a strictly validated AgentRecommendation (Pydantic)
  - Never stores chain-of-thought; only evidence-grounded findings
  - Never writes to the database or performs external actions
"""

import json
import logging
import os

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

logger = logging.getLogger(__name__)

MAX_AGENT_STEPS = 5

OPENROUTER_API_BASE = "https://openrouter.ai/api/v1"
OPENROUTER_REFERER = "https://payproof-frontend.vercel.app"
OPENROUTER_TITLE = "PayProof AI"


# --------------------------------------------------------------------------- #
# System prompt
# --------------------------------------------------------------------------- #

SYSTEM_PROMPT = """\
You are PayProof AI — a dispute investigation agent for Razorpay merchants.

GOAL: Investigate a payment dispute by reviewing the provided evidence data, identifying contradictions, and recommending the safest next action.

RULES:
1. Base your recommendation ONLY on the evidence data provided in this message.
2. Do NOT invent evidence.
3. If evidence contradicts the customer claim, note it clearly.
4. If evidence is missing, recommend REQUEST_MORE_EVIDENCE.
5. Always set human_approval_required to true.

When you have enough information, respond with ONLY a JSON object matching this exact schema (no markdown fences, no commentary):

{
  "recommended_action": "CONTEST" | "ACCEPT" | "ESCALATE" | "REQUEST_MORE_EVIDENCE",
  "confidence": <float 0.0-1.0>,
  "risk_level": "LOW" | "MEDIUM" | "HIGH",
  "evidence_strength": "LOW" | "MEDIUM" | "HIGH",
  "summary": "<one paragraph summary of findings>",
  "key_findings": [
    {"finding": "<what was found>", "source": "<data source>", "importance": "high"|"medium"|"low"}
  ],
  "missing_evidence": ["<evidence type not found>"],
  "contradictions": ["<description of contradiction>"],
  "human_approval_required": true,
  "source_status": "COMPLETE" | "PARTIAL" | "LIMITED"
}
"""


# --------------------------------------------------------------------------- #
# Deterministic fallback
# --------------------------------------------------------------------------- #

def _deterministic_fallback(
    evidence_types: list[str],
    contradictions_found: bool,
    completeness: int,
    duplicate_payment_detected: bool = False,
) -> AgentRecommendation:
    """
    Pure rule-based recommendation when the AI is unavailable.
    """
    if duplicate_payment_detected:
        action = RecommendedAction.ACCEPT
        risk = RiskLevel.LOW
        strength = EvidenceStrength.HIGH
        summary = "Multiple successful payments detected for duplicate charge claim. Recommending ACCEPT/refund."
        confidence = 0.9
    elif contradictions_found:
        action = RecommendedAction.ESCALATE
        risk = RiskLevel.HIGH
        strength = EvidenceStrength.MEDIUM
        summary = "Contradicting evidence detected. Deterministic fallback recommends escalation."
        confidence = 0.4
    elif "refund" in evidence_types:
        action = RecommendedAction.ACCEPT
        risk = RiskLevel.LOW
        strength = EvidenceStrength.HIGH
        summary = "Refund already processed. Deterministic fallback recommends accepting."
        confidence = 0.8
    elif completeness >= 50:
        action = RecommendedAction.CONTEST
        risk = RiskLevel.LOW
        strength = EvidenceStrength.HIGH
        summary = "Sufficient verified evidence available. Deterministic fallback recommends contesting."
        confidence = 0.7
    else:
        action = RecommendedAction.REQUEST_MORE_EVIDENCE
        risk = RiskLevel.MEDIUM if completeness >= 30 else RiskLevel.HIGH
        strength = EvidenceStrength.LOW
        summary = "Insufficient or missing evidence. Deterministic fallback recommends gathering more before contesting."
        confidence = 0.5 if completeness >= 30 else 0.2

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
            finding=f"Evidence categories present: {', '.join(evidence_types) or 'none'}",
            source="deterministic_fallback",
            importance="high",
            verified=False
        )],
        missing_evidence=missing,
        contradictions=["Contradiction detected by rule engine"] if contradictions_found else [],
        human_approval_required=True,
        source_status=SourceStatus.COMPLETE if completeness >= 50 else SourceStatus.PARTIAL if completeness >= 30 else SourceStatus.LIMITED,
        ai_status="FALLBACK",
    )


# --------------------------------------------------------------------------- #
# Mock agent (when no OpenRouter key is configured)
# --------------------------------------------------------------------------- #

def _mock_investigate(
    case_id: str,
    db: Session,
    evidence_types: list[str],
    contradictions_found: bool,
    completeness: int,
    duplicate_payment_detected: bool = False,
) -> AgentRecommendation:
    """
    Deterministic mock agent for demos — no LLM call.
    Produces realistic structured output based on evidence and rules.
    """
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
            confidence=0.55 if completeness >= 30 else 0.2,
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


# --------------------------------------------------------------------------- #
# JSON parsing helper
# --------------------------------------------------------------------------- #

def _parse_final_json(text: str) -> AgentRecommendation:
    """Parse and validate the agent's final JSON output. Strips markdown fences if present."""
    clean = text.strip()
    # Strip ```json ... ``` or ``` ... ``` fences
    if clean.startswith("```"):
        lines = clean.split("\n")
        lines = [l for l in lines if not l.strip().startswith("```")]
        clean = "\n".join(lines).strip()

    # Find the JSON object boundaries in case the model added commentary
    start = clean.find("{")
    end = clean.rfind("}")
    if start != -1 and end != -1 and end > start:
        clean = clean[start:end + 1]

    data = json.loads(clean)
    return AgentRecommendation(**data)


# --------------------------------------------------------------------------- #
# OpenRouter AI agent
# --------------------------------------------------------------------------- #

def _run_openrouter_agent(case_id: str, db: Session) -> AgentRecommendation:
    """
    Gather evidence via Python tool calls, then send a single OpenRouter
    chat completion request with the full evidence context and parse the
    JSON recommendation from the response.
    """
    print("DIAGNOSTIC - OpenRouter request started for case " + str(case_id))

    # --- Gather evidence directly via tool functions ---
    evidence_data = {}
    tool_names = ["get_case_details", "search_case_evidence", "get_payment_details", "get_refund_status", "get_rule_flags"]

    for tool_name in tool_names:
        try:
            result = execute_tool(tool_name, {"case_id": str(case_id)}, db)
            evidence_data[tool_name] = result
        except Exception as e:
            evidence_data[tool_name] = {"error": str(e)}

    # --- Build context summary for the LLM ---
    context = json.dumps(evidence_data, indent=2, default=str)
    user_message = (
        f"Investigate this payment dispute. Here is all available evidence data:\n\n"
        f"{context}\n\n"
        f"Based on this evidence, provide your structured JSON recommendation."
    )

    model = settings.openrouter_model or "openrouter/free"

    headers = {
        "Authorization": f"Bearer {settings.openrouter_api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": OPENROUTER_REFERER,
        "X-Title": OPENROUTER_TITLE,
    }

    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_message},
        ],
        "max_tokens": 1024,
    }

    with httpx.Client(timeout=60.0) as client:
        response = client.post(
            f"{OPENROUTER_API_BASE}/chat/completions",
            headers=headers,
            json=payload,
        )

    if response.status_code != 200:
        raise RuntimeError(
            f"OpenRouter returned HTTP {response.status_code}: {response.text[:300]}"
        )

    response_data = response.json()
    choices = response_data.get("choices", [])
    if not choices:
        raise RuntimeError("OpenRouter response contained no choices")

    content = choices[0].get("message", {}).get("content", "")
    if not content or not content.strip():
        raise RuntimeError("OpenRouter returned empty content")

    print("DIAGNOSTIC - OpenRouter request succeeded for case " + str(case_id))
    return _parse_final_json(content)


# --------------------------------------------------------------------------- #
# Public API
# --------------------------------------------------------------------------- #

def investigate(
    case_id: str,
    db: Session,
    evidence_types: list[str],
    contradictions_found: bool,
    completeness: int,
    duplicate_payment_detected: bool = False,
) -> AgentRecommendation:
    """
    Run the dispute investigation agent.

    If OPENROUTER_API_KEY is configured, uses the live OpenRouter AI agent.
    Otherwise falls back to the deterministic mock agent.
    On any failure, falls back to deterministic recommendation.
    """
    # --- DIAGNOSTICS ---
    print("DIAGNOSTIC - OPENROUTER_API_KEY configured: " + str(bool(settings.openrouter_api_key)))
    print("DIAGNOSTIC - OPENROUTER_MODEL: " + str(settings.openrouter_model))
    print("DIAGNOSTIC - settings.mock_verifier: " + str(settings.mock_verifier))
    # -------------------

    if not settings.openrouter_api_key:
        logger.info("No OPENROUTER_API_KEY — using mock investigation agent for case %s", case_id)
        from app.db.models import AuditLog
        db.add(AuditLog(
            case_id=case_id,
            step="mock_investigation_mode",
            detail={"info": "Deterministic safety analysis used because live AI verification is unavailable."}
        ))
        db.commit()
        return _mock_investigate(case_id, db, evidence_types, contradictions_found, completeness, duplicate_payment_detected)

    try:
        return _run_openrouter_agent(case_id, db)
    except (json.JSONDecodeError, ValidationError) as e:
        print("DIAGNOSTIC - OpenRouter request failed (JSON/Validation): " + str(e))
        logger.error("OpenRouter agent output validation failed for case %s: %s", case_id, e)
        return _deterministic_fallback(evidence_types, contradictions_found, completeness, duplicate_payment_detected)
    except Exception as e:
        print("DIAGNOSTIC - OpenRouter request failed: " + str(e))
        logger.error("OpenRouter agent failed for case %s: %s", case_id, e)
        return _deterministic_fallback(evidence_types, contradictions_found, completeness, duplicate_payment_detected)
