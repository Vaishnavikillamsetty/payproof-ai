import logging
from sqlalchemy import text
from app.db.session import engine
from app.db import models

logger = logging.getLogger(__name__)

def init_db():
    logger.info("Initializing database schema...")
    
    # 1. Create all tables for a completely fresh database (safe, idempotent)
    models.Base.metadata.create_all(bind=engine)
    
    # 2. Migrations for existing databases (idempotent, non-destructive)
    try:
        with engine.begin() as conn:
            # Check if external_dispute_id exists in cases
            result = conn.execute(text(
                "SELECT column_name FROM information_schema.columns "
                "WHERE table_name='cases' AND column_name='external_dispute_id';"
            ))
            if result.rowcount == 0:
                logger.info("Running migration: adding external_dispute_id to cases")
                conn.execute(text("ALTER TABLE cases ADD COLUMN IF NOT EXISTS external_dispute_id VARCHAR"))
                conn.execute(text("CREATE UNIQUE INDEX IF NOT EXISTS uq_cases_external_dispute_id ON cases (external_dispute_id)"))

            # Add human review and evidence tracking columns to cases
            logger.info("Running migration: ensuring human review and evidence strength columns exist on cases")
            conn.execute(text("ALTER TABLE cases ADD COLUMN IF NOT EXISTS human_decision VARCHAR"))
            conn.execute(text("ALTER TABLE cases ADD COLUMN IF NOT EXISTS reviewer_id VARCHAR"))
            conn.execute(text("ALTER TABLE cases ADD COLUMN IF NOT EXISTS decision_timestamp TIMESTAMPTZ"))
            conn.execute(text("ALTER TABLE cases ADD COLUMN IF NOT EXISTS reviewer_notes TEXT"))
            conn.execute(text("ALTER TABLE cases ADD COLUMN IF NOT EXISTS ai_explanation TEXT"))
            conn.execute(text("ALTER TABLE cases ADD COLUMN IF NOT EXISTS evidence_strength VARCHAR"))

            # Add category and document metadata columns to evidence
            logger.info("Running migration: ensuring category and document metadata columns exist on evidence")
            conn.execute(text("ALTER TABLE evidence ADD COLUMN IF NOT EXISTS category VARCHAR"))
            conn.execute(text("ALTER TABLE evidence ADD COLUMN IF NOT EXISTS filename VARCHAR"))
            conn.execute(text("ALTER TABLE evidence ADD COLUMN IF NOT EXISTS description TEXT"))
            conn.execute(text("ALTER TABLE evidence ADD COLUMN IF NOT EXISTS verification_status VARCHAR DEFAULT 'unverified'"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS ix_evidence_category ON evidence (category)"))

            # Backfill currency from payment evidence
            conn.execute(text("""
                UPDATE cases AS c
                SET currency = UPPER(payment.content->>'currency')
                FROM evidence AS payment
                WHERE payment.case_id = c.id
                  AND payment.evidence_type = 'payment'
                  AND COALESCE(payment.content->>'currency', '') <> ''
            """))

            # Backfill human_decision from final_action if unpopulated
            conn.execute(text("""
                UPDATE cases
                SET human_decision = final_action
                WHERE final_action IS NOT NULL AND human_decision IS NULL;
            """))

            # Backfill canonical categories for existing evidence.
            # CRITICAL RULE: Unknown types must NEVER default to 'merchant'; they remain NULL (uncategorized).
            conn.execute(text("""
                UPDATE evidence
                SET category = CASE
                    WHEN LOWER(evidence_type) IN ('payment', 'refund', 'gateway', 'charge', 'ext_payment_gateway', 'transaction') THEN 'transaction'
                    WHEN LOWER(evidence_type) IN ('delivery', 'tracking', 'fulfillment', 'fulfilment', 'shipping', 'proof_of_receipt', 'ext_delivery') THEN 'delivery'
                    WHEN LOWER(evidence_type) IN ('communication', 'customer_communication', 'customer', 'otp', 'auth', 'authentication', 'ext_otp_log', 'ext_communication_log') THEN 'customer'
                    WHEN LOWER(evidence_type) IN ('merchant', 'merchant_communication', 'policy', 'refund_policy', 'invoice', 'receipt', 'merchant_notes', 'business_record') THEN 'merchant'
                    ELSE NULL
                END
                WHERE category IS NULL;
            """))

            # Normalize unreviewed statuses
            conn.execute(text("""
                UPDATE cases AS c
                SET status = CASE LOWER(c.ai_recommendation)
                    WHEN 'escalate' THEN 'ESCALATED'
                    WHEN 'request_more_evidence' THEN 'EVIDENCE_REQUESTED'
                    ELSE 'OPEN'
                END
                WHERE c.ai_recommendation IS NOT NULL
                  AND c.human_decision IS NULL
                  AND LOWER(c.status) IN ('new', 'pending_review', 'investigating');
            """))
                
    except Exception as e:
        logger.error(f"Error during schema migration: {e}")
        
    # 3. Demo Initialization
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
                seeded = False
                try:
                    from scripts.seed_evidence_db import seed_db
                    seed_db()
                    seeded = True
                except ImportError:
                    try:
                        from data.seed_evidence_db import seed_db
                        seed_db()
                        seeded = True
                    except ImportError as e:
                        logger.warning(f"Could not import seed_evidence_db: {e}")
                if seeded:
                    logger.info("Demo evidence data seeded successfully.")
            else:
                logger.info(f"Demo tables already contain {count} records, skipping seed.")
        except Exception as e:
            logger.warning(f"Could not check/seed demo tables (non-fatal): {e}")

    logger.info("Database initialization complete.")

if __name__ == "__main__":
    init_db()
