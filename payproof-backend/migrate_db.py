import sys
sys.path.insert(0, '.')
from app.db.session import engine
from sqlalchemy import text

with engine.begin() as conn:
    try:
        conn.execute(text("ALTER TABLE cases ADD COLUMN IF NOT EXISTS ai_recommendation VARCHAR"))
        conn.execute(text("ALTER TABLE cases ADD COLUMN IF NOT EXISTS final_action VARCHAR"))
        conn.execute(text("ALTER TABLE cases ADD COLUMN IF NOT EXISTS contradiction_detected BOOLEAN DEFAULT false"))
        conn.execute(text("ALTER TABLE cases ADD COLUMN IF NOT EXISTS currency VARCHAR DEFAULT 'USD'"))
        # Update existing cases
        conn.execute(text("UPDATE cases SET ai_recommendation = status, final_action = status, currency = 'USD'"))
        print("Database schema migrated successfully.")
    except Exception as e:
        print(f"Error migrating: {e}")
