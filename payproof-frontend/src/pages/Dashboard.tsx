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
 * Dashboard - the case list page.
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

  const filterGroups: Partial<Record<FilterValue, string[]>> = {
    'all': [],
    'strong_case': ['strong_case', 'accept', 'contest', 'pending_review'],
    'human_review': ['human_review', 'escalate', 'escalated'],
    'request_more_evidence': ['request_more_evidence', 'evidence_requested', 'weak_case'],
    'investigating': ['investigating', 'new', 'under_review', 'action_required'],
    'closed': ['closed', 'resolved', 'won', 'lost']
  }

  const filtered = filter === 'all' 
    ? cases 
    : cases.filter((c) => filterGroups[filter]?.includes(c.status) ?? c.status === filter)

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

      {/* Loading state - Skeletons */}
      {loading && (
        <div>
          {[...Array(5)].map((_, i) => (
            <CaseCardSkeleton key={i} index={i} />
          ))}
          <div style={{ textAlign: 'center', marginTop: 24 }}>
            <span className="font-mono text-slate" style={{ fontSize: 11, letterSpacing: '0.06em' }}>
              WAKING BACKEND...
            </span>
          </div>
        </div>
      )}

      {/* Error state */}
      {error && !loading && (
        <div
          className="card verdict-edge-red"
          style={{ padding: '18px 22px', marginBottom: 16 }}
        >
          <span className="font-mono text-red" style={{ fontSize: 13 }}>
            Error: Could not reach the backend: {error}
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
            (empty)
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

      {/* Live indicator shows when polling is active */}
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
            LIVE refreshes every 8s
          </span>
        </motion.div>
      )}

      <style>{`
        @keyframes pulse {
          0%, 100% { opacity: 1; }
          50% { opacity: 0.3; }
        }
      `}</style>

      {(import.meta.env.DEV || import.meta.env.VITE_DEMO_MODE === 'true') && (
      <div style={{ textAlign: 'center', marginTop: 40, borderTop: '1px solid var(--color-ink-border)', paddingTop: 24 }}>
        <button 
          onClick={async () => {
            if (window.confirm("Are you sure you want to delete all demo cases? This will clear the dashboard.")) {
              await api.resetDemoCases();
              window.location.reload();
            }
          }}
          className="font-mono text-slate" 
          style={{ fontSize: 11, background: 'transparent', border: '1px solid var(--color-ink-border)', padding: '6px 12px', borderRadius: 4, cursor: 'pointer' }}
        >
          RESET DEMO CASES
        </button>
      </div>
      )}
    </main>
  )
}



function CaseCardSkeleton({ index }: { index: number }) {
  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ duration: 0.3, delay: index * 0.05 }}
      className="card grid grid-cols-1 md:grid-cols-[1fr_200px_200px_32px] gap-5 items-start md:items-center"
      style={{
        padding: '16px 20px',
        marginBottom: 8,
        borderColor: 'var(--color-ink-border)',
        background: 'rgba(255, 255, 255, 0.01)',
      }}
    >
      <div>
        <div style={{ height: 16, width: '40%', background: 'var(--color-ink-border)', borderRadius: 4, marginBottom: 8, animation: 'pulse 1.5s infinite' }} />
        <div style={{ height: 14, width: '70%', background: 'var(--color-ink-border)', borderRadius: 4, marginBottom: 8, animation: 'pulse 1.5s infinite 0.2s' }} />
        <div style={{ height: 12, width: '20%', background: 'var(--color-ink-border)', borderRadius: 4, animation: 'pulse 1.5s infinite 0.4s' }} />
      </div>
      <div>
        <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 6 }}>
          <div style={{ height: 12, width: '40%', background: 'var(--color-ink-border)', borderRadius: 4 }} />
          <div style={{ height: 12, width: '40%', background: 'var(--color-ink-border)', borderRadius: 4 }} />
        </div>
        <div style={{ height: 8, width: '100%', background: 'var(--color-ink-border)', borderRadius: 4, marginBottom: 8, animation: 'pulse 1.5s infinite 0.1s' }} />
        <div style={{ display: 'flex', justifyContent: 'flex-end' }}>
           <div style={{ height: 12, width: '20%', background: 'var(--color-ink-border)', borderRadius: 4 }} />
        </div>
      </div>
      <div className="flex flex-row md:flex-col items-center md:items-end justify-between w-full md:w-auto mt-2 md:mt-0">
         <div style={{ height: 24, width: '60px', background: 'var(--color-ink-border)', borderRadius: 12, animation: 'pulse 1.5s infinite 0.3s' }} className="md:mb-3" />
         <div style={{ height: 12, width: '80px', background: 'var(--color-ink-border)', borderRadius: 4 }} />
      </div>
      <div className="flex justify-end md:justify-center w-full mt-2 md:mt-0">
        <div style={{ height: 16, width: 16, background: 'var(--color-ink-border)', borderRadius: 4, animation: 'pulse 1.5s infinite 0.5s' }} />
      </div>
    </motion.div>
  )
}
