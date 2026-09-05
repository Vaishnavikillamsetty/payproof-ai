import pathlib
import re

# 1. Update CaseCard.tsx
p = pathlib.Path('src/components/CaseCard.tsx')
text = p.read_text(encoding='utf-8')
text = text.replace('{formatAmount(c.amount)}', '{formatAmount(c.amount, c.currency)}')
p.write_text(text, encoding='utf-8')

# 2. Update CaseDetail.tsx
p = pathlib.Path('src/pages/CaseDetail.tsx')
text = p.read_text(encoding='utf-8')

# Remove duplicate local formatAmount
old_format = """function formatAmount(n: number) {
  return new Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR' }).format(n)
}"""
text = text.replace(old_format, "")

# Import formatAmount from utils instead
text = text.replace(
    "import { statusTheme, getAIRecommendation, aiRecommendationLabel, isWebhookOrigin, isDemoCase } from '../utils'",
    "import { statusTheme, getAIRecommendation, aiRecommendationLabel, isWebhookOrigin, isDemoCase, formatAmount } from '../utils'"
)

# Update its usage
text = text.replace('{formatAmount(c.amount)}', '{formatAmount(c.amount, c.currency)}')

# 3. Update the Case Details header for the requested UI:
# AI RECOMMENDATION | HUMAN REVIEW | FINAL ACTION | LIFECYCLE
# I need to find the decision section and replace it.
# Let's inspect the decision section first.
p.write_text(text, encoding='utf-8')
