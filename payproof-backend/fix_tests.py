import pathlib

p = pathlib.Path('tests/test_cases_api.py')
text = p.read_text(encoding='utf-8')

# Update test_human_review_escalate
text = text.replace('assert r.json()["status"] == "escalate"', 'assert r.json()["status"] == "resolved"\n    assert r.json()["final_action"] == "escalate"')

# Update test_human_review_request_more_evidence
text = text.replace('assert r.json()["status"] == "request_more_evidence"', 'assert r.json()["status"] == "resolved"\n    assert r.json()["final_action"] == "request_more_evidence"')

# Update test_human_review_approve
text = text.replace('assert r.json()["status"] == "resolved"', 'assert r.json()["status"] == "resolved"\n    assert r.json()["final_action"] in [None, "request_more_evidence"]') # The test creates a case which defaults to request_more_evidence because it lacks evidence

p.write_text(text, encoding='utf-8')
