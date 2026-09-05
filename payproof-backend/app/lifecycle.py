"""Canonical mapping between an AI recommendation and a case lifecycle."""

from typing import Optional


_RECOMMENDATION_LIFECYCLES = {
    "escalate": "escalated",
    "request_more_evidence": "evidence_requested",
    # The current investigation agent uses ACCEPT/CONTEST; support the
    # equivalent APPROVE/REJECT values as well for API compatibility.
    "approve": "resolved",
    "reject": "resolved",
    "accept": "resolved",
    "contest": "resolved",
}


def lifecycle_for_recommendation(recommendation: Optional[str], fallback: str) -> str:
    """Return the lifecycle implied by an AI recommendation."""
    normalized = (recommendation or "").strip().lower()
    return _RECOMMENDATION_LIFECYCLES.get(normalized, fallback)


def lifecycle_after_human_review(recommendation: Optional[str], action: str) -> str:
    """Apply a human workflow action without discarding the AI recommendation."""
    implied = lifecycle_for_recommendation(recommendation, "")
    if implied:
        return implied
    return {
        "approve": "resolved",
        "request_more_evidence": "evidence_requested",
        "escalate": "escalated",
    }[action]
