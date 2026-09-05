from app.lifecycle import lifecycle_after_human_review, lifecycle_for_recommendation


def test_escalate_recommendation_is_always_escalated():
    assert lifecycle_for_recommendation("ESCALATE", "resolved") == "escalated"
    assert lifecycle_after_human_review("ESCALATE", "approve") == "escalated"


def test_request_more_evidence_recommendation_requests_evidence():
    assert lifecycle_for_recommendation("REQUEST_MORE_EVIDENCE", "resolved") == "evidence_requested"
    assert lifecycle_after_human_review("REQUEST_MORE_EVIDENCE", "approve") == "resolved"


def test_terminal_recommendations_wait_for_human_review():
    assert lifecycle_for_recommendation("CONTEST") == "pending_review"
    assert lifecycle_for_recommendation("APPROVE") == "pending_review"
    assert lifecycle_after_human_review("CONTEST", "approve") == "resolved"
