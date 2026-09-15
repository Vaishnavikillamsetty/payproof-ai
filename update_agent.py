import pathlib

p = pathlib.Path('payproof-backend/app/agents/investigation_agent.py')
text = p.read_text(encoding='utf-8')

text = text.replace(
    'evidence_types: list[str],\n    contradictions_found: bool,\n    completeness: int,\n) -> AgentRecommendation:',
    'evidence_types: list[str],\n    contradictions_found: bool,\n    completeness: int,\n    duplicate_payment_detected: bool = False,\n) -> AgentRecommendation:'
)

# In _mock_investigate
text = text.replace(
    'return _deterministic_fallback(evidence_types, contradictions_found, completeness)',
    'return _deterministic_fallback(evidence_types, contradictions_found, completeness, duplicate_payment_detected)'
)

# In investigate() 
text = text.replace(
    'evidence_types: list[str],\n    contradictions_found: bool,\n    completeness: int,\n) -> AgentRecommendation:',
    'evidence_types: list[str],\n    contradictions_found: bool,\n    completeness: int,\n    duplicate_payment_detected: bool = False,\n) -> AgentRecommendation:'
)
text = text.replace(
    'return _mock_investigate(case_id, db, evidence_types, contradictions_found, completeness)',
    'return _mock_investigate(case_id, db, evidence_types, contradictions_found, completeness, duplicate_payment_detected)'
)
text = text.replace(
    'return _deterministic_fallback(evidence_types, contradictions_found, completeness)',
    'return _deterministic_fallback(evidence_types, contradictions_found, completeness, duplicate_payment_detected)'
)

# In _deterministic_fallback logic
fallback_logic_old = """    if contradictions_found:
        action = RecommendedAction.ESCALATE"""
fallback_logic_new = """    if duplicate_payment_detected:
        action = RecommendedAction.ACCEPT
        risk = RiskLevel.LOW
        strength = EvidenceStrength.HIGH
        summary = "Multiple successful payments detected for duplicate charge claim. Recommending ACCEPT/refund."
        confidence = 0.9
    elif contradictions_found:
        action = RecommendedAction.ESCALATE"""
text = text.replace(fallback_logic_old, fallback_logic_new)

p.write_text(text, encoding='utf-8')
