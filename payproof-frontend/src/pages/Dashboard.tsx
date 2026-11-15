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
    <main style={{ maxWidth: 1200, margin: "0 auto", padding: "32px 24px" }}>
      {/* Page heading */}
      <div style={{ marginBottom: 32 }}>
        <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 6 }}>
          <div style={{ width: 3, height: 20, background: "var(--color-teal)", borderRadius: 2, flexShrink: 0 }} />
          <span
            className="font-mono"
            style={{
              fontSize: 11,
              fontWeight: 600,
              letterSpacing: "0.14em",
              textTransform: "uppercase",
              color: "var(--color-teal)",
            }}
          >
            Case Registry
          </span>
        </div>
        <h1
          className="font-body"
          style={{
            fontSize: 30,
            fontWeight: 700,
            color: "var(--color-white)",
            lineHeight: 1.15,
            letterSpacing: "-0.01em",
          }}
        >
          Dispute Cases
        </h1>
      </div>

      {/* Summary strip */}
      <SummaryStrip cases={cases} />

      {/* Section label + filters */}
      <div
        style={{
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          marginBottom: 14,
          flexWrap: "wrap",
          gap: 12,
          borderTop: "1px solid var(--color-ink-border)",
          paddingTop: 20,
        }}
      >
        <span
          className="font-mono"
          style={{ fontSize: 11, letterSpacing: "0.1em", textTransform: "uppercase", color: "var(--color-slate)" }}
        >
          {filtered.length} case{filtered.length !== 1 ? "s" : ""}
        </span>
        <FilterPills active={filter} onChange={setFilter} />
      </div>

      {/* Loading state */}
      {loading && (
        <div>
          {[...Array(5)].map((_, i) => (
            <CaseCardSkeleton key={i} index={i} />
          ))}
          <div style={{ textAlign: "center", marginTop: 28, display: "flex", alignItems: "center", justifyContent: "center", gap: 10 }}>
            <span
              style={{
                display: "inline-block",
                width: 6,
                height: 6,
                borderRadius: "50%",
                background: "var(--color-teal)",
                animation: "kpi-pulse 1.2s ease-in-out infinite",
              }}
            />
            <span className="font-mono" style={{ fontSize: 11, letterSpacing: "0.08em", color: "var(--color-slate)" }}>
              WAKING BACKEND...
            </span>
          </div>
        </div>
      )}

      {/* Error state */}
      {error && !loading && (
        <div
          className="card"
          style={{
            padding: "20px 24px",
            marginBottom: 16,
            borderLeft: "3px solid var(--color-red)",
            background: "rgba(224, 82, 82, 0.05)",
          }}
        >
          <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 6 }}>
            <span style={{ fontSize: 16 }}>?</span>
            <span className="font-mono" style={{ fontSize: 13, color: "var(--color-red)", fontWeight: 600 }}>
              Backend Unreachable
            </span>
          </div>
          <span className="font-body" style={{ fontSize: 13, color: "var(--color-slate-light)" }}>
            {error}
          </span>
          <div className="font-body" style={{ fontSize: 13, marginTop: 8, color: "var(--color-slate)" }}>
            Make sure{" "}
            <code
              style={{
                fontFamily: "var(--font-mono)",
                background: "rgba(255,255,255,0.06)",
                padding: "2px 8px",
                borderRadius: 4,
                fontSize: 12,
              }}
            >
              uvicorn app.main:app --reload
            </code>{" "}
            is running on port 8000.
          </div>
        </div>
      )}

      {/* Empty state */}
      {!loading && !error && filtered.length === 0 && (
        <div style={{ textAlign: "center", padding: "72px 0", color: "var(--color-slate)" }}>
          <div style={{ fontSize: 40, marginBottom: 16, opacity: 0.2, lineHeight: 1 }}>&#9878;</div>
          <div className="font-mono" style={{ fontSize: 13, letterSpacing: "0.08em", marginBottom: 8, color: "var(--color-slate)" }}>
            NO CASES FOUND
          </div>
          <p className="font-body" style={{ fontSize: 14, color: "var(--color-slate)", maxWidth: 320, margin: "0 auto", lineHeight: 1.6 }}>
            {filter === "all"
              ? "No cases yet. Submit a dispute to get started."
              : "No cases matching the selected filter."}
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

      {/* Live indicator */}
      {!loading && !error && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.5 }}
          style={{ display: "flex", alignItems: "center", gap: 8, marginTop: 28, justifyContent: "center" }}
        >
          <span
            style={{
              width: 6,
              height: 6,
              borderRadius: "50%",
              background: "var(--color-teal)",
              animation: "kpi-pulse 2s ease-in-out infinite",
              display: "inline-block",
            }}
          />
          <span className="font-mono" style={{ fontSize: 10, letterSpacing: "0.08em", color: "var(--color-slate)" }}>
            LIVE · refreshes every 8s
          </span>
        </motion.div>
      )}

      <style>{`
        @keyframes kpi-pulse {
          0%, 100% { opacity: 1; transform: scale(1); }
          50% { opacity: 0.3; transform: scale(0.85); }
        }
      `}</style>

      {(import.meta.env.DEV || import.meta.env.VITE_DEMO_MODE === "true") && (
      <div style={{ textAlign: "center", marginTop: 48, borderTop: "1px solid var(--color-ink-border)", paddingTop: 24 }}>
        <button
          onClick={async () => {
            if (window.confirm("Are you sure you want to delete all demo cases? This will clear the dashboard.")) {
              await api.resetDemoCases();
              window.location.reload();
            }
          }}
          className="font-mono"
          style={{
            fontSize: 11,
            background: "transparent",
            border: "1px solid var(--color-ink-border)",
            color: "var(--color-slate)",
            padding: "6px 14px",
            borderRadius: 5,
            cursor: "pointer",
            letterSpacing: "0.06em",
          }}
          onMouseEnter={(e) => {
            (e.currentTarget as HTMLButtonElement).style.borderColor = "var(--color-red)"
            ;(e.currentTarget as HTMLButtonElement).style.color = "var(--color-red)"
          }}
          onMouseLeave={(e) => {
            (e.currentTarget as HTMLButtonElement).style.borderColor = "var(--color-ink-border)"
            ;(e.currentTarget as HTMLButtonElement).style.color = "var(--color-slate)"
          }}
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
        padding: "16px 20px",
        marginBottom: 8,
        background: "rgba(255, 255, 255, 0.015)",
      }}
    >
      <div>
        <div style={{ height: 14, width: "38%", background: "var(--color-ink-border)", borderRadius: 4, marginBottom: 8, animation: "kpi-pulse 1.5s ease-in-out infinite" }} />
        <div style={{ height: 13, width: "65%", background: "var(--color-ink-border)", borderRadius: 4, marginBottom: 8, animation: "kpi-pulse 1.5s ease-in-out infinite 0.2s" }} />
        <div style={{ height: 11, width: "22%", background: "var(--color-ink-border)", borderRadius: 4, animation: "kpi-pulse 1.5s ease-in-out infinite 0.4s" }} />
      </div>
      <div>
        <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 8 }}>
          <div style={{ height: 11, width: "35%", background: "var(--color-ink-border)", borderRadius: 4 }} />
          <div style={{ height: 11, width: "35%", background: "var(--color-ink-border)", borderRadius: 4 }} />
        </div>
        <div style={{ height: 5, width: "100%", background: "var(--color-ink-border)", borderRadius: 4, marginBottom: 8, animation: "kpi-pulse 1.5s ease-in-out infinite 0.1s" }} />
        <div style={{ display: "flex", justifyContent: "flex-end" }}>
           <div style={{ height: 11, width: "25%", background: "var(--color-ink-border)", borderRadius: 4 }} />
        </div>
      </div>
      <div className="flex flex-row md:flex-col items-center md:items-end justify-between w-full md:w-auto mt-2 md:mt-0">
         <div style={{ height: 22, width: "70px", background: "var(--color-ink-border)", borderRadius: 5, animation: "kpi-pulse 1.5s ease-in-out infinite 0.3s" }} className="md:mb-3" />
         <div style={{ height: 11, width: "90px", background: "var(--color-ink-border)", borderRadius: 4 }} />
      </div>
      <div className="flex justify-end md:justify-center w-full mt-2 md:mt-0">
        <div style={{ height: 16, width: 16, background: "var(--color-ink-border)", borderRadius: 4, animation: "kpi-pulse 1.5s ease-in-out infinite 0.5s" }} />
      </div>
    </motion.div>
  )
}
