import time
import json
import urllib.request

start = time.time()
with urllib.request.urlopen('http://127.0.0.1:8000/cases/') as response:
    raw_data = response.read()
    status = response.status
end = time.time()

data = json.loads(raw_data)
print(f"Time: {end - start:.4f}s")
print(f"Status: {status}")
print(f"Cases returned: {len(data)}")
if data:
    first = data[0]
    print(f"First case evidence_types: {first.get('evidence_types')}")
    print(f"First case score: {first.get('completeness_score')}")
    print(f"First case transaction_id: {first.get('transaction_id')}")
