import { useState } from 'react'
import NavBar from './components/NavBar'
import Dashboard from './pages/Dashboard'

/**
 * App shell — minimal routing without a router library.
 * Phase 4 has one page: Dashboard.
 * Phase 5 will add CaseDetail; we'll add a `view` state for that.
 */
export default function App() {
  const [selectedCaseId, setSelectedCaseId] = useState<string | null>(null)

  // Phase 5 hook — selecting a case will navigate to detail view
  const handleSelectCase = (id: string) => {
    setSelectedCaseId(id)
    // TODO Phase 5: render <CaseDetail id={id} />
    console.log('Selected case:', id)
  }

  // Suppress unused-var lint for now (used in Phase 5)
  void selectedCaseId

  return (
    <div style={{ minHeight: '100svh', background: 'var(--color-ink)' }}>
      <NavBar>
        {/* New Case button placeholder — wired up in Phase 5 */}
        <button
          type="button"
          id="btn-new-case"
          style={{
            padding: '7px 16px',
            borderRadius: 5,
            border: '1px solid var(--color-teal)',
            background: 'rgba(63, 167, 150, 0.12)',
            color: 'var(--color-teal)',
            fontFamily: 'var(--font-mono)',
            fontSize: 12,
            fontWeight: 600,
            letterSpacing: '0.06em',
            textTransform: 'uppercase',
            cursor: 'pointer',
            transition: 'background 0.15s ease',
          }}
          onMouseEnter={(e) =>
            ((e.currentTarget as HTMLButtonElement).style.background =
              'rgba(63, 167, 150, 0.22)')
          }
          onMouseLeave={(e) =>
            ((e.currentTarget as HTMLButtonElement).style.background =
              'rgba(63, 167, 150, 0.12)')
          }
        >
          + New Case
        </button>
      </NavBar>

      <Dashboard onSelectCase={handleSelectCase} />
    </div>
  )
}
