import pathlib
p = pathlib.Path('app/orchestrator.py')
text = p.read_text(encoding='utf-8')

old_update = """        # ------------------------------------------------------------------ #
        # Update case with final scores                                       #
        # ------------------------------------------------------------------ #
        case.status = status
        case.completeness_score = score
        case.overall_confidence = round(avg_confidence, 4)"""
new_update = """        # ------------------------------------------------------------------ #
        # Update case with final scores                                       #
        # ------------------------------------------------------------------ #
        case.status = status
        case.ai_recommendation = recommendation.recommended_action.value
        case.contradiction_detected = contradictions_found
        case.completeness_score = score
        case.overall_confidence = round(avg_confidence, 4)"""

if 'case.ai_recommendation =' not in text:
    text = text.replace(old_update, new_update)
    p.write_text(text, encoding='utf-8')
