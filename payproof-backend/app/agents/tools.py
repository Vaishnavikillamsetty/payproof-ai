"""
Agent Tools — controlled, read-only functions the DisputeInvestigationAgent can call.

Each tool:
  - reads from the database or the RazorpayProvider
  - returns a plain dict (JSON-serializable)
  - never writes to the database
  - never performs external actions
"""

import logging
from uuid import UUID
from sqlalchemy.orm import Session

from app.db.models import Case, Evidence, Claim, RuleFlag
from app.services.razorpay.factory import get_razorpay_provider

logger = logging.getLogger(__name__)


# --------------------------------------------------------------------------- #
# Tool Registry — the agent can ONLY call tools in this dict
# --------------------------------------------------------------------------- #

TOOL_DEFINITIONS = [
    {
        "name": "get_case_details",
        "description": "Get the dispute case details including dispute reason, amount, merchant, and current status.",
        "input_schema": {
            "type": "object",
            "properties": {
                "case_id": {"type": "string", "description": "UUID of the case"}
            },
            "required": ["case_id"]
        }
    },
    {
        "name": "get_payment_details",
        "description": "Fetch payment details from the payment provider (Razorpay or demo). Returns amount, status, currency.",
        "input_schema": {
            "type": "object",
            "properties": {
                "payment_id": {"type": "string", "description": "Transaction/payment ID"}
            },
            "required": ["payment_id"]
        }
    },
    {
        "name": "get_refund_status",
        "description": "Check if any refunds exist for a payment. Returns list of refund records.",
        "input_schema": {
            "type": "object",
            "properties": {
                "payment_id": {"type": "string", "description": "Transaction/payment ID"}
            },
            "required": ["payment_id"]
        }
    },
    {
        "name": "search_case_evidence",
        "description": "Retrieve all evidence records collected for this case from the database. Returns evidence type, content, and timestamps.",
        "input_schema": {
            "type": "object",
            "properties": {
                "case_id": {"type": "string", "description": "UUID of the case"}
            },
            "required": ["case_id"]
        }
    },
    {
        "name": "get_rule_flags",
        "description": "Get deterministic rule engine results for a case. Shows which rules triggered (e.g., amount_mismatch, delivery contradiction).",
        "input_schema": {
            "type": "object",
            "properties": {
                "case_id": {"type": "string", "description": "UUID of the case"}
            },
            "required": ["case_id"]
        }
    },
]


# --------------------------------------------------------------------------- #
# Tool Implementations
# --------------------------------------------------------------------------- #

def execute_tool(tool_name: str, tool_input: dict, db: Session) -> dict:
    """
    Dispatch a tool call.  Returns a plain dict.
    Raises ValueError for unknown tools.
    """
    if tool_name == "get_case_details":
        return _get_case_details(tool_input["case_id"], db)
    elif tool_name == "get_payment_details":
        return _get_payment_details(tool_input["payment_id"])
    elif tool_name == "get_refund_status":
        return _get_refund_status(tool_input["payment_id"])
    elif tool_name == "search_case_evidence":
        return _search_case_evidence(tool_input["case_id"], db)
    elif tool_name == "get_rule_flags":
        return _get_rule_flags(tool_input["case_id"], db)
    else:
        raise ValueError(f"Unknown tool: {tool_name}")


def _get_case_details(case_id: str, db: Session) -> dict:
    case = db.query(Case).filter(Case.id == UUID(case_id)).first()
    if not case:
        return {"error": "Case not found"}
    return {
        "case_id": str(case.id),
        "transaction_id": case.transaction_id,
        "dispute_reason": case.dispute_reason,
        "customer_claim": case.customer_claim,
        "merchant_id": case.merchant_id,
        "amount": float(case.amount),
        "status": case.status,
        "created_at": str(case.created_at),
    }


def _get_payment_details(payment_id: str) -> dict:
    try:
        provider = get_razorpay_provider()
        result = provider.get_payment_details(payment_id)
        if result is None:
            return {"payment_found": False, "payment_id": payment_id}
        return {
            "payment_found": True,
            "payment_id": result.payment_id,
            "amount_minor": result.amount_minor,
            "currency": result.currency,
            "status": result.status,
            "source": result.source,
        }
    except Exception as e:
        logger.error("Tool get_payment_details failed: %s", e)
        return {"payment_found": False, "error": str(e)}


def _get_refund_status(payment_id: str) -> dict:
    try:
        provider = get_razorpay_provider()
        refunds = provider.get_refund_details(payment_id)
        return {
            "payment_id": payment_id,
            "refund_count": len(refunds),
            "refunds": [
                {
                    "refund_id": r.refund_id,
                    "amount_minor": r.amount_minor,
                    "currency": r.currency,
                    "status": r.status,
                    "source": r.source,
                }
                for r in refunds
            ]
        }
    except Exception as e:
        logger.error("Tool get_refund_status failed: %s", e)
        return {"payment_id": payment_id, "refund_count": 0, "refunds": [], "error": str(e)}


def _search_case_evidence(case_id: str, db: Session) -> dict:
    evidence_rows = (
        db.query(Evidence)
        .filter(Evidence.case_id == UUID(case_id))
        .order_by(Evidence.event_timestamp.nullslast())
        .all()
    )
    return {
        "case_id": case_id,
        "evidence_count": len(evidence_rows),
        "evidence": [
            {
                "evidence_type": e.evidence_type,
                "source_id": e.source_id,
                "content": e.content,
                "event_timestamp": str(e.event_timestamp) if e.event_timestamp else None,
            }
            for e in evidence_rows
        ]
    }


def _get_rule_flags(case_id: str, db: Session) -> dict:
    flags = (
        db.query(RuleFlag)
        .filter(RuleFlag.case_id == UUID(case_id))
        .all()
    )
    return {
        "case_id": case_id,
        "flag_count": len(flags),
        "flags": [
            {
                "rule_name": f.rule_name,
                "triggered": f.triggered,
                "detail": f.detail,
            }
            for f in flags
        ]
    }
