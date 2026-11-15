import type { ReactNode } from 'react'

interface Props {
  children: ReactNode
  onNavMetrics?: () => void
}

/**
 * Top navigation bar — sticky, always visible.
 * IBM Plex Mono for the wordmark; Inter for sub-label.
 */
export default function NavBar({ children, onNavMetrics }: Props) {
  return (
    <nav
      style={{
        background: 'var(--color-ink-light)',
        borderBottom: '1px solid var(--color-ink-border)',
        position: 'sticky',
        top: 0,
        zIndex: 50,
        boxShadow: '0 1px 0 rgba(0,0,0,0.3), 0 2px 8px rgba(0,0,0,0.2)',
      }}
    >
      <div
        style={{
          maxWidth: 1200,
          margin: '0 auto',
          padding: '0 24px',
          height: 64,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
        }}
      >
        {/* Wordmark */}
        <div style={{ display: 'flex', alignItems: 'center', gap: 14 }}>
          {/* Brand dot accent */}
          <div
            style={{
              width: 8,
              height: 8,
              borderRadius: '50%',
              background: 'var(--color-teal)',
              boxShadow: '0 0 8px rgba(54, 198, 174, 0.5)',
              flexShrink: 0,
            }}
          />
          <div style={{ display: 'flex', alignItems: 'baseline', gap: 8 }}>
            <span
              className="font-mono"
              style={{
                fontSize: 15,
                fontWeight: 700,
                letterSpacing: '0.1em',
                color: 'var(--color-white)',
                textTransform: 'uppercase',
              }}
            >
              PayProof{' '}
              <span style={{ color: 'var(--color-teal)' }}>AI</span>
            </span>
            <span
              className="font-body hidden sm:inline"
              style={{
                fontSize: 12,
                color: 'var(--color-slate)',
                letterSpacing: '0.03em',
              }}
            >
              Evidence-First Dispute Defense
            </span>
          </div>
        </div>

        {/* Right side nav */}
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          {onNavMetrics && (
            <NavTextButton onClick={onNavMetrics} label="Metrics" />
          )}
          {/* Divider */}
          {onNavMetrics && (
            <div
              style={{
                width: 1,
                height: 20,
                background: 'var(--color-ink-border)',
                margin: '0 4px',
              }}
            />
          )}
          {children}
        </div>
      </div>
    </nav>
  )
}

function NavTextButton({ onClick, label }: { onClick: () => void; label: string }) {
  return (
    <button
      onClick={onClick}
      className="font-mono"
      style={{
        background: 'transparent',
        border: 'none',
        cursor: 'pointer',
        fontSize: 12,
        letterSpacing: '0.07em',
        textTransform: 'uppercase',
        fontWeight: 600,
        color: 'var(--color-slate)',
        padding: '6px 12px',
        borderRadius: 6,
        transition: 'color 0.15s ease, background 0.15s ease',
      }}
      onMouseEnter={(e) => {
        (e.currentTarget as HTMLButtonElement).style.color = 'var(--color-white)'
        ;(e.currentTarget as HTMLButtonElement).style.background = 'var(--color-ink-mid)'
      }}
      onMouseLeave={(e) => {
        (e.currentTarget as HTMLButtonElement).style.color = 'var(--color-slate)'
        ;(e.currentTarget as HTMLButtonElement).style.background = 'transparent'
      }}
    >
      {label}
    </button>
  )
}
