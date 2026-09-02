"""
DisputeInvestigationAgent — bounded tool-calling AI agent.

Architecture:
  - Uses Anthropic's native tool_use capability (no LangChain)
  - Bounded to MAX_AGENT_STEPS tool calls to prevent runaway loops
  - Falls back to deterministic logic if the LLM fails
  - Outputs a strictly validated AgentRecommendation (Pydantic)
  - Never stores chain-of-thought; only evidence-grounded findings
  - Never writes to the database or performs external actions
"""

import json
import logging

import anthropic
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
from app.agents.tools import TOOL_DEFINITIONS, execute_tool

logger = logging.getLogger(__name__)

MAX_AGENT_STEPS = 5


# --------------------------------------------------------------------------- #
# System prompt
# --------------------------------------------------------------------------- #

SYSTEM_PROMPT = """\
You are PayProof AI — a dispute investigation agent for Razorpay merchants.

GOAL: Investigate a payment dispute by gathering available evidence using the tools provided, checking verified facts, identifying missing evidence, detecting contradictions, and recommending the safest next action.

RULES:
1. Use the provided tools to gather information. Do NOT invent evidence.
2. Call get_case_details first to understand the dispute.
3. Then call search_case_evidence to see what evidence exists.
4. Call get_payment_details and get_refund_status if you need payment/refund data.
5. Call get_rule_flags to see deterministic rule results.
6. After gathering enough information, provide your final recommendation.

IMPORTANT CONSTRAINTS:
- You are read-only. You cannot modify data or submit disputes.
- Base your recommendation ONLY on the evidence returned by tools.
- If evidence contradicts the customer claim, note it clearly.
- If evidence is missing, recommend REQUEST_MORE_EVIDENCE.
- Always set human_approval_required to true.

When you have enough information, respond with a JSON object (no markdown fences) matching this exact schema:

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
) -> AgentRecommendation:
    """
    Pure rule-based recommendation when the AI is unavailable.
    """
    if contradictions_found:
        action = RecommendedAction.ESCALATE
        risk = RiskLevel.HIGH
        strength = EvidenceStrength.MEDIUM
        summary = "Contradicting evidence detected. Deterministic fallback recommends escalation."
        confidence = 0.4
    elif "refund" in evidence_types: # Example rule if refund check exists
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
        # For completeness < 50 (including 0), it's weak or empty, so we request more.
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
# Mock agent (when MOCK_VERIFIER=true)
# --------------------------------------------------------------------------- #

def _mock_investigate(
    case_id: str,
    db: Session,
    evidence_types: list[str],
    contradictions_found: bool,
    completeness: int,
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
        # Empty or weak case
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
# Real Anthropic tool-calling agent
# --------------------------------------------------------------------------- #

def _parse_final_json(text: str) -> AgentRecommendation:
    """Parse and validate the agent's final JSON output."""
    # Strip markdown fences if present
    clean = text.strip()
    if clean.startswith("```"):
        lines = clean.split("\n")
        lines = [l for l in lines if not l.strip().startswith("```")]
        clean = "\n".join(lines).strip()

    data = json.loads(clean)
    return AgentRecommendation(**data)


