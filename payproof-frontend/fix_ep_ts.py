import pathlib

p = pathlib.Path('src/components/EvidencePanel.tsx')
text = p.read_text(encoding='utf-8')

# Remove the unused aiAnalysis variable
text = text.replace(
    "  const aiAnalysis = evidenceList.filter(e => ['ai_analysis', 'contradiction', 'risk'].includes(e.evidence_type))\n",
    ""
)

# Remove the unused aiRec local variable inside the IIFE (it shadows the import)
text = text.replace(
    "        const aiRec = getAIRecommendation(audit)\n",
    ""
)

p.write_text(text, encoding='utf-8')
