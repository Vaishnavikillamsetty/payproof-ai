import pathlib

p = pathlib.Path('src/pages/CaseDetail.tsx')
text = p.read_text(encoding='utf-8')

old_card = """  const recLabel = aiRecommendationLabel(recStr)

  let modeLabel = '🤖 AI AGENT INVESTIGATION'
  if (isMock) modeLabel = 'DEMO RULE-BASED INVESTIGATION'
  else if (usedFallback) modeLabel = '⚠ DETERMINISTIC FALLBACK'

  return (
    <div className="card" style={{ padding: '24px', marginBottom: 24, borderTop: `4px solid ${recColor}` }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: 16 }}>
        <div>
          <div className="font-mono text-slate" style={{ fontSize: 11, letterSpacing: '0.1em', marginBottom: 8 }}>
            {modeLabel}
          </div>
          <div className="font-mono" style={{ fontSize: 24, color: recColor, fontWeight: 700, letterSpacing: '0.02em' }}>
            {recLabel}
          </div>
        </div>
        <div style={{ textAlign: 'right' }}>
          <div className="font-mono text-slate" style={{ fontSize: 11, letterSpacing: '0.05em', marginBottom: 4 }}>CONFIDENCE</div>
          <div className="font-mono" style={{ fontSize: 20, color: 'var(--color-white)' }}>
            {aiRec?.confidence != null ? `${Math.round(aiRec.confidence * 100)}%` : (c.overall_confidence ? `${Math.round(c.overall_confidence * 100)}%` : '---')}
          </div>
        </div>
      </div>
      
      <div style={{ marginTop: 20, paddingTop: 16, borderTop: '1px solid var(--color-ink-border)' }}>
        <div className="font-mono text-slate" style={{ fontSize: 11, marginBottom: 8 }}>BASED ON:</div>
        <ul className="font-body" style={{ margin: 0, paddingLeft: 20, color: 'var(--color-slate-light)', fontSize: 13, lineHeight: 1.6 }}>
          <li><span style={{ color: 'var(--color-teal)' }}>✓</span> Verified payment evidence</li>
          <li><span style={{ color: 'var(--color-amber)' }}>✓</span> Merchant records</li>
          <li>🤖 AI consistency analysis</li>
        </ul>
        <p className="font-body text-slate" style={{ fontSize: 12, marginTop: 12, fontStyle: 'italic' }}>
          Recommendation only - final action requires human review.
        </p>
      </div>
    </div>
  )
}"""

new_card = """  // If the backend has a specific ai_recommendation, use it. Otherwise fall back to aiRec or status.
  const recStr = c.ai_recommendation || aiRec?.recommended_action || c.status
  const recLabel = aiRecommendationLabel(recStr)
  const recColor = (recStr === 'contest' || recStr === 'strong_case') ? 'var(--color-teal)' :
                   (recStr === 'request_more_evidence' || recStr === 'weak_case') ? 'var(--color-amber)' :
                   (recStr === 'escalate' || recStr === 'human_review') ? 'var(--color-red)' : 'var(--color-slate)'

  let modeLabel = '🤖 AI AGENT INVESTIGATION'
  if (isMock) modeLabel = 'DEMO RULE-BASED INVESTIGATION'
  else if (usedFallback) modeLabel = '⚠ DETERMINISTIC FALLBACK'
  
  const hasReview = !!c.final_action
  const finalActionColor = (c.final_action === 'contest' || c.final_action === 'strong_case') ? 'var(--color-teal)' :
                   (c.final_action === 'request_more_evidence' || c.final_action === 'weak_case') ? 'var(--color-amber)' :
                   (c.final_action === 'escalate' || c.final_action === 'human_review') ? 'var(--color-red)' : 'var(--color-slate)'

  return (
    <div className="card" style={{ padding: '24px', marginBottom: 24, borderTop: `4px solid ${recColor}` }}>
      {/* Top row: AI Recommendation & Confidence */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: 16 }}>
        <div>
          <div className="font-mono text-slate" style={{ fontSize: 11, letterSpacing: '0.1em', marginBottom: 8 }}>
            AI RECOMMENDATION ({modeLabel})
          </div>
          <div className="font-mono" style={{ fontSize: 24, color: recColor, fontWeight: 700, letterSpacing: '0.02em' }}>
            {recLabel}
          </div>
        </div>
        <div style={{ textAlign: 'right' }}>
          <div className="font-mono text-slate" style={{ fontSize: 11, letterSpacing: '0.05em', marginBottom: 4 }}>CONFIDENCE</div>
          <div className="font-mono" style={{ fontSize: 20, color: 'var(--color-white)' }}>
            {aiRec?.confidence != null ? `${Math.round(aiRec.confidence * 100)}%` : (c.overall_confidence ? `${Math.round(c.overall_confidence * 100)}%` : '---')}
          </div>
        </div>
      </div>
      
      {/* If human reviewed, show Human Review / Final Action / Lifecycle */}
      {hasReview ? (
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: 16, marginTop: 24, paddingTop: 16, borderTop: '1px solid var(--color-ink-border)' }}>
          <div>
            <div className="font-mono text-slate" style={{ fontSize: 11, letterSpacing: '0.05em', marginBottom: 4 }}>HUMAN REVIEW</div>
            <div className="font-mono text-white" style={{ fontSize: 14 }}>{c.final_action === recStr ? 'Approved' : 'Overridden'}</div>
          </div>
          <div>
            <div className="font-mono text-slate" style={{ fontSize: 11, letterSpacing: '0.05em', marginBottom: 4 }}>FINAL ACTION</div>
            <div className="font-mono" style={{ fontSize: 14, color: finalActionColor, fontWeight: 600 }}>{aiRecommendationLabel(c.final_action)}</div>
          </div>
          <div>
            <div className="font-mono text-slate" style={{ fontSize: 11, letterSpacing: '0.05em', marginBottom: 4 }}>LIFECYCLE</div>
            <div className="font-mono" style={{ fontSize: 14, color: 'var(--color-teal)', fontWeight: 600 }}>{c.status.toUpperCase()}</div>
          </div>
        </div>
      ) : (
        <div style={{ marginTop: 20, paddingTop: 16, borderTop: '1px solid var(--color-ink-border)' }}>
          <div className="font-mono text-slate" style={{ fontSize: 11, marginBottom: 8 }}>BASED ON:</div>
          <ul className="font-body" style={{ margin: 0, paddingLeft: 20, color: 'var(--color-slate-light)', fontSize: 13, lineHeight: 1.6 }}>
            <li><span style={{ color: 'var(--color-teal)' }}>✓</span> Verified payment evidence</li>
            <li><span style={{ color: 'var(--color-amber)' }}>✓</span> Merchant records</li>
            <li>🤖 AI consistency analysis</li>
          </ul>
          <p className="font-body text-slate" style={{ fontSize: 12, marginTop: 12, fontStyle: 'italic' }}>
            Recommendation only - final action requires human review.
          </p>
        </div>
      )}
    </div>
  )
}"""

# Need to replace the whole body of AiRecommendationCard. Let's just find the `const recStr = ...` and replace from there to the closing brace of the component.
import re
text = re.sub(r'  const recStr = aiRec\?\.recommended_action.*?(?=\n\s+function SectionHeader)', new_card + '\n', text, flags=re.DOTALL)
p.write_text(text, encoding='utf-8')
