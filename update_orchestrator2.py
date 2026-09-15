import pathlib
import re

p = pathlib.Path('payproof-backend/app/orchestrator.py')
text = p.read_text(encoding='utf-8')

# Change contradictions_found logic to ignore duplicate_payment_detected
text = text.replace(
    "contradictions_found = any(trig for _, trig, _ in rule_results)",
    "contradictions_found = any(trig for name, trig, _ in rule_results if name != 'duplicate_payment_detected')\n        duplicate_payment_detected = any(trig for name, trig, _ in rule_results if name == 'duplicate_payment_detected')"
)

# Update _audit for agent_investigation_started
text = text.replace(
    '"contradictions_found": contradictions_found,',
    '"contradictions_found": contradictions_found,\n            "duplicate_payment_detected": duplicate_payment_detected,'
)

# Pass duplicate_payment_detected to investigate()
text = text.replace(
    'contradictions_found=contradictions_found,\n            completeness=score,',
    'contradictions_found=contradictions_found,\n            completeness=score,\n            duplicate_payment_detected=duplicate_payment_detected,'
)

p.write_text(text, encoding='utf-8')
