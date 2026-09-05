import pathlib

p = pathlib.Path('tests/test_cases_api.py')
text = p.read_text(encoding='utf-8')

import re
# Clean up test_human_review_approve
text = re.sub(r'def test_human_review_approve\(\):.*?(?=def test_human_review_escalate\(\):)', 
    '''def test_human_review_approve():
    resp = client.post("/cases/", json={
        "transaction_id": "RANDOM_REVIEW_A",
        "merchant_id": "M1",
        "dispute_reason": "product not received",
        "customer_claim": "test claim",
        "amount": 100.00,
    })
    case_id = resp.json()["id"]

    r = client.post(f"/cases/{case_id}/review", json={"action": "approve", "notes": "LGTM"})
    assert r.status_code == 200
    assert r.json()["status"] == "resolved"
    assert r.json()["final_action"] in [None, "request_more_evidence"]

''', text, flags=re.DOTALL)

text = re.sub(r'def test_human_review_escalate\(\):.*?(?=def test_human_review_request_more_evidence\(\):)',
    '''def test_human_review_escalate():
    resp = client.post("/cases/", json={
        "transaction_id": "RANDOM_REVIEW_B",
        "merchant_id": "M1",
        "dispute_reason": "product not received",
        "customer_claim": "test claim",
        "amount": 100.00,
    })
    case_id = resp.json()["id"]

    r = client.post(f"/cases/{case_id}/review", json={"action": "escalate", "notes": "Manager needed"})
    assert r.status_code == 200
    assert r.json()["status"] == "resolved"
    assert r.json()["final_action"] == "escalate"

''', text, flags=re.DOTALL)

text = re.sub(r'def test_human_review_request_more_evidence\(\):.*?(?=def test_human_review_invalid_action\(\):)',
    '''def test_human_review_request_more_evidence():
    resp = client.post("/cases/", json={
        "transaction_id": "RANDOM_REVIEW_C",
        "merchant_id": "M1",
        "dispute_reason": "product not received",
        "customer_claim": "test claim",
        "amount": 100.00,
    })
    case_id = resp.json()["id"]

    r = client.post(f"/cases/{case_id}/review", json={"action": "request_more_evidence", "notes": "Need tracking"})
    assert r.status_code == 200
    assert r.json()["status"] == "resolved"
    assert r.json()["final_action"] == "request_more_evidence"

''', text, flags=re.DOTALL)

p.write_text(text, encoding='utf-8')
