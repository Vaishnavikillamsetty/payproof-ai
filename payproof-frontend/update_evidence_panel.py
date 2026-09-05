import pathlib

p = pathlib.Path('src/components/EvidencePanel.tsx')
text = p.read_text(encoding='utf-8')

# First update Props
text = text.replace(
    'export default function EvidencePanel({ evidenceList }: Props) {',
    "import { getAIRecommendation } from '../utils'\n\ninterface Props {\n  evidenceList: Evidence[]\n  audit?: any[]\n}\n\nexport default function EvidencePanel({ evidenceList, audit = [] }: Props) {"
)
text = text.replace("interface Props {\n  evidenceList: Evidence[]\n}\n\n", "")

# Then replace the AI ANALYSIS section
old_ai_section = """      {/* AI ANALYSIS */}
      <div className="card" style={{ overflow: 'hidden' }}>
        <div style={{ padding: '16px 20px', background: 'rgba(91, 107, 124, 0.1)', borderBottom: '1px solid rgba(91, 107, 124, 0.2)' }}>
          <h3 className="font-mono" style={{ margin: 0, fontSize: 13, color: 'var(--color-slate-light)', display: 'flex', alignItems: 'center', gap: 8 }}>
            <span>🤖</span> AI ANALYSIS
          </h3>
          <p className="font-body" style={{ margin: '4px 0 0 0', fontSize: 12, color: 'rgba(255,255,255,0.7)' }}>
            System-generated findings and risk assessments.
          </p>
        </div>
        <div style={{ padding: '0 20px' }}>
          {aiAnalysis.length === 0 ? (
            <p className="font-body text-slate" style={{ fontStyle: 'italic', fontSize: 13, margin: '20px 0' }}>No AI records generated for this case.</p>
          ) : (
            aiAnalysis.map(e => <EvidenceItem key={e.id} e={e} />)
          )}
        </div>
      </div>"""

new_ai_section = """      {/* SYSTEM/AI ANALYSIS */}
      {(() => {
        const aiRec = getAIRecommendation(audit)
        const isMock = audit.some(a => a.step === 'mock_investigation_mode')
        const usedFallback = audit.some(a => a.step === 'agent_fallback_used')
        const title = isMock || usedFallback ? "RULE ANALYSIS / SYSTEM ANALYSIS" : "AI ANALYSIS"
        const subtitle = isMock || usedFallback ? "Deterministic safety analysis used because live AI verification is unavailable." : "System-generated findings and risk assessments."
        const recStep = audit.find(a => a.step === 'agent_recommendation_created')

        return (
          <div className="card" style={{ overflow: 'hidden' }}>
            <div style={{ padding: '16px 20px', background: 'rgba(91, 107, 124, 0.1)', borderBottom: '1px solid rgba(91, 107, 124, 0.2)' }}>
              <h3 className="font-mono" style={{ margin: 0, fontSize: 13, color: 'var(--color-slate-light)', display: 'flex', alignItems: 'center', gap: 8 }}>
                <span>🤖</span> {title}
              </h3>
              <p className="font-body" style={{ margin: '4px 0 0 0', fontSize: 12, color: 'rgba(255,255,255,0.7)' }}>
                {subtitle}
              </p>
            </div>
            <div style={{ padding: '20px' }}>
              {!recStep ? (
                <p className="font-body text-slate" style={{ fontStyle: 'italic', fontSize: 13, margin: 0 }}>No analysis records generated yet.</p>
              ) : (
                <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
                  <div>
                    <span className="font-mono text-slate" style={{ fontSize: 10, textTransform: 'uppercase', letterSpacing: '0.06em', display: 'block', marginBottom: 4 }}>Summary</span>
                    <span className="font-body" style={{ fontSize: 14, color: 'var(--color-white)' }}>{String(recStep.detail?.summary || '-')}</span>
                  </div>
                  <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(180px, 1fr))', gap: 16 }}>
                    <div>
                      <span className="font-mono text-slate" style={{ fontSize: 10, textTransform: 'uppercase', letterSpacing: '0.06em', display: 'block', marginBottom: 4 }}>Recommended Action</span>
                      <span className="font-mono" style={{ fontSize: 13, color: 'var(--color-white)' }}>{String(recStep.detail?.recommended_action || '-').toUpperCase()}</span>
                    </div>
                    <div>
                      <span className="font-mono text-slate" style={{ fontSize: 10, textTransform: 'uppercase', letterSpacing: '0.06em', display: 'block', marginBottom: 4 }}>Confidence</span>
                      <span className="font-mono" style={{ fontSize: 13, color: 'var(--color-white)' }}>{recStep.detail?.confidence != null ? `${Math.round(Number(recStep.detail.confidence) * 100)}%` : '-'}</span>
                    </div>
                    <div>
                      <span className="font-mono text-slate" style={{ fontSize: 10, textTransform: 'uppercase', letterSpacing: '0.06em', display: 'block', marginBottom: 4 }}>Risk Level</span>
                      <span className="font-mono" style={{ fontSize: 13, color: 'var(--color-white)' }}>{String(recStep.detail?.risk_level || '-').toUpperCase()}</span>
                    </div>
                  </div>
                </div>
              )}
            </div>
          </div>
        )
      })()}"""

text = text.replace(old_ai_section, new_ai_section)
p.write_text(text, encoding='utf-8')
