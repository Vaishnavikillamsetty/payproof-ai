import pathlib

p = pathlib.Path('src/types.ts')
text = p.read_text(encoding='utf-8')

old_case = """  amount: number
  status: CaseStatus
  completeness_score: number | null"""

new_case = """  amount: number
  currency: string
  status: CaseStatus
  ai_recommendation: string | null
  final_action: string | null
  contradiction_detected: boolean
  completeness_score: number | null"""

text = text.replace(old_case, new_case)
p.write_text(text, encoding='utf-8')
