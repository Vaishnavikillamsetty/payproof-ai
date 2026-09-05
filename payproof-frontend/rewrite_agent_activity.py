import pathlib

content = """\
import type { AuditEntry } from '../types'
import { getAgentToolCalls } from '../utils'
import { useState } from 'react'

interface Props {
  audit: AuditEntry[]
}

const TOOL_LABEL: Record<string, string> = {
  get_case_details: 'Fetch Case Details',
  get_payment_details: 'Query Payment API',
  get_refund_status: 'Query Refund API',
  search_case_evidence: 'Search Evidence Records',
  get_rule_flags: 'Evaluate Deterministic Rules',
  get_claims: 'Verify Customer Claims',
}

export default function AgentActivity({ audit }: Props) {
  const [expanded, setExpanded] = useState(true)
  const toolCalls = getAgentToolCalls(audit)
  const recStep = audit.find(a => a.step === 'agent_recommendation_created')
  const isMock = audit.some(a => a.step === 'mock_investigation_mode')
  const usedFallback = audit.some(a => a.step === 'agent_fallback_used')
  
  if (!recStep && toolCalls.length === 0 && !isMock) {
    return null
  }

  return (
    <div className="card" style={{ overflow: 'hidden' }}>
      <button
        type="button"
        onClick={() => setExpanded(e => !e)}
        style={{
          width: '100%', display: 'flex', alignItems: 'center', justifyContent: 'space-between',
          padding: '14px 20px', background: 'none', border: 'none', cursor: 'pointer',
          borderBottom: expanded ? '1px solid var(--color-ink-border)' : 'none',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
          <span style={{ fontSize: 16 }}>&#x1F916;</span>
          <div style={{ textAlign: 'left' }}>
            <div className="font-mono" style={{ fontSize: 13, color: 'var(--color-white)', fontWeight: 600, letterSpacing: '0.05em' }}>
              AI INVESTIGATION
            </div>
            <div className="font-body text-slate" style={{ fontSize: 12, marginTop: 2 }}>
              {isMock ? (
                <span style={{ color: 'var(--color-teal)' }}>DEMO RULE-BASED INVESTIGATION</span>
              ) : usedFallback ? (
                <span style={{ color: 'var(--color-amber)' }}>&#x26A0; DETERMINISTIC FALLBACK</span>
              ) : (
                <span style={{ color: 'var(--color-teal)' }}>AI AGENT INVESTIGATION</span>
              )}
            </div>
          </div>
        </div>
        <span className="font-mono text-slate" style={{ fontSize: 12, transform: expanded ? 'rotate(180deg)' : 'none', transition: 'transform 0.2s' }}>&#x25BC;</span>
      </button>

      {expanded && (
        <div style={{ padding: '16px 20px' }}>
          
          {isMock ? (
            <div style={{ paddingLeft: 20, marginBottom: 20 }}>
              <p className="font-body text-slate" style={{ fontSize: 12, fontStyle: 'italic', marginBottom: 16 }}>
                Deterministic safety analysis used because live AI verification is unavailable.
              </p>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
                  <span style={{ color: 'var(--color-teal)' }}>&#x2713;</span><span className="font-mono text-white" style={{ fontSize: 12 }}>Case analyzed</span>
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
                  <span style={{ color: 'var(--color-teal)' }}>&#x2713;</span><span className="font-mono text-white" style={{ fontSize: 12 }}>Evidence collected</span>
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
                  <span style={{ color: 'var(--color-teal)' }}>&#x2713;</span><span className="font-mono text-white" style={{ fontSize: 12 }}>Claims compared</span>
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
                  <span style={{ color: 'var(--color-teal)' }}>&#x2713;</span><span className="font-mono text-white" style={{ fontSize: 12 }}>Decision policy applied</span>
                </div>
              </div>
            </div>
          ) : (
            <>
              {toolCalls.length > 0 && (
                <div style={{ position: 'relative', paddingLeft: 20, marginBottom: recStep ? 20 : 0 }}>
                  <div style={{ position: 'absolute', left: 6, top: 8, bottom: 8, width: 2, background: 'var(--color-ink-border)' }} />
                  {toolCalls.map((tc, i) => (
                    <div key={i} style={{ position: 'relative', marginBottom: 16, paddingLeft: 12 }}>
                      <div style={{
                        position: 'absolute', left: -8, top: 4,
                        width: 8, height: 8, borderRadius: '50%',
                        background: 'var(--color-teal)', border: '2px solid var(--color-ink)',
                      }} />
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                        <div>
                          <span className="font-mono" style={{ fontSize: 11, color: 'var(--color-slate-light)', display: 'block' }}>
                            STEP {i + 1}
                          </span>
                          <span className="font-mono" style={{ fontSize: 13, color: 'var(--color-white)', fontWeight: 600 }}>
                            {TOOL_LABEL[tc.tool] ?? tc.tool}
                          </span>
                          <span className="font-mono" style={{ fontSize: 11, color: 'var(--color-teal)', display: 'block', marginTop: 4 }}>
                            &#x2713; Completed
                          </span>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </>
          )}

          {recStep && (
            <div style={{
              display: 'flex', alignItems: 'center', gap: 10,
              padding: '12px 16px', borderRadius: 6,
              background: 'rgba(63,167,150,0.08)', border: '1px solid rgba(63,167,150,0.2)',
            }}>
              <span style={{ fontSize: 16 }}>&#x1F916;</span>
              <div>
                <span className="font-mono" style={{ fontSize: 13, color: 'var(--color-teal)', fontWeight: 600 }}>
                  RECOMMENDATION GENERATED
                </span>
                <div className="font-mono" style={{ fontSize: 12, color: 'var(--color-white)', marginTop: 4 }}>
                  {typeof recStep.detail?.recommended_action === 'string' ? recStep.detail.recommended_action.toUpperCase() : 'COMPLETED'}
                </div>
                {usedFallback && (
                  <div className="font-body" style={{ fontSize: 12, color: 'var(--color-amber)', marginTop: 4 }}>
                    AI model unavailable - safety rules generated recommendation
                  </div>
                )}
              </div>
            </div>
          )}

        </div>
      )}
    </div>
  )
}
"""

pathlib.Path('src/components/AgentActivity.tsx').write_text(content, encoding='utf-8')
print("AgentActivity.tsx written cleanly")
