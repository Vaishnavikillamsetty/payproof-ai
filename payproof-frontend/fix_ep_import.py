import pathlib

p = pathlib.Path('src/components/EvidencePanel.tsx')
text = p.read_text(encoding='utf-8')

# Remove the now-unused import at the top of the file
text = text.replace("import { getAIRecommendation } from '../utils'\n\n", "")

p.write_text(text, encoding='utf-8')
