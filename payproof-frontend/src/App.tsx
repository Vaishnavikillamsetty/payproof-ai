import { useState } from 'react'
import { warmBackend } from './api'
import NavBar from './components/NavBar'
import Dashboard from './pages/Dashboard'
import CaseDetail from './pages/CaseDetail'
import NewCase from './pages/NewCase'
import Metrics from './pages/Metrics'

// Fire a lightweight /health ping as soon as JS loads to wake the backend
// from Render free-tier cold sleep before the user triggers a data fetch.
warmBackend()

type ViewState = 
  | { type: 'dashboard' }
  | { type: 'case_detail', id: string }
  | { type: 'new_case' }
  | { type: 'metrics' }

/**
 * App shell ??? minimal routing without a router library.
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
      <NavBar onNavMetrics={() => setView({ type: 'metrics' })}>
        <button
          type="button"
          id="btn-new-case"
          onClick={navButtonAction}
          style={
            view.type === 'dashboard'
              ? {
                  padding: '8px 18px',
                  borderRadius: 6,
                  border: 'none',
                  background: 'var(--color-teal)',
                  color: '#0B1120',
                  fontFamily: 'var(--font-mono)',
                  fontSize: 12,
                  fontWeight: 700,
                  letterSpacing: '0.07em',
                  textTransform: 'uppercase',
                  cursor: 'pointer',
                  transition: 'background 0.15s ease, transform 0.1s ease',
                  boxShadow: '0 2px 8px rgba(54,198,174,0.3)',
                }
              : {
                  padding: '8px 18px',
                  borderRadius: 6,
                  border: '1px solid var(--color-ink-border)',
                  background: 'var(--color-ink-mid)',
                  color: 'var(--color-slate-light)',
                  fontFamily: 'var(--font-mono)',
                  fontSize: 12,
                  fontWeight: 600,
                  letterSpacing: '0.07em',
                  textTransform: 'uppercase',
                  cursor: 'pointer',
                  transition: 'background 0.15s ease',
                }
          }
          onMouseEnter={(e) => {
            const btn = e.currentTarget as HTMLButtonElement
            if (view.type === 'dashboard') {
              btn.style.background = 'var(--color-teal-dim)'
            } else {
              btn.style.background = '#1E2D45'
              btn.style.color = 'var(--color-white)'
            }
          }}
          onMouseLeave={(e) => {
            const btn = e.currentTarget as HTMLButtonElement
            if (view.type === 'dashboard') {
              btn.style.background = 'var(--color-teal)'
            } else {
              btn.style.background = 'var(--color-ink-mid)'
              btn.style.color = 'var(--color-slate-light)'
            }
          }}
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
      {view.type === 'metrics' && (
        <Metrics />
      )}
    </div>
  )
}
