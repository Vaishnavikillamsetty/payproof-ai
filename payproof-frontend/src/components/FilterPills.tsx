import type { CaseStatus } from '../types'

type FilterValue = CaseStatus | 'all'

interface Props {
  active: FilterValue
  onChange: (v: FilterValue) => void
}

const FILTERS: { label: string; value: FilterValue }[] = [
  { label: 'All', value: 'all' },
  { label: 'Strong Case', value: 'strong_case' },
  { label: 'Weak Case', value: 'weak_case' },
  { label: 'Human Review', value: 'human_review' },
  { label: 'Investigating', value: 'investigating' },
  { label: 'New', value: 'new' },
]

/**
 * Filter pill row — lets the user narrow the case list by status.
 */
export default function FilterPills({ active, onChange }: Props) {
  return (
    <div
      style={{
        display: 'flex',
        gap: 8,
        flexWrap: 'wrap',
        marginBottom: 20,
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
              padding: '5px 14px',
              borderRadius: 4,
              border: isActive
                ? '1px solid var(--color-teal)'
                : '1px solid var(--color-ink-border)',
              background: isActive
                ? 'rgba(63, 167, 150, 0.15)'
                : 'transparent',
              color: isActive
                ? 'var(--color-teal)'
                : 'var(--color-slate)',
              fontFamily: 'var(--font-mono)',
              fontSize: 12,
              fontWeight: 600,
              letterSpacing: '0.05em',
              textTransform: 'uppercase' as const,
              cursor: 'pointer',
              transition: 'all 0.15s ease',
            }}
          >
            {f.label}
          </button>
        )
      })}
    </div>
  )
}
