import type { AuditEntry } from '../types'
import { formatDate, getAgentToolCalls } from '../utils'
import { useState } from 'react'

interface Props {
  audit: AuditEntry[]
}

const TOOL_LABEL: Record<string, string> = {
  get_case_details: 'Fetch Case Details',
  get_payment_details: 'Query Payment API',
  get_refund_details: 'Query Refund API',
  search_case_evidence: 'Search Evidence Records',
  get_rule_flags: 'Evaluate Deterministic Rules',
  get_audit_log: 'Read Audit Trail',
}

export default function AgentActivity({ audit }: Props) {
  const [expanded, setExpanded] = useState(false)
  const toolCalls = getAgentToolCalls(audit)
  const recStep = audit.find(a => a.step === 'final_recommendation')
  const usedFallback = recStep?.detail?.used_fallback as boolean | undefined
  const totalSteps = toolCalls.length

  if (totalSteps === 0 && !recStep) {
    return (
      <div className="card" style={{ padding: '16px 20px' }}>
        <span className="font-mono text-slate" style={{ fontSize: 12 }}>No agent activity recorded yet.</span>
      </div>
    )
  }

  return (
    <div className="card" style={{ overflow: 'hidden' }}>
      {/* Header — always visible */}
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
          <span style={{ fontSize: 16 }}>🤖</span>
          <div style={{ textAlign: 'left' }}>
            <div className="font-mono" style={{ fontSize: 12, color: 'var(--color-white)', fontWeight: 600, letterSpacing: '0.05em' }}>
              AGENT INVESTIGATION
            </div>
            <div className="font-body text-slate" style={{ fontSize: 12, marginTop: 2 }}>
              {totalSteps} tool call{totalSteps !== 1 ? 's' : ''} executed
              {usedFallback && <span style={{ color: 'var(--color-amber)', marginLeft: 8 }}>· DETERMINISTIC FALLBACK</span>}
            </div>
          </div>
        </div>
        <span className="font-mono text-slate" style={{ fontSize: 12, transform: expanded ? 'rotate(180deg)' : 'none', transition: 'transform 0.2s' }}>▼</span>
      </button>

      {expanded && (
        <div style={{ padding: '16px 20px' }}>
          {/* Tool call steps */}
          {toolCalls.length > 0 && (
            <div style={{ position: 'relative', paddingLeft: 20, marginBottom: recStep ? 20 : 0 }}>
              {/* Vertical line */}
              <div style={{ position: 'absolute', left: 6, top: 8, bottom: 8, width: 2, background: 'var(--color-ink-border)' }} />
              {toolCalls.map((tc, i) => (
                <div key={i} style={{ position: 'relative', marginBottom: 14, paddingLeft: 12 }}>
                  {/* Dot */}
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
                      <span className="font-mono" style={{ fontSize: 10, color: 'var(--color-teal)', display: 'block', marginTop: 2 }}>
                        ✓ Completed
                      </span>
                    </div>
                    <span className="font-mono text-slate" style={{ fontSize: 10, whiteSpace: 'nowrap', marginLeft: 12 }}>
                      {formatDate(tc.timestamp)}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          )}

          {/* Final recommendation step */}
          {recStep && (
            <div style={{
              display: 'flex', alignItems: 'center', gap: 10,
              padding: '10px 14px', borderRadius: 6,
              background: 'rgba(63,167,150,0.08)', border: '1px solid rgba(63,167,150,0.2)',
            }}>
              <span style={{ fontSize: 14 }}>🏁</span>
              <div>
                <span className="font-mono" style={{ fontSize: 12, color: 'var(--color-teal)', fontWeight: 600 }}>
                  RECOMMENDATION GENERATED
                </span>
                {usedFallback && (
                  <div className="font-body" style={{ fontSize: 12, color: 'var(--color-amber)', marginTop: 2 }}>
                    Deterministic fallback used — AI model was not available or returned invalid output.
                  </div>
                )}
              </div>
            </div>
          )}

          <p className="font-body text-slate" style={{ fontSize: 11, marginTop: 16, fontStyle: 'italic', lineHeight: 1.5 }}>
            Note: Tool call inputs/outputs are not displayed to prevent exposure of internal reasoning. The AI agent read evidence and payment data, then produced a structured recommendation.
          </p>
        </div>
      )}
    </div>
  )
}
