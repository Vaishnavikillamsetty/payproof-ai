import { useEffect, useState } from 'react'
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
import type { EvalMetrics } from '../types'

export default function Metrics() {
  const [metrics, setMetrics] = useState<EvalMetrics | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    api.getMetrics()
      .then((data) => setMetrics(data))
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false))
  }, [])

  if (loading) {
    return (
      <div style={{ padding: 60, textAlign: 'center', color: 'var(--color-slate)' }}>
        <div style={{ animation: 'spin 1s linear infinite', display: 'inline-block', marginBottom: 16 }}>◒</div>
        <div className="font-body">Loading evaluation metrics...</div>
      </div>
    )
  }

  if (error || !metrics) {
    return (
      <div style={{ padding: 60, textAlign: 'center', color: 'var(--color-red)' }}>
        <div className="font-mono">ERROR</div>
        <div className="font-body">{error}</div>
      </div>
    )
  }

  const { confusion_matrix: cm, rates, business_impact: biz } = metrics

  // Data for Recharts
  const data = [
    { name: 'True Negative (Correct Auto-Resolve)', count: cm.true_negatives, color: 'var(--color-teal)' },
    { name: 'True Positive (Correct Review)', count: cm.true_positives, color: 'var(--color-teal)' },
    { name: 'False Positive (Wasted Review)', count: cm.false_positives, color: 'var(--color-amber)' },
    { name: 'False Negative (Unsafe Auto)', count: cm.false_negatives, color: 'var(--color-red)' },
  ]

  return (
    <main style={{ maxWidth: 1000, margin: '0 auto', padding: '40px 24px' }}>
      <div style={{ marginBottom: 40 }}>
        <h1 className="font-mono text-slate" style={{ fontSize: 13, letterSpacing: '0.12em', textTransform: 'uppercase', marginBottom: 8 }}>
          System Evaluation (Synthetic Held-Out Dataset)
        </h1>
        <p className="font-body text-white" style={{ fontSize: 28, fontWeight: 600, lineHeight: 1.2 }}>
          Performance Metrics
        </p>
        <p className="font-body text-amber" style={{ fontSize: 13, marginTop: 12, padding: "8px 12px", background: "rgba(224, 163, 57, 0.1)", borderRadius: 4, display: "inline-block" }}>Note: Metrics are computed from a fixed synthetic evaluation dataset and are NOT derived from live submitted cases.</p>
      </div>

      {/* Explanation Block */}
      <div style={{ background: 'var(--color-ink-light)', padding: '20px 24px', borderRadius: 6, marginBottom: 40, border: '1px solid var(--color-ink-border)' }}>
        <h2 className="font-mono text-slate" style={{ fontSize: 12, textTransform: 'uppercase', marginBottom: 16 }}>Metric Definitions</h2>
        <ul className="font-body text-slate-light" style={{ fontSize: 14, lineHeight: 1.6, paddingLeft: 20, margin: '0 0 16px 0' }}>
          <li><strong style={{ color: 'var(--color-teal)' }}>True Positive (Correct):</strong> An ambiguous case correctly routed to human review.</li>
          <li><strong style={{ color: 'var(--color-amber)' }}>False Positive (Cost):</strong> A clear case unnecessarily routed to human review (wasted manual effort).</li>
          <li><strong style={{ color: 'var(--color-red)' }}>Unsafe Resolve (Failure):</strong> An ambiguous case dangerously auto-resolved (our worst failure type).</li>
        </ul>
        <p className="font-body text-white" style={{ fontSize: 14, fontStyle: 'italic', margin: 0, padding: '16px 0 0 0', borderTop: '1px solid var(--color-ink-border)' }}>
          This system prioritizes safety over automation efficiency — {cm.false_negatives} unsafe resolves, with {cm.false_positives} unnecessary human reviews as the current tradeoff. Policy tuning is the next optimization target.
        </p>
      </div>

      {/* Top Section: Precision / Recall */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 24, marginBottom: 40 }}>
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

      {/* Middle Section: Cost / Business Impact */}
      <div className="card" style={{ padding: 32, marginBottom: 40, borderLeft: '4px solid var(--color-amber)' }}>
        <h2 className="font-mono text-slate" style={{ fontSize: 13, textTransform: 'uppercase', marginBottom: 16 }}>
          Business Impact
        </h2>
        <p className="font-body text-white" style={{ fontSize: 16, lineHeight: 1.5, marginBottom: 20 }}>
          {biz.cost_statement}
        </p>
        
        <div style={{ padding: 16, background: biz.unsafe_resolves > 0 ? 'rgba(214, 72, 60, 0.1)' : 'rgba(63, 167, 150, 0.1)', borderRadius: 6, border: `1px solid ${biz.unsafe_resolves > 0 ? 'var(--color-red)' : 'var(--color-teal)'}` }}>
          <p className="font-body" style={{ color: biz.unsafe_resolves > 0 ? 'var(--color-red)' : 'var(--color-teal)', fontSize: 15, margin: 0 }}>
            {biz.unsafe_statement}
          </p>
        </div>
      </div>

      {/* Bottom Section: Confusion Matrix Chart */}
      <div className="card" style={{ padding: '32px 32px 48px 32px' }}>
        <h2 className="font-mono text-slate" style={{ fontSize: 13, textTransform: 'uppercase', marginBottom: 32 }}>
          Confusion Matrix Distribution (N={cm.total})
        </h2>
        
        <div style={{ width: '100%', height: 350 }}>
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

        <div style={{ marginTop: 40, paddingTop: 24, borderTop: '1px solid var(--color-ink-border)' }}>
          <h3 className="font-mono text-slate" style={{ fontSize: 11, textTransform: 'uppercase', marginBottom: 12 }}>
            Data Interpretation
          </h3>
          <p className="font-body text-slate-light" style={{ fontSize: 14, lineHeight: 1.6 }}>
            The current policy is {cm.false_negatives === 0 && cm.false_positives > 0 ? 'conservative' : 'balanced'}. 
            It achieved {cm.false_negatives} unsafe auto-resolves on this synthetic evaluation set, but {cm.false_positives} cases 
            were unnecessarily routed to human review. Future improvements should reduce unnecessary reviews without 
            increasing unsafe auto-resolves.
          </p>
        </div>
      </div>
      
      {/* Benchmark Note */}
      <div style={{ marginTop: 24, textAlign: 'center' }}>
        <p className="font-body text-slate-light" style={{ fontSize: 12 }}>
          * Benchmark metrics are computed from a fixed 30-case evaluation set, separate from live cases you submit here.
        </p>
      </div>
    </main>
  )
}
