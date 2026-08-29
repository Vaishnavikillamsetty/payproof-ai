import { useEffect, useState } from 'react'
import { AnimatePresence, motion } from 'framer-motion'
import { api } from '../api'
import type { Case, CaseStatus } from '../types'
import CaseCard from '../components/CaseCard'
import FilterPills from '../components/FilterPills'
import SummaryStrip from '../components/SummaryStrip'

type FilterValue = CaseStatus | 'all'

interface Props {
  onSelectCase: (id: string) => void
}

/**
 * Dashboard — the case list page.
 *
 * Shows the summary strip, filter pills, then an animated stack of CaseCards.
 * Polls every 8s so newly submitted cases (which process in background) appear.
 */
export default function Dashboard({ onSelectCase }: Props) {
  const [cases, setCases] = useState<Case[]>([])
  const [filter, setFilter] = useState<FilterValue>('all')
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const load = () => {
    api
      .getCases()
      .then((data) => {
        setCases(data)
        setError(null)
      })
      .catch((e: Error) => setError(e.message))
      .finally(() => setLoading(false))
  }

  // Initial load + polling every 8s so pipeline results surface automatically
  useEffect(() => {
    load()
    const id = setInterval(load, 8000)
    return () => clearInterval(id)
  }, [])

  const filtered =
    filter === 'all' ? cases : cases.filter((c) => c.status === filter)

  return (
    <main style={{ maxWidth: 1200, margin: '0 auto', padding: '32px 24px' }}>
      {/* Page heading */}
      <div style={{ marginBottom: 28 }}>
        <h1
          className="font-mono"
          style={{
            fontSize: 13,
            fontWeight: 600,
            letterSpacing: '0.12em',
            textTransform: 'uppercase',
            color: 'var(--color-slate)',
            marginBottom: 8,
          }}
        >
          Case Registry
        </h1>
        <p
          className="font-body"
          style={{
            fontSize: 28,
            fontWeight: 600,
            color: 'var(--color-white)',
            lineHeight: 1.2,
          }}
        >
          Dispute Cases
        </p>
      </div>

      {/* Summary strip */}
      <SummaryStrip cases={cases} />

      {/* Section label + filters */}
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          marginBottom: 12,
          flexWrap: 'wrap',
          gap: 12,
        }}
      >
        <span
          className="font-mono text-slate"
          style={{ fontSize: 11, letterSpacing: '0.12em', textTransform: 'uppercase' }}
        >
          {filtered.length} case{filtered.length !== 1 ? 's' : ''}
        </span>
        <FilterPills active={filter} onChange={setFilter} />
      </div>

      {/* Loading state */}
      {loading && (
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            padding: '60px 0',
          }}
        >
          <LoadingSpinner />
          <span className="font-body text-slate" style={{ marginLeft: 12, fontSize: 14 }}>
            Loading cases…
          </span>
        </div>
      )}

      {/* Error state */}
      {error && !loading && (
        <div
          className="card verdict-edge-red"
          style={{ padding: '18px 22px', marginBottom: 16 }}
        >
          <span className="font-mono text-red" style={{ fontSize: 13 }}>
            ⚠ Could not reach the backend: {error}
          </span>
          <div className="font-body text-slate" style={{ fontSize: 13, marginTop: 6 }}>
            Make sure{' '}
            <code
              style={{
                fontFamily: 'var(--font-mono)',
                background: 'rgba(255,255,255,0.06)',
                padding: '1px 6px',
                borderRadius: 3,
              }}
            >
              uvicorn app.main:app --reload
            </code>{' '}
            is running on port 8000.
          </div>
        </div>
      )}

      {/* Empty state */}
      {!loading && !error && filtered.length === 0 && (
        <div
          style={{
            textAlign: 'center',
            padding: '60px 0',
            color: 'var(--color-slate)',
          }}
        >
          <div
            className="font-mono"
            style={{ fontSize: 32, marginBottom: 12, opacity: 0.3 }}
          >
            ∅
          </div>
          <p className="font-body" style={{ fontSize: 15 }}>
            {filter === 'all'
              ? 'No cases yet. Submit a dispute to get started.'
              : `No cases with status "${filter}".`}
          </p>
        </div>
      )}

      {/* Case list */}
      {!loading && (
        <AnimatePresence mode="popLayout">
          {filtered.map((c, i) => (
            <CaseCard
              key={c.id}
              case_={c}
              index={i}
              onSelect={onSelectCase}
            />
          ))}
        </AnimatePresence>
      )}

      {/* Live indicator — shows when polling is active */}
      {!loading && !error && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.5 }}
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: 8,
            marginTop: 24,
            justifyContent: 'center',
          }}
        >
          <span
            style={{
              width: 6,
              height: 6,
              borderRadius: '50%',
              background: 'var(--color-teal)',
              animation: 'pulse 2s infinite',
              display: 'inline-block',
            }}
          />
          <span className="font-mono text-slate" style={{ fontSize: 11, letterSpacing: '0.06em' }}>
            LIVE · refreshes every 8s
          </span>
        </motion.div>
      )}

      <style>{`
        @keyframes pulse {
          0%, 100% { opacity: 1; }
          50% { opacity: 0.3; }
        }
      `}</style>
    </main>
  )
}

function LoadingSpinner() {
  return (
    <svg
      width="20"
      height="20"
      viewBox="0 0 20 20"
      fill="none"
      aria-hidden="true"
      style={{ animation: 'spin 0.8s linear infinite' }}
    >
      <circle
        cx="10"
        cy="10"
        r="8"
        stroke="var(--color-ink-border)"
        strokeWidth="2"
      />
      <path
        d="M10 2a8 8 0 0 1 8 8"
        stroke="var(--color-teal)"
        strokeWidth="2"
        strokeLinecap="round"
      />
      <style>{`@keyframes spin { to { transform: rotate(360deg); } }`}</style>
    </svg>
  )
}
