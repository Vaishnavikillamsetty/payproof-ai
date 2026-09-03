import pathlib, sys

root = pathlib.Path('src')
broken = []
for f in root.rglob('*.tsx'):
    try:
        text = f.read_text(encoding='utf-8')
    except Exception:
        text = f.read_bytes().decode('latin-1', errors='replace')
    for i, line in enumerate(text.splitlines(), 1):
        if '\ufffd' in line or '\u0097' in line or '\u0085' in line or '?' in line:
            broken.append(f"{f}:{i}: {line.strip()[:120]}")
for f in root.rglob('*.ts'):
    try:
        text = f.read_text(encoding='utf-8')
    except Exception:
        text = f.read_bytes().decode('latin-1', errors='replace')
    for i, line in enumerate(text.splitlines(), 1):
        if '\ufffd' in line or '\u0097' in line or '\u0085' in line or '?' in line:
            broken.append(f"{f}:{i}: {line.strip()[:120]}")

print(f"Found {len(broken)} suspicious lines:")
for b in broken[:50]:
    print(' ', b)