def _run_anthropic_agent(case_id: str, db: Session) -> AgentRecommendation:
    """
    Bounded Anthropic tool-calling loop.
    The model calls tools, we execute them and feed results back.
    After MAX_AGENT_STEPS tool calls OR when the model stops calling tools,
    we parse the final text output as AgentRecommendation JSON.
    """
    if not settings.anthropic_api_key:
        raise RuntimeError("ANTHROPIC_API_KEY is not configured")

    client = anthropic.Anthropic(api_key=settings.anthropic_api_key)

    messages = [
        {
            "role": "user",
            "content": f"Investigate dispute case {case_id}. Start by calling get_case_details, then gather evidence and rule flags, and provide your structured recommendation.",
        }
    ]

    # Convert our tool definitions to Anthropic's format
    anthropic_tools = [
        {
            "name": t["name"],
            "description": t["description"],
            "input_schema": t["input_schema"],
        }
        for t in TOOL_DEFINITIONS
    ]

    steps_used = 0

    from app.db.models import AuditLog
    
    def _agent_audit(step_name: str, detail: dict):
        entry = AuditLog(case_id=case_id, step=step_name, detail=detail)
        db.add(entry)
        db.commit()

    while steps_used < MAX_AGENT_STEPS:
        response = client.messages.create(
            model=settings.anthropic_model,
            max_tokens=2048,
            system=SYSTEM_PROMPT,
            messages=messages,
            tools=anthropic_tools,
        )

        # Check if there are tool_use blocks
        tool_use_blocks = [b for b in response.content if b.type == "tool_use"]

        if not tool_use_blocks:
            # Model is done — extract final text
            text_blocks = [b.text for b in response.content if hasattr(b, "text")]
            final_text = "\n".join(text_blocks)
            return _parse_final_json(final_text)

        # Process tool calls
        # First, add the assistant message with all content blocks
        messages.append({"role": "assistant", "content": response.content})

        # Then create tool results
        tool_results = []
        for block in tool_use_blocks:
            steps_used += 1
            logger.info("Agent step %d/%d: calling tool %s", steps_used, MAX_AGENT_STEPS, block.name)

            try:
                result = execute_tool(block.name, block.input, db)
                _agent_audit("agent_tool_called", {
                    "tool": block.name,
                    "case_id": case_id,
                    "status": "success"
                })
            except ValueError as e:
                result = {"error": str(e)}
                _agent_audit("agent_tool_called", {
                    "tool": block.name,
                    "case_id": case_id,
                    "status": "failure",
                    "error": str(e)
                })
            except Exception as e:
                logger.error("Tool %s failed: %s", block.name, e)
                result = {"error": f"Tool execution failed: {type(e).__name__}"}
                _agent_audit("agent_tool_called", {
                    "tool": block.name,
                    "case_id": case_id,
                    "status": "failure",
                    "error": type(e).__name__
                })

            tool_results.append({
                "type": "tool_result",
                "tool_use_id": block.id,
                "content": json.dumps(result, default=str),
            })

        messages.append({"role": "user", "content": tool_results})

    # If we exhausted MAX_AGENT_STEPS, force one final completion without tools
    messages.append({
        "role": "user",
        "content": "You have reached the maximum number of tool calls. Based on the information you have gathered so far, provide your final structured JSON recommendation now.",
    })

    response = client.messages.create(
        model=settings.anthropic_model,
        max_tokens=2048,
        system=SYSTEM_PROMPT,
        messages=messages,
    )

    text_blocks = [b.text for b in response.content if hasattr(b, "text")]
    final_text = "\n".join(text_blocks)
    return _parse_final_json(final_text)


# --------------------------------------------------------------------------- #
# Public API
# --------------------------------------------------------------------------- #

def investigate(
    case_id: str,
    db: Session,
    evidence_types: list[str],
    contradictions_found: bool,
    completeness: int,
) -> AgentRecommendation:
    """
    Run the dispute investigation agent.

    Uses MOCK_VERIFIER setting to choose between:
      - Mock agent (deterministic, no API cost)
      - Real Anthropic tool-calling agent

    On any failure, falls back to deterministic recommendation.
    """
    if settings.mock_verifier:
        logger.info("Using MOCK investigation agent for case %s", case_id)
        return _mock_investigate(case_id, db, evidence_types, contradictions_found, completeness)

    try:
        logger.info("Starting Anthropic investigation agent for case %s", case_id)
        return _run_anthropic_agent(case_id, db)
    except (json.JSONDecodeError, ValidationError) as e:
        logger.error("Agent output validation failed for case %s: %s", case_id, e)
        return _deterministic_fallback(evidence_types, contradictions_found, completeness)
    except anthropic.APIError as e:
        logger.error("Anthropic API error for case %s: %s", case_id, e)
        return _deterministic_fallback(evidence_types, contradictions_found, completeness)
    except Exception as e:
        logger.error("Agent failed for case %s: %s", case_id, e)
        return _deterministic_fallback(evidence_types, contradictions_found, completeness)
