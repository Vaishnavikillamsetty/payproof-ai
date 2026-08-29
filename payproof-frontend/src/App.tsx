import { useState } from 'react'
import NavBar from './components/NavBar'
import Dashboard from './pages/Dashboard'
import CaseDetail from './pages/CaseDetail'
import NewCase from './pages/NewCase'

type ViewState = 
  | { type: 'dashboard' }
  | { type: 'case_detail', id: string }
  | { type: 'new_case' }

/**
 * App shell — minimal routing without a router library.
 */
export default function App() {
  const [view, setView] = useState<ViewState>({ type: 'dashboard' })

  let navButtonText = '+ New Case'
  let navButtonAction = () => setView({ type: 'new_case' })
  
  if (view.type !== 'dashboard') {
    navButtonText = 'Dashboard'
    navButtonAction = () => setView({ type: 'dashboard' })
  }

  return (
    <div style={{ minHeight: '100svh', background: 'var(--color-ink)' }}>
      <NavBar>
        <button
          type="button"
          id="btn-new-case"
          onClick={navButtonAction}
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
          {navButtonText}
        </button>
      </NavBar>

      {view.type === 'dashboard' && (
        <Dashboard onSelectCase={(id) => setView({ type: 'case_detail', id })} />
      )}
      {view.type === 'case_detail' && (
        <CaseDetail caseId={view.id} onBack={() => setView({ type: 'dashboard' })} />
      )}
      {view.type === 'new_case' && (
        <NewCase 
          onCancel={() => setView({ type: 'dashboard' })} 
          onSuccess={(id) => setView({ type: 'case_detail', id })}
        />
      )}
    </div>
  )
}
