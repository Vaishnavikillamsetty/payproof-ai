import sys
sys.path.insert(0, '.')
from app.agents.external_systems import _get_base_demo_id, fetch_external_evidence

test_ids = [
    "DEMO_SCN_01_GNHIIT",
    "DEMO_SCN_15_GKHVPQ",
    "DEMO_SCN_01",
    "DEMO_SCN_01_ABCD",
    "DEMO_TXN_STRONG_1",
    "RANDOM_TXN_123",
    "DEMO_SCN_09_XYZ123",
]
print("=== _get_base_demo_id results ===")
for tid in test_ids:
    result = _get_base_demo_id(tid)
    print(f"  {tid} -> {result}")
