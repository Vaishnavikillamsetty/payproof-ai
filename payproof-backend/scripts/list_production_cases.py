import os
import sys

# Ensure the app module is in path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.db.models import Case

def list_cases():
    db_url = os.environ.get("DATABASE_URL")
    if not db_url:
        print("ERROR: DATABASE_URL environment variable is not set.")
        print("Please run this script with your production database URL:")
        print('$env:DATABASE_URL="<your_render_postgres_url>"')
        print("python scripts/list_production_cases.py")
        sys.exit(1)
        
    engine = create_engine(db_url)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()

    try:
        cases = db.query(Case).order_by(Case.created_at.desc()).all()
        
        print(f"\nFound {len(cases)} cases in the database:")
        print("-" * 120)
        print(f"{'ID':<38} | {'Transaction ID':<25} | {'Merchant':<15} | {'Status':<15} | {'Created At'}")
        print("-" * 120)
        
        for c in cases:
            print(f"{str(c.id):<38} | {c.transaction_id[:25]:<25} | {c.merchant_id[:15]:<15} | {c.status:<15} | {c.created_at.strftime('%Y-%m-%d %H:%M:%S')}")
            
        print("-" * 120)
    finally:
        db.close()

if __name__ == "__main__":
    list_cases()
