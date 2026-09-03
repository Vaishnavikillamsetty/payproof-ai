import pathlib

def fix_completeness_bar():
    p = pathlib.Path('src/components/CompletenessBar.tsx')
    text = p.read_text(encoding='utf-8')
    text = text.replace('/** 0???100 */', '/** 0-100 */')
    text = text.replace('???\n          </span>', '--\n          </span>')
    text = text.replace('<span style={{ color: \'var(--color-teal)\' }}>???</span>', '<span style={{ color: \'var(--color-teal)\' }}>✓</span>')
    text = text.replace('<span style={{ color: \'var(--color-red)\' }}>???</span>', '<span style={{ color: \'var(--color-red)\' }}>✗</span>')
    p.write_text(text, encoding='utf-8')

def fix_case_card():
    p = pathlib.Path('src/components/CaseCard.tsx')
    text = p.read_text(encoding='utf-8')
    text = text.replace('???', '--')
    text = text.replace('aria-label={`Case ${c.transaction_id} --', 'aria-label={`Case ${c.transaction_id} -')
    text = text.replace('{/* ------ Col 1: Identity ------ */}', '{/* Col 1: Identity */}')
    text = text.replace('{/* ------ Col 2: Completeness ------ */}', '{/* Col 2: Completeness */}')
    text = text.replace('{/* ------ Col 3: Lifecycle status ------ */}', '{/* Col 3: Lifecycle status */}')
    text = text.replace('{/* ------ Col 4: AI Recommendation ------ */}', '{/* Col 4: AI Recommendation */}')
    text = text.replace('{/* ------ Col 5: Chevron ------ */}', '{/* Col 5: Chevron */}')
    p.write_text(text, encoding='utf-8')

def fix_dashboard():
    p = pathlib.Path('src/pages/Dashboard.tsx')
    text = p.read_text(encoding='utf-8')
    text = text.replace('??? Could not reach the backend:', 'Error: Could not reach the backend:')
    text = text.replace('???\n          </div>', '(empty)\n          </div>')
    text = text.replace('LIVE ?? refreshes every 8s', 'LIVE refreshes every 8s')
    text = text.replace('Dashboard ??? the case list page.', 'Dashboard - the case list page.')
    text = text.replace('Live indicator ??? shows when polling is active', 'Live indicator shows when polling is active')
    
    # Add RESET DEMO CASES button to dashboard
    btn_html = """
      <div style={{ textAlign: 'center', marginTop: 40, borderTop: '1px solid var(--color-ink-border)', paddingTop: 24 }}>
        <button 
          onClick={async () => {
            if (window.confirm("Are you sure you want to delete all demo cases? This will clear the dashboard.")) {
              await api.resetDemoCases();
              window.location.reload();
            }
          }}
          className="font-mono text-slate" 
          style={{ fontSize: 11, background: 'transparent', border: '1px solid var(--color-ink-border)', padding: '6px 12px', borderRadius: 4, cursor: 'pointer' }}
        >
          RESET DEMO CASES
        </button>
      </div>
"""
    if "RESET DEMO CASES" not in text:
        text = text.replace('    </main>', f'{btn_html}    </main>')
        
    p.write_text(text, encoding='utf-8')

def fix_metrics():
    p = pathlib.Path('src/pages/Metrics.tsx')
    text = p.read_text(encoding='utf-8')
    text = text.replace('???</div>', '◒</div>')
    text = text.replace('efficiency ??? {cm.false_negatives}', 'efficiency — {cm.false_negatives}')
    text = text.replace('* Benchmark metrics ??? computed', '* Benchmark metrics are computed')
    text = text.replace('Performance Metrics\n        </p>\n      </div>', 'Performance Metrics\n        </p>\n        <p className="font-body text-amber" style={{ fontSize: 13, marginTop: 12, padding: "8px 12px", background: "rgba(224, 163, 57, 0.1)", borderRadius: 4, display: "inline-block" }}>Note: Metrics are computed from a fixed synthetic evaluation dataset and are NOT derived from live submitted cases.</p>\n      </div>')
    p.write_text(text, encoding='utf-8')

def fix_agent_activity():
    p = pathlib.Path('src/components/AgentActivity.tsx')
    text = p.read_text(encoding='utf-8')
    # Use exact string replacements based on the grep
    text = text.replace('<span style={{ fontSize: 16 }}>??</span>', '<span style={{ fontSize: 16 }}>🤖</span>')
    text = text.replace('<span style={{ color: \'var(--color-amber)\' }}>? DETERMINISTIC FALLBACK</span>', '<span style={{ color: \'var(--color-amber)\' }}>⚠ DETERMINISTIC FALLBACK</span>')
    text = text.replace('<span style={{ color: \'var(--color-teal)\' }}>?</span>', '<span style={{ color: \'var(--color-teal)\' }}>✓</span>')
    text = text.replace('? Completed', '✓ Completed')
    p.write_text(text, encoding='utf-8')

def fix_api():
    p = pathlib.Path('src/api.ts')
    text = p.read_text(encoding='utf-8')
    if 'resetDemoCases' not in text:
        text = text.replace('  reviewCase: async (id: string, req: { action: string, notes: string }) => {', 
'''  resetDemoCases: async () => {
    const res = await fetch(`${API_URL}/cases/demo-reset`, { method: 'DELETE' })
    if (!res.ok) throw new Error('Failed to reset demo cases')
    return res.json()
  },
  reviewCase: async (id: string, req: { action: string, notes: string }) => {''')
        p.write_text(text, encoding='utf-8')

try:
    fix_completeness_bar()
    fix_case_card()
    fix_dashboard()
    fix_metrics()
    fix_agent_activity()
    fix_api()
    print("Frontend encodings fixed successfully.")
except Exception as e:
    print(f"Error: {e}")
