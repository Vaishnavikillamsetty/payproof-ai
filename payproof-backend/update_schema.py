import pathlib

# Update models.py
p = pathlib.Path('app/db/models.py')
text = p.read_text(encoding='utf-8')
old_status = 'status = Column(String, nullable=False, default="new", index=True)'
new_status = """status = Column(String, nullable=False, default="new", index=True)
    ai_recommendation = Column(String, nullable=True)
    final_action = Column(String, nullable=True)
    contradiction_detected = Column(Boolean, default=False)
    currency = Column(String, nullable=False, default="USD")"""
if 'ai_recommendation =' not in text:
    text = text.replace(old_status, new_status)
    p.write_text(text, encoding='utf-8')

# Update schemas.py
p = pathlib.Path('app/schemas.py')
text = p.read_text(encoding='utf-8')

if 'ai_recommendation: Optional[str] = None' not in text:
    text = text.replace('status: str', 'status: str\n    ai_recommendation: Optional[str] = None\n    final_action: Optional[str] = None\n    contradiction_detected: bool = False\n    currency: str = "USD"')
    # make sure typing Optional is imported
    if 'Optional' not in text:
        text = text.replace('from typing import List, Dict, Any', 'from typing import List, Dict, Any, Optional')
    p.write_text(text, encoding='utf-8')
