import pathlib

p = pathlib.Path('src/components/CaseCard.tsx')
text = p.read_text(encoding='utf-8')

import re
text = re.sub(r"const rec = c\.ai_recommendation \? aiRecommendationLabel\(c\.ai_recommendation\) : '.*?'", "const rec = c.ai_recommendation ? aiRecommendationLabel(c.ai_recommendation) : '-'", text)

p.write_text(text, encoding='utf-8')
