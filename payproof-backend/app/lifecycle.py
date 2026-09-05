"""Canonical mapping between an AI recommendation and a case lifecycle."""

from typing import Optional


_FOLLOW_UP_LIFECYCLES = {
    "escalate": "escalated",
    "request_more_evidence": "evidence_requested",
}


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
