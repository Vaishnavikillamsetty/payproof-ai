"""
Canonical lifecycle state machine and workflow transitions.

Lifecycles:
  - OPEN: Initial state for newly created disputes.
  - INVESTIGATING: Background pipeline is running.
  - EVIDENCE_REQUESTED: Critical evidence missing or reviewer requested more evidence.
  - ESCALATED: High risk or conflicting evidence detected.
  - DECISION_RECORDED: Reviewer recorded APPROVE or CONTEST. Final resolution pending.
  - RESOLVED: Explicit authorized resolution workflow completed.
  - CLOSED: Explicit case closure.

CRITICAL RULES:
  - APPROVE or CONTEST moves lifecycle to DECISION_RECORDED (NEVER automatically to RESOLVED).
  - REQUEST_MORE_EVIDENCE moves lifecycle to EVIDENCE_REQUESTED.
  - Only explicit resolution or close workflows can transition to RESOLVED or CLOSED.
"""

from typing import Optional

OPEN_LIFECYCLES = frozenset({
    "open", "new", "investigating", "pending_review",
    "evidence_requested", "request_more_evidence",
    "escalated", "escalate",
    "decision_recorded", "action_required", "under_review",
    "strong_case", "weak_case", "human_review", "contest", "accept"
})

TERMINAL_LIFECYCLES = frozenset({
    "resolved", "closed", "won", "lost"
})


def is_open_lifecycle(status: Optional[str]) -> bool:
    if not status:
        return False
    return status.strip().lower() in OPEN_LIFECYCLES


def is_terminal_lifecycle(status: Optional[str]) -> bool:
    if not status:
        return False
    return status.strip().lower() in TERMINAL_LIFECYCLES


def lifecycle_for_recommendation(recommendation: Optional[str], fallback: str = "OPEN") -> str:
    """
    Return the pre-review lifecycle implied by an AI recommendation.
    Advisory recommendation only.
    """
    normalized = (recommendation or "").strip().lower()
    if normalized == "escalate":
        return "ESCALATED"
    if normalized == "request_more_evidence":
        return "EVIDENCE_REQUESTED"
    return fallback


def lifecycle_after_human_review(recommendation: Optional[str], action: str) -> str:
    """
    Apply a human review action.
    APPROVE or CONTEST -> DECISION_RECORDED (NEVER RESOLVED automatically).
    REQUEST_MORE_EVIDENCE -> EVIDENCE_REQUESTED.
    """
    norm_action = (action or "").strip().lower()
    if norm_action in ("approve", "contest", "accept"):
        return "DECISION_RECORDED"
    if norm_action in ("request_more_evidence", "evidence_requested"):
        return "EVIDENCE_REQUESTED"
    if norm_action == "escalate":
        return "ESCALATED"
    raise ValueError(f"Unsupported human review action: {action}")


def lifecycle_after_resolution(status: Optional[str]) -> str:
    """
    Explicit authorized resolution workflow.
    """
    return "RESOLVED"


def lifecycle_after_close(status: Optional[str]) -> str:
    """
    Explicit authorized case closure.
    """
    return "CLOSED"
