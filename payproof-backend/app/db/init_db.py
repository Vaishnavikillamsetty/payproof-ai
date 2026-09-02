import logging
from sqlalchemy import text
from app.db.session import engine
from app.db import models

logger = logging.getLogger(__name__)

def init_db():
    logger.info("Initializing database schema...")
    
    # 1. Create all tables for a completely fresh database
    # (Safe to run, won't recreate existing tables)
    models.Base.metadata.create_all(bind=engine)
    
    # 2. Hackathon-style migrations for existing databases
    # We apply specific schema changes manually if they are missing
    try:
        with engine.begin() as conn:
            # Check if external_dispute_id exists in cases
            result = conn.execute(text(
                "SELECT column_name FROM information_schema.columns "
                "WHERE table_name='cases' AND column_name='external_dispute_id';"
            ))
            if result.rowcount == 0:
                logger.info("Running hackathon migration: adding external_dispute_id to cases")
                conn.execute(text("ALTER TABLE cases ADD COLUMN external_dispute_id VARCHAR"))
                conn.execute(text("ALTER TABLE cases ADD CONSTRAINT uq_cases_external_dispute_id UNIQUE (external_dispute_id)"))
                conn.execute(text("CREATE INDEX ix_cases_external_dispute_id ON cases (external_dispute_id)"))
    except Exception as e:
        logger.error(f"Error during schema migration: {e}")
        # Not throwing to allow startup to attempt continuing if it's a minor error,
        # but in a real app this would crash startup.
        
    logger.info("Database initialization complete.")

if __name__ == "__main__":
    init_db()
