import type { CaseStatus } from '../types'

type FilterValue = CaseStatus | 'all'

interface Props {
  active: FilterValue
  onChange: (v: FilterValue) => void
}

const FILTERS: { label: string; value: FilterValue }[] = [
  { label: 'All', value: 'all' },
  { label: 'Contest / Accept', value: 'strong_case' },
  { label: 'Escalated / Review', value: 'human_review' },
  { label: 'More Evidence', value: 'request_more_evidence' },
  { label: 'Investigating', value: 'investigating' },
  { label: 'Resolved / Closed', value: 'closed' },
]

/**
 * Filter pill row — lets the user narrow the case list by status.
 * Visual-only update: improved hover, spacing, border radius.
 * All filter logic and onChange handlers are preserved exactly.
 */
export default function FilterPills({ active, onChange }: Props) {
  return (
    <div
      style={{
        display: 'flex',
        gap: 6,
        flexWrap: 'wrap',
      }}
      role="group"
      aria-label="Filter cases by status"
    >
      {FILTERS.map((f) => {
        const isActive = f.value === active
        return (
          <button
            id={`filter-${f.value}`}
            key={f.value}
            type="button"
            onClick={() => onChange(f.value)}
            style={{
              padding: '6px 14px',
              borderRadius: 6,
              border: isActive
                ? '1px solid var(--color-teal)'
                : '1px solid var(--color-ink-border)',
              background: isActive
                ? 'rgba(54, 198, 174, 0.14)'
                : 'var(--color-ink-mid)',
              color: isActive
                ? 'var(--color-teal)'
                : 'var(--color-slate-light)',
              fontFamily: 'var(--font-mono)',
              fontSize: 11,
              fontWeight: 600,
              letterSpacing: '0.06em',
              textTransform: 'uppercase' as const,
              cursor: 'pointer',
              transition: 'all 0.15s ease',
              whiteSpace: 'nowrap',
            }}
            onMouseEnter={(e) => {
              if (!isActive) {
                const btn = e.currentTarget as HTMLButtonElement
                btn.style.borderColor = 'var(--color-slate)'
                btn.style.color = 'var(--color-white)'
              }
            }}
            onMouseLeave={(e) => {
              if (!isActive) {
                const btn = e.currentTarget as HTMLButtonElement
                btn.style.borderColor = 'var(--color-ink-border)'
                btn.style.color = 'var(--color-slate-light)'
              }
            }}
          >
            {f.label}
          </button>
        )
      })}
    </div>
  )
}
