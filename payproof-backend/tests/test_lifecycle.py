from app.lifecycle import lifecycle_after_human_review, lifecycle_for_recommendation, lifecycle_after_resolution, lifecycle_after_close


def test_escalate_recommendation_is_always_escalated():
    assert lifecycle_for_recommendation("ESCALATE", "OPEN") == "ESCALATED"
    # When a reviewer approves, human decision is recorded
    assert lifecycle_after_human_review("ESCALATE", "approve") == "DECISION_RECORDED"


def test_request_more_evidence_recommendation_requests_evidence():
    assert lifecycle_for_recommendation("REQUEST_MORE_EVIDENCE", "OPEN") == "EVIDENCE_REQUESTED"
    assert lifecycle_after_human_review("REQUEST_MORE_EVIDENCE", "approve") == "DECISION_RECORDED"
    assert lifecycle_after_human_review("REQUEST_MORE_EVIDENCE", "request_more_evidence") == "EVIDENCE_REQUESTED"


def test_terminal_recommendations_wait_for_human_review():
    assert lifecycle_for_recommendation("CONTEST", "OPEN") == "OPEN"
    assert lifecycle_for_recommendation("APPROVE", "OPEN") == "OPEN"
    # APPROVE and CONTEST record decision (NEVER automatically resolved)
    assert lifecycle_after_human_review("CONTEST", "approve") == "DECISION_RECORDED"
    assert lifecycle_after_human_review("CONTEST", "contest") == "DECISION_RECORDED"
    assert lifecycle_after_resolution("DECISION_RECORDED") == "RESOLVED"
    assert lifecycle_after_close("RESOLVED") == "CLOSED"
