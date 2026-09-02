import os
import sys

# Ensure the app module is in path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from sqlalchemy import text
from app.db.session import engine
from app.db.models import Case, Evidence, Claim, RuleFlag, AuditLog

def clean_production_cases():
    db_url = os.environ.get("DATABASE_URL")
    if not db_url:
        print("ERROR: DATABASE_URL environment variable is not set.")
        sys.exit(1)
        
    print("WARNING: This script will delete ALL submitted cases and their history.")
    print("It will NOT touch the seeded demo data in ext_* tables.")
    
    confirm = input("Type 'DELETE' to confirm: ")
    if confirm != "DELETE":
        print("Aborting.")
        sys.exit(0)

    try:
        with engine.begin() as conn:
            # Delete child tables first to avoid foreign key constraint violations
            print("Deleting from audit_log...")
            conn.execute(text("DELETE FROM audit_log;"))
            
            print("Deleting from rule_flags...")
            conn.execute(text("DELETE FROM rule_flags;"))
            
            print("Deleting from claims...")
            conn.execute(text("DELETE FROM claims;"))
            
            print("Deleting from evidence...")
            conn.execute(text("DELETE FROM evidence;"))
            
            # Finally delete parent table
            print("Deleting from cases...")
            conn.execute(text("DELETE FROM cases;"))
            
        print("\n[OK] All case history cleared successfully.")
        
        # Verify counts
        with engine.begin() as conn:
            case_count = conn.execute(text("SELECT COUNT(*) FROM cases;")).scalar()
            ev_count = conn.execute(text("SELECT COUNT(*) FROM evidence;")).scalar()
            claim_count = conn.execute(text("SELECT COUNT(*) FROM claims;")).scalar()
            rule_count = conn.execute(text("SELECT COUNT(*) FROM rule_flags;")).scalar()
            audit_count = conn.execute(text("SELECT COUNT(*) FROM audit_log;")).scalar()
            
            print("\nVerification:")
            print(f"cases: {case_count}")
            print(f"evidence: {ev_count}")
            print(f"claims: {claim_count}")
            print(f"rule_flags: {rule_count}")
            print(f"audit_log: {audit_count}")
            
    except Exception as e:
        print(f"\n[ERROR] Failed to clean database: {e}")

if __name__ == "__main__":
    clean_production_cases()
