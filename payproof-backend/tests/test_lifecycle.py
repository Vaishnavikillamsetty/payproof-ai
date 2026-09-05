from app.lifecycle import lifecycle_after_human_review, lifecycle_for_recommendation


def test_escalate_recommendation_is_always_escalated():
    assert lifecycle_for_recommendation("ESCALATE", "resolved") == "escalated"
    assert lifecycle_after_human_review("ESCALATE", "approve") == "escalated"


def test_request_more_evidence_recommendation_requests_evidence():
    assert lifecycle_for_recommendation("REQUEST_MORE_EVIDENCE", "resolved") == "evidence_requested"


def test_terminal_recommendations_resolve_cases():
    assert lifecycle_for_recommendation("APPROVE", "human_review") == "resolved"
    assert lifecycle_for_recommendation("REJECT", "human_review") == "resolved"
