import pathlib

p = pathlib.Path('src/components/CaseCard.tsx')
text = p.read_text(encoding='utf-8')

old_logic = """  const theme = statusTheme(c.status)
  const rec = aiRecommendationLabel(c.status)
  const recColor = REC_COLORS[rec] ?? 'var(--color-slate)'"""

new_logic = """  const theme = statusTheme(c.status)
  const rec = c.ai_recommendation ? aiRecommendationLabel(c.ai_recommendation) : '—'
  const recColor = c.ai_recommendation ? (REC_COLORS[rec] ?? 'var(--color-slate)') : 'var(--color-slate)'"""

text = text.replace(old_logic, new_logic)

p.write_text(text, encoding='utf-8')
