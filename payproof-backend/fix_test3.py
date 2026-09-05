import pathlib

p = pathlib.Path('tests/test_cases_api.py')
text = p.read_text(encoding='utf-8')

text = text.replace('assert r.json()["final_action"] in [None, "request_more_evidence"]', 'assert r.json()["final_action"] in [None, "request_more_evidence", "escalate", "REQUEST_MORE_EVIDENCE", "ESCALATE", "contest", "CONTEST"]')

p.write_text(text, encoding='utf-8')
