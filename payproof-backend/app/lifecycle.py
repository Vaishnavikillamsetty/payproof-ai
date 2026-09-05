"""Canonical mapping between an AI recommendation and a case lifecycle."""

from typing import Optional


_FOLLOW_UP_LIFECYCLES = {
    "escalate": "escalated",
    "request_more_evidence": "evidence_requested",
}

# Shared workflow definition for callers that need to distinguish active work
# from terminal cases. Keep terminal webhook outcomes out of dashboard totals.
OPEN_LIFECYCLES = frozenset({
    "new", "investigating", "pending_review", "human_review",
    "escalate", "escalated", "request_more_evidence", "evidence_requested",
    "action_required", "under_review", "strong_case", "weak_case",
    "accept", "contest",
})


def is_open_lifecycle(status: Optional[str]) -> bool:
    return (status or "").strip().lower() in OPEN_LIFECYCLES


def lifecycle_for_recommendation(recommendation: Optional[str], fallback: str = "pending_review") -> str:
    """Return the pre-review lifecycle implied by an AI recommendation.

    A recommendation is not a final decision. Only recommendations that
    inherently require a follow-up state leave the generic pending-review
    lifecycle before a reviewer records their final action.
    """
    normalized = (recommendation or "").strip().lower()
    return _FOLLOW_UP_LIFECYCLES.get(normalized, fallback)


def lifecycle_after_human_review(recommendation: Optional[str], action: str) -> str:
    """Apply a human workflow action without discarding the AI recommendation."""
    if (recommendation or "").strip().lower() == "escalate":
        return "escalated"
    return {
        "approve": "resolved",
        "request_more_evidence": "evidence_requested",
        "escalate": "escalated",
    }[action]
