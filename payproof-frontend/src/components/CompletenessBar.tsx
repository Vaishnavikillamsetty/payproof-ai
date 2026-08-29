interface Props {
  /** 0–100 */
  score: number | null
  /** Show a text label beside the bar */
  showLabel?: boolean
}

/**
 * Slim horizontal progress bar showing the evidence completeness score.
 * Color shifts: teal ≥70, amber 40-69, red <40.
 */
export default function CompletenessBar({ score, showLabel = true }: Props) {
  if (score === null) {
    return (
      <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
        <div
          style={{
            flex: 1,
            height: 4,
            borderRadius: 2,
            background: 'var(--color-ink-border)',
          }}
        />
        {showLabel && (
          <span
            className="font-mono text-slate"
            style={{ fontSize: 12, minWidth: 32, textAlign: 'right' }}
          >
            —
          </span>
        )}
      </div>
    )
  }

  const pct = Math.max(0, Math.min(100, score))
  const color =
    pct >= 70
      ? 'var(--color-teal)'
      : pct >= 40
        ? 'var(--color-amber)'
        : 'var(--color-red)'

  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
      <div
        style={{
          flex: 1,
          height: 4,
          borderRadius: 2,
          background: 'var(--color-ink-border)',
          overflow: 'hidden',
        }}
        role="progressbar"
        aria-valuenow={pct}
        aria-valuemin={0}
        aria-valuemax={100}
        aria-label={`Evidence completeness ${pct}%`}
      >
        <div
          style={{
            width: `${pct}%`,
            height: '100%',
            background: color,
            borderRadius: 2,
            transition: 'width 0.4s ease',
          }}
        />
      </div>
      {showLabel && (
        <span
          className="font-mono"
          style={{ fontSize: 12, color, minWidth: 32, textAlign: 'right' }}
        >
          {pct}%
        </span>
      )}
    </div>
  )
}
