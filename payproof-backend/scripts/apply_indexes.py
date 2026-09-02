import os
import sys

# Ensure the app module is in path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from sqlalchemy import text
from app.db.session import engine

def apply_indexes():
    """
    Applies indexes to an existing database. 
    SQLAlchemy's create_all() does not modify existing tables to add indexes,
    so we issue the CREATE INDEX IF NOT EXISTS commands directly.
    """
    print("Applying performance indexes to the database...")
    
    index_statements = [
        "CREATE INDEX IF NOT EXISTS ix_cases_created_at ON cases (created_at);",
        "CREATE INDEX IF NOT EXISTS ix_cases_status ON cases (status);",
        "CREATE INDEX IF NOT EXISTS ix_cases_transaction_id ON cases (transaction_id);",
        "CREATE INDEX IF NOT EXISTS ix_evidence_case_id ON evidence (case_id);",
        "CREATE INDEX IF NOT EXISTS ix_claims_case_id ON claims (case_id);",
        "CREATE INDEX IF NOT EXISTS ix_rule_flags_case_id ON rule_flags (case_id);",
        "CREATE INDEX IF NOT EXISTS ix_audit_log_case_id ON audit_log (case_id);"
    ]

    try:
        with engine.begin() as conn:
            for statement in index_statements:
                print(f"Executing: {statement}")
                conn.execute(text(statement))
        print("\n[OK] All indexes applied successfully.")
    except Exception as e:
        print(f"\n[ERROR] Failed to apply indexes: {e}")

if __name__ == "__main__":
    apply_indexes()
