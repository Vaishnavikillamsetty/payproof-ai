import pathlib
p = pathlib.Path('payproof-backend/app/orchestrator.py')
text = p.read_text(encoding='utf-8')

text = text.replace(
    '''def run_pipeline(case_id: UUID, db: Session | None = None) -> None:
    """
    Execute the full evidence-verification pipeline for a case.
    Updates the Case row in-place and writes a complete audit trail.
    """''',
    '''def run_pipeline(case_id: UUID, db: Session | None = None) -> None:
    """
    Execute the full evidence-verification pipeline for a case.
    Updates the Case row in-place and writes a complete audit trail.
    """
    print(f"DIAGNOSTIC - BACKGROUND INVESTIGATION ENTERED for case {case_id}")'''
)

# Also add a print right before the investigate() call
text = text.replace(
    'recommendation = investigate(',
    'print(f"DIAGNOSTIC - CALLING investigation_agent.investigate() for case {case_id}")\n        recommendation = investigate('
)

p.write_text(text, encoding='utf-8')
