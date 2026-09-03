import { motion, useReducedMotion } from 'framer-motion'
import type { CaseStatus } from '../types'

interface Props {
  status: CaseStatus
  confidence: number | null
  size?: 'small' | 'large'
}

/**
 * Signature rotated confidence "stamp".
 * Animates a single "stamp down" (scale + rotate) on mount.
 */
export default function VerdictStamp({ status, confidence, size = 'large' }: Props) {
  const shouldReduceMotion = useReducedMotion()

  let text = 'INVESTIGATING'
  let color = 'var(--color-slate)'

  if (status === 'strong_case') {
    text = confidence !== null ? `VERIFIED ?? ${Math.round(confidence * 100)}%` : 'VERIFIED'
    color = 'var(--color-teal)'
  } else if (status === 'human_review') {
    text = 'HUMAN REVIEW'
    color = 'var(--color-red)'
  } else if (status === 'weak_case') {
    text = 'INSUFFICIENT EVIDENCE'
    color = 'var(--color-amber)'
  } else if (status === 'new') {
    text = 'NEW CASE'
  }

  // Stamp animation: scale down and rotate slightly
  // Large stamp rotates more visibly than small stamp
  const rotation = size === 'large' ? -4 : -2
  const initial = shouldReduceMotion ? { opacity: 0 } : { opacity: 0, scale: 1.8, rotate: 0 }
  const animate = shouldReduceMotion
    ? { opacity: 1 }
    : { opacity: 1, scale: 1, rotate: rotation }

  const fontSize = size === 'large' ? 18 : 11
  const padding = size === 'large' ? '6px 16px' : '2px 8px'
  const borderWidth = size === 'large' ? 4 : 2

  return (
    <motion.div
      initial={initial}
      animate={animate}
      transition={{ type: 'spring', stiffness: 250, damping: 20 }}
      style={{
        display: 'inline-block',
        border: `${borderWidth}px double ${color}`, // Double border simulates a bit of texture/stamp feel
        borderRadius: 4,
        padding: padding,
        color: color,
        fontFamily: 'var(--font-mono)',
        fontSize: fontSize,
        fontWeight: 700,
        letterSpacing: '0.05em',
        textTransform: 'uppercase',
        opacity: 0.9,
        whiteSpace: 'nowrap',
      }}
    >
      {text}
    </motion.div>
  )
}
