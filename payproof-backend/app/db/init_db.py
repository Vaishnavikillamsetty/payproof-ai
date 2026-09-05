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

            conn.execute(text("""
                UPDATE cases AS c
                SET currency = UPPER(payment.content->>'currency')
                FROM evidence AS payment
                WHERE payment.case_id = c.id
                  AND payment.evidence_type = 'payment'
                  AND COALESCE(payment.content->>'currency', '') <> ''
            """))

            # An unreviewed recommendation is not a final resolution.
            conn.execute(text("""
                UPDATE cases AS c
                SET status = CASE LOWER(c.ai_recommendation)
                    WHEN 'escalate' THEN 'escalated'
                    WHEN 'request_more_evidence' THEN 'evidence_requested'
                    ELSE 'pending_review'
                END
                WHERE c.ai_recommendation IS NOT NULL
                  AND NOT EXISTS (
                    SELECT 1 FROM audit_log AS a
                    WHERE a.case_id = c.id AND a.step = 'human_review_decision'
                  )
            """))

            # Backfill a high-priority authentication contradiction for legacy
            # cases. Unreviewed cases are routed to escalation; reviewed cases
            # retain their recorded human workflow decision.
            conn.execute(text("""
                UPDATE cases AS c
                SET contradiction_detected = TRUE,
                    ai_recommendation = CASE
                        WHEN NOT EXISTS (
                            SELECT 1 FROM audit_log AS a
                            WHERE a.case_id = c.id AND a.step = 'human_review_decision'
                        ) THEN 'ESCALATE'
                        ELSE c.ai_recommendation
                    END,
                    status = CASE
                        WHEN NOT EXISTS (
                            SELECT 1 FROM audit_log AS a
                            WHERE a.case_id = c.id AND a.step = 'human_review_decision'
                        ) THEN 'escalated'
                        ELSE c.status
                    END
                WHERE EXISTS (
                    SELECT 1 FROM evidence AS verified
                    WHERE verified.case_id = c.id
                      AND verified.evidence_type = 'otp'
                      AND verified.content->>'verified' = 'true'
                )
                  AND EXISTS (
                    SELECT 1 FROM evidence AS unverified
                    WHERE unverified.case_id = c.id
                      AND unverified.evidence_type = 'otp'
                      AND unverified.content->>'verified' = 'false'
                )
            """))
                
    except Exception as e:
        logger.error(f"Error during schema migration: {e}")
        
    # 3. Demo Initialization (Hackathon only)
    from app.config import settings
    if settings.mock_verifier:
        logger.info("Demo mode enabled. Checking if demo records need to be seeded.")
        try:
            with engine.begin() as conn:
                result = conn.execute(text("SELECT COUNT(*) FROM ext_payment_gateway"))
                count = result.scalar()
            if count == 0:
                logger.info("Demo tables empty, seeding mock evidence data...")
                import sys
                import os
                sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))
                try:
                    from data.seed_evidence_db import seed_db
                    seed_db()
                    logger.info("Demo evidence data seeded successfully.")
                except ImportError as e:
                    logger.warning(f"Could not import seed_evidence_db: {e}")
            else:
                logger.info(f"Demo tables already contain {count} records, skipping seed.")
        except Exception as e:
            logger.warning(f"Could not check/seed demo tables (non-fatal): {e}")

    logger.info("Database initialization complete.")

if __name__ == "__main__":
    init_db()
