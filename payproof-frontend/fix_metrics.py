import pathlib

# ── FIX 2: Metrics.tsx ─────────────────────────────────────────────────────
# Keep benchmark section exactly as-is.
# Add LIVE CASE ACTIVITY section below it, using api.getCases().
#
# Live statistic mapping from existing CaseStatus values:
#   Cases Processed  = all cases with a terminal/investigated status
#                      (anything that's not 'new' or 'investigating')
#   Auto-Resolved    = 'strong_case' | 'resolved' | 'accept' | 'contest' | 'won'
#   Human Review     = 'human_review' | 'escalate' | 'request_more_evidence'
#   Insufficient Ev. = 'weak_case'
#   Contradictions   = cases with completeness_score < 50 AND
#                      overall_confidence not null AND human_review status

metrics_src = r'''import { useEffect, useState } from 'react'
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Cell,
} from 'recharts'
import { api } from '../api'
import type { EvalMetrics, Case } from '../types'

// ── Live statistics derived from actual case statuses ───────────────────────
// Mapping is based on the CaseStatus type defined in types.ts.
const AUTO_RESOLVED_STATUSES = new Set([
  'strong_case', 'resolved', 'accept', 'contest', 'won', 'closed',
])
const HUMAN_REVIEW_STATUSES = new Set([
  'human_review', 'escalate', 'request_more_evidence',
])
const INSUFFICIENT_EVIDENCE_STATUSES = new Set(['weak_case'])
// "Processed" = investigation finished (exclude cases still queued/investigating)
const IN_FLIGHT_STATUSES = new Set(['new', 'investigating'])

function computeLiveStats(cases: Case[]) {
  const processed = cases.filter(c => !IN_FLIGHT_STATUSES.has(c.status))
  const autoResolved = processed.filter(c => AUTO_RESOLVED_STATUSES.has(c.status))
  const humanReview = processed.filter(c => HUMAN_REVIEW_STATUSES.has(c.status))
  const insufficient = processed.filter(c => INSUFFICIENT_EVIDENCE_STATUSES.has(c.status))
  // Contradictions: resolved into human review with contradictory signals
  // We use cases in human_review / escalate that have a low completeness score
  // as a proxy for contradiction-driven escalation.
  const contradictions = processed.filter(
    c => (c.status === 'human_review' || c.status === 'escalate') &&
         c.completeness_score !== null && c.completeness_score < 50
  )
  return {
    total: cases.length,
    processed: processed.length,
    autoResolved: autoResolved.length,
    humanReview: humanReview.length,
    insufficient: insufficient.length,
    contradictions: contradictions.length,
  }
}

function LiveStatRow({ label, value, color = 'var(--color-white)' }: { label: string, value: number, color?: string }) {
  return (
    <div style={{
      display: 'flex',
      justifyContent: 'space-between',
      alignItems: 'center',
      padding: '14px 0',
      borderBottom: '1px solid var(--color-ink-border)',
    }}>
      <span className="font-body" style={{ fontSize: 14, color: 'var(--color-slate-light)' }}>{label}</span>
      <span className="font-mono" style={{ fontSize: 22, fontWeight: 700, color }}>{value}</span>
    </div>
  )
}

export default function Metrics() {
  const [metrics, setMetrics] = useState<EvalMetrics | null>(null)
  const [loadingMetrics, setLoadingMetrics] = useState(true)
  const [errorMetrics, setErrorMetrics] = useState<string | null>(null)

  const [cases, setCases] = useState<Case[]>([])
  const [loadingCases, setLoadingCases] = useState(true)

  // Load fixed benchmark metrics once
  useEffect(() => {
    api.getMetrics()
      .then(data => setMetrics(data))
      .catch(err => setErrorMetrics(err.message))
      .finally(() => setLoadingMetrics(false))
  }, [])

  // Load live cases, then poll every 10s so new submissions surface automatically
  useEffect(() => {
    const load = () =>
      api.getCases()
        .then(data => setCases(data))
        .catch(() => { /* silently ignore – live section shows 0 on failure */ })
        .finally(() => setLoadingCases(false))

    load()
    const id = setInterval(load, 10_000)
    return () => clearInterval(id)
  }, [])

  if (loadingMetrics) {
    return (
      <div style={{ padding: 60, textAlign: 'center', color: 'var(--color-slate)' }}>
        <div style={{ animation: 'spin 1s linear infinite', display: 'inline-block', marginBottom: 16 }}>◒</div>
        <div className="font-body">Loading evaluation metrics...</div>
      </div>
    )
  }

  if (errorMetrics || !metrics) {
    return (
      <div style={{ padding: 60, textAlign: 'center', color: 'var(--color-red)' }}>
        <div className="font-mono">ERROR</div>
        <div className="font-body">{errorMetrics}</div>
      </div>
    )
  }

  const { confusion_matrix: cm, rates, business_impact: biz } = metrics
  const live = computeLiveStats(cases)

  // Data for Recharts
  const data = [
    { name: 'True Negative (Correct Auto-Resolve)', count: cm.true_negatives, color: 'var(--color-teal)' },
    { name: 'True Positive (Correct Review)', count: cm.true_positives, color: 'var(--color-teal)' },
    { name: 'False Positive (Wasted Review)', count: cm.false_positives, color: 'var(--color-amber)' },
    { name: 'False Negative (Unsafe Auto)', count: cm.false_negatives, color: 'var(--color-red)' },
  ]

  return (
    <main style={{ maxWidth: 1000, margin: '0 auto', padding: '40px 24px' }}>

      {/* ── Page heading ── */}
      <div style={{ marginBottom: 40 }}>
        <h1 className="font-mono text-slate" style={{ fontSize: 13, letterSpacing: '0.12em', textTransform: 'uppercase', marginBottom: 8 }}>
          Performance Metrics
        </h1>
        <p className="font-body text-white" style={{ fontSize: 28, fontWeight: 600, lineHeight: 1.2 }}>
          System Evaluation
        </p>
      </div>

      {/* ══════════════════════════════════════════════════════════════════════
          SECTION A — FIXED BENCHMARK (synthetic held-out dataset)
          These numbers are deterministic and never change when you submit cases.
      ════════════════════════════════════════════════════════════════════════ */}
      <div style={{ marginBottom: 8 }}>
        <span className="font-mono" style={{
          fontSize: 11, letterSpacing: '0.1em', textTransform: 'uppercase',
          color: 'var(--color-slate)', display: 'block', marginBottom: 4,
        }}>
          Section A
        </span>
        <h2 className="font-body text-white" style={{ fontSize: 20, fontWeight: 600, marginBottom: 4 }}>
          Fixed Benchmark
        </h2>
        <p className="font-body text-slate-light" style={{ fontSize: 13, marginBottom: 16 }}>
          Synthetic 30-case held-out evaluation set. These numbers do <em>not</em> change when you submit live cases.
        </p>
      </div>

      {/* Explanation Block */}
      <div style={{ background: 'var(--color-ink-light)', padding: '20px 24px', borderRadius: 6, marginBottom: 32, border: '1px solid var(--color-ink-border)' }}>
        <h3 className="font-mono text-slate" style={{ fontSize: 12, textTransform: 'uppercase', marginBottom: 16 }}>Metric Definitions</h3>
        <ul className="font-body text-slate-light" style={{ fontSize: 14, lineHeight: 1.6, paddingLeft: 20, margin: '0 0 16px 0' }}>
          <li><strong style={{ color: 'var(--color-teal)' }}>True Positive (Correct):</strong> An ambiguous case correctly routed to human review.</li>
          <li><strong style={{ color: 'var(--color-amber)' }}>False Positive (Cost):</strong> A clear case unnecessarily routed to human review (wasted manual effort).</li>
          <li><strong style={{ color: 'var(--color-red)' }}>Unsafe Resolve (Failure):</strong> An ambiguous case dangerously auto-resolved (our worst failure type).</li>
        </ul>
        <p className="font-body text-white" style={{ fontSize: 14, fontStyle: 'italic', margin: 0, padding: '16px 0 0 0', borderTop: '1px solid var(--color-ink-border)' }}>
          This system prioritizes safety over automation efficiency — {cm.false_negatives} unsafe resolves,
          with {cm.false_positives} unnecessary human reviews as the current tradeoff.
          Policy tuning is the next optimization target.
        </p>
      </div>

      {/* Precision / Recall */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 24, marginBottom: 32 }}>
        <div className="card" style={{ padding: 32, textAlign: 'center' }}>
          <div className="font-mono text-slate" style={{ fontSize: 13, textTransform: 'uppercase', marginBottom: 12 }}>Precision</div>
          <div className="font-body text-white" style={{ fontSize: 48, fontWeight: 700 }}>
            {(rates.precision * 100).toFixed(1)}%
          </div>
          <div className="font-body text-slate-light" style={{ fontSize: 13, marginTop: 8 }}>
            % of auto-flagged cases that actually required review
          </div>
        </div>
        <div className="card" style={{ padding: 32, textAlign: 'center' }}>
          <div className="font-mono text-slate" style={{ fontSize: 13, textTransform: 'uppercase', marginBottom: 12 }}>Recall</div>
          <div className="font-body text-white" style={{ fontSize: 48, fontWeight: 700 }}>
            {(rates.recall * 100).toFixed(1)}%
          </div>
          <div className="font-body text-slate-light" style={{ fontSize: 13, marginTop: 8 }}>
            % of ambiguous cases correctly caught by the policy gate
          </div>
        </div>
      </div>

      {/* Benchmark Business Impact */}
      <div className="card" style={{ padding: 32, marginBottom: 32, borderLeft: '4px solid var(--color-amber)' }}>
        <h3 className="font-mono text-slate" style={{ fontSize: 13, textTransform: 'uppercase', marginBottom: 4 }}>
          Benchmark Business Impact
        </h3>
        <p className="font-mono text-slate-light" style={{ fontSize: 11, marginBottom: 16 }}>
          Based on the synthetic 30-case evaluation set — not affected by live submissions.
        </p>
        <p className="font-body text-white" style={{ fontSize: 16, lineHeight: 1.5, marginBottom: 20 }}>
          {biz.cost_statement}
        </p>
        <div style={{
          padding: 16,
          background: biz.unsafe_resolves > 0 ? 'rgba(214, 72, 60, 0.1)' : 'rgba(63, 167, 150, 0.1)',
          borderRadius: 6,
          border: `1px solid ${biz.unsafe_resolves > 0 ? 'var(--color-red)' : 'var(--color-teal)'}`,
        }}>
          <p className="font-body" style={{ color: biz.unsafe_resolves > 0 ? 'var(--color-red)' : 'var(--color-teal)', fontSize: 15, margin: 0 }}>
            {biz.unsafe_statement}
          </p>
        </div>
      </div>

      {/* Confusion Matrix Chart */}
      <div className="card" style={{ padding: '32px 32px 48px 32px', marginBottom: 48 }}>
        <h3 className="font-mono text-slate" style={{ fontSize: 13, textTransform: 'uppercase', marginBottom: 32 }}>
          Confusion Matrix Distribution (N={cm.total})
        </h3>
        <div style={{ width: '100%', height: 300 }}>
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={data} layout="vertical" margin={{ top: 0, right: 30, left: 0, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="var(--color-ink-border)" horizontal={true} vertical={false} />
              <XAxis type="number" stroke="var(--color-slate)" tick={{ fontFamily: 'var(--font-mono)', fontSize: 11 }} />
              <YAxis
                dataKey="name"
                type="category"
                width={160}
                stroke="var(--color-slate)"
                tick={{ fontFamily: 'var(--font-mono)', fontSize: 11 }}
              />
              <Tooltip
                cursor={{ fill: 'rgba(255,255,255,0.05)' }}
                contentStyle={{ background: 'var(--color-ink-light)', border: '1px solid var(--color-ink-border)', borderRadius: 4, fontFamily: 'var(--font-body)' }}
                itemStyle={{ color: 'var(--color-white)' }}
              />
              <Bar dataKey="count" radius={[0, 4, 4, 0]} barSize={40}>
                {data.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={entry.color} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
        <div style={{ marginTop: 32, paddingTop: 24, borderTop: '1px solid var(--color-ink-border)' }}>
          <h4 className="font-mono text-slate" style={{ fontSize: 11, textTransform: 'uppercase', marginBottom: 12 }}>Data Interpretation</h4>
          <p className="font-body text-slate-light" style={{ fontSize: 14, lineHeight: 1.6 }}>
            The current policy is {cm.false_negatives === 0 && cm.false_positives > 0 ? 'conservative' : 'balanced'}.
            It achieved {cm.false_negatives} unsafe auto-resolves on this synthetic evaluation set, but {cm.false_positives} cases
            were unnecessarily routed to human review. Future improvements should reduce unnecessary reviews without
            increasing unsafe auto-resolves.
          </p>
        </div>
      </div>

      {/* Divider between sections */}
      <div style={{ position: 'relative', textAlign: 'center', marginBottom: 48 }}>
        <div style={{ position: 'absolute', top: '50%', left: 0, right: 0, height: 1, background: 'var(--color-ink-border)' }} />
        <span className="font-mono text-slate" style={{
          position: 'relative', fontSize: 11, letterSpacing: '0.12em', textTransform: 'uppercase',
          background: 'var(--color-ink)', padding: '0 16px',
        }}>
          Live Data
        </span>
      </div>

      {/* ══════════════════════════════════════════════════════════════════════
          SECTION B — LIVE CASE ACTIVITY
          Derived from the actual cases in the database via /cases/ API.
          Updates every 10 seconds automatically.
      ════════════════════════════════════════════════════════════════════════ */}
      <div style={{ marginBottom: 8 }}>
        <span className="font-mono" style={{
          fontSize: 11, letterSpacing: '0.1em', textTransform: 'uppercase',
          color: 'var(--color-slate)', display: 'block', marginBottom: 4,
        }}>
          Section B
        </span>
        <h2 className="font-body text-white" style={{ fontSize: 20, fontWeight: 600, marginBottom: 4 }}>
          Live Case Activity
        </h2>
        <p className="font-body text-slate-light" style={{ fontSize: 13, marginBottom: 24 }}>
          Counts from cases currently in the database. Updates automatically every 10 s.
          {loadingCases && <span style={{ marginLeft: 8, color: 'var(--color-slate)' }}>Loading...</span>}
        </p>
      </div>

      <div className="card" style={{ padding: 32 }}>
        <div style={{ marginBottom: 8 }}>
          <LiveStatRow
            label="Total Cases Submitted"
            value={live.total}
          />
          <LiveStatRow
            label="Cases Processed (investigation complete)"
            value={live.processed}
            color="var(--color-teal)"
          />
          <LiveStatRow
            label="Auto-Resolved (strong case / resolved / won)"
            value={live.autoResolved}
            color="var(--color-teal)"
          />
          <LiveStatRow
            label="Flagged for Human Review"
            value={live.humanReview}
            color="var(--color-amber)"
          />
          <LiveStatRow
            label="Insufficient Evidence (weak case)"
            value={live.insufficient}
            color="var(--color-amber)"
          />
          <div style={{
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            padding: '14px 0',
          }}>
            <span className="font-body" style={{ fontSize: 14, color: 'var(--color-slate-light)' }}>Contradiction-Escalated</span>
            <span className="font-mono" style={{ fontSize: 22, fontWeight: 700, color: 'var(--color-red)' }}>{live.contradictions}</span>
          </div>
        </div>

        {live.total === 0 && !loadingCases && (
          <div style={{ marginTop: 16, padding: '12px 16px', background: 'rgba(91,107,124,0.1)', borderRadius: 6, borderLeft: '3px solid var(--color-ink-border)' }}>
            <p className="font-body text-slate" style={{ fontSize: 13, margin: 0 }}>
              No cases submitted yet. Create a case from the dashboard to see live statistics update here.
            </p>
          </div>
        )}

        <div style={{ marginTop: 24, paddingTop: 16, borderTop: '1px solid var(--color-ink-border)' }}>
          <p className="font-body text-slate-light" style={{ fontSize: 12, margin: 0, lineHeight: 1.5 }}>
            Status mapping: <em>Auto-Resolved</em> includes statuses strong_case, resolved, accept, contest, won, closed.
            <em> Human Review</em> includes human_review, escalate, request_more_evidence.
            <em> Contradictions</em> are escalated cases with completeness score below 50%.
          </p>
        </div>
      </div>

      {/* Footer note */}
      <div style={{ marginTop: 24, textAlign: 'center' }}>
        <p className="font-body text-slate-light" style={{ fontSize: 12 }}>
          * Section A benchmark metrics are computed from a fixed 30-case evaluation set, separate from live cases you submit.
        </p>
      </div>

    </main>
  )
}
'''

pathlib.Path('src/pages/Metrics.tsx').write_text(metrics_src, encoding='utf-8')
print("Metrics.tsx written")
