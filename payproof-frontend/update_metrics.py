import pathlib

p = pathlib.Path('src/pages/Metrics.tsx')
text = p.read_text(encoding='utf-8')

old_contradictions = """  // Contradictions: resolved into human review with contradictory signals
  // We use cases in human_review / escalate that have a low completeness score
  // as a proxy for contradiction-driven escalation.
  const contradictions = processed.filter(
    c => (c.status === 'human_review' || c.status === 'escalate') &&
         c.completeness_score !== null && c.completeness_score < 50
  )"""

new_contradictions = """  // Contradictions: derived from the actual backend contradiction_detected flag
  const contradictions = processed.filter(c => c.contradiction_detected)"""

old_text = """            <em> Contradictions</em> are escalated cases with completeness score below 50%."""
new_text = """            <em> Contradictions</em> are cases where contradicting evidence was detected by the rules engine."""

text = text.replace(old_contradictions, new_contradictions)
text = text.replace(old_text, new_text)
p.write_text(text, encoding='utf-8')
