import pathlib
p = pathlib.Path('src/api.ts')
text = p.read_text(encoding='utf-8')
if 'resetDemoCases' not in text:
    old_str = "reviewCase: (id: string, action: string, notes: string): Promise<CaseDetail> =>"
    new_str = """resetDemoCases: async (): Promise<any> =>
    request('/cases/demo-reset', { method: 'DELETE' }),

  reviewCase: (id: string, action: string, notes: string): Promise<CaseDetail> =>"""
    text = text.replace(old_str, new_str)
    p.write_text(text, encoding='utf-8')
