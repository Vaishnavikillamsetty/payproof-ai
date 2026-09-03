import pathlib
p = pathlib.Path('src/pages/Dashboard.tsx')
text = p.read_text(encoding='utf-8')

old_btn = """<div style={{ textAlign: 'center', marginTop: 40, borderTop: '1px solid var(--color-ink-border)', paddingTop: 24 }}>"""
new_btn = """{(import.meta.env.DEV || import.meta.env.VITE_DEMO_MODE === 'true') && (
      <div style={{ textAlign: 'center', marginTop: 40, borderTop: '1px solid var(--color-ink-border)', paddingTop: 24 }}>"""

if "(import.meta.env.DEV" not in text:
    text = text.replace(old_btn, new_btn)
    text = text.replace("""RESET DEMO CASES
        </button>
      </div>""", """RESET DEMO CASES
        </button>
      </div>
      )}""")
    p.write_text(text, encoding='utf-8')
print("Successfully modified Dashboard.tsx")
