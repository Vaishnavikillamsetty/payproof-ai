import pathlib

p = pathlib.Path('app/agents/investigation_agent.py')
text = p.read_text(encoding='utf-8')

old_check = """    if not settings.anthropic_api_key or settings.mock_verifier:
        logger.info("Using MOCK investigation agent for case %s", case_id)
        # Record explicit mock mode event
        from app.db.models import AuditLog
        db.add(AuditLog(
            case_id=case_id,
            step="mock_investigation_mode",
            detail={"info": "Deterministic safety analysis used because live AI verification is unavailable."}
        ))
        db.commit()
        return _mock_investigate(case_id, db, evidence_types, contradictions_found, completeness)"""

new_check = """    if not settings.anthropic_api_key:
        logger.info("Using MOCK investigation agent for case %s", case_id)
        # Record explicit mock mode event
        from app.db.models import AuditLog
        db.add(AuditLog(
            case_id=case_id,
            step="mock_investigation_mode",
            detail={"info": "Deterministic safety analysis used because live AI verification is unavailable."}
        ))
        db.commit()
        return _mock_investigate(case_id, db, evidence_types, contradictions_found, completeness)"""
        
text = text.replace(old_check, new_check)
p.write_text(text, encoding='utf-8')
