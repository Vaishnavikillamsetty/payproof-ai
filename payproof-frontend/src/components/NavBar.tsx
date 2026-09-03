import type { ReactNode } from 'react'

interface Props {
  children: ReactNode
  onNavMetrics?: () => void
}

/**
 * Top navigation bar ??? fixed, always visible.
 * IBM Plex Mono for the wordmark; Inter for sub-label.
 */
export default function NavBar({ children, onNavMetrics }: Props) {
  return (
    <nav
      style={{
        background: 'var(--color-ink)',
        borderBottom: '1px solid var(--color-ink-border)',
        position: 'sticky',
        top: 0,
        zIndex: 50,
      }}
    >
      <div
        style={{
          maxWidth: 1200,
          margin: '0 auto',
          padding: '0 24px',
          height: 60,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
        }}
      >
        {/* Wordmark */}
        <div style={{ display: 'flex', alignItems: 'baseline', gap: 12 }}>
          <span
            className="font-mono"
            style={{
              fontSize: 16,
              fontWeight: 700,
              letterSpacing: '0.12em',
              color: 'var(--color-white)',
              textTransform: 'uppercase',
            }}
          >
            PayProof AI
          </span>
          <span
            className="font-body text-slate hidden sm:inline"
            style={{ fontSize: 12, letterSpacing: '0.04em' }}
          >
            Evidence-First Dispute Defense
          </span>
        </div>

        {/* Slot for right-side content */}
        <div style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
          {onNavMetrics && (
            <button
              onClick={onNavMetrics}
              className="font-mono text-slate hover:text-white transition-colors"
              style={{
                background: 'transparent',
                border: 'none',
                cursor: 'pointer',
                fontSize: 12,
                letterSpacing: '0.06em',
                textTransform: 'uppercase',
                fontWeight: 600,
              }}
            >
              Metrics
            </button>
          )}
          {children}
        </div>
      </div>
    </nav>
  )
}
