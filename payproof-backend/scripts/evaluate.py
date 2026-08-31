import json
import logging
import os
import sys
from uuid import UUID

# Ensure the app module can be imported
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.db.models import AuditLog, Case, Claim, RuleFlag
from app.db.session import SessionLocal
from app.orchestrator import run_pipeline

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

AVG_REVIEW_COST_USD = 5.00

def evaluate():
    logger.info("Starting held-out evaluation...")
    
    gt_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'ground_truth.json')
    if not os.path.exists(gt_path):
        logger.error(f"Ground truth file not found at {gt_path}")
        return

    with open(gt_path, 'r') as f:
        ground_truth = json.load(f)

    # Filter for test split
    test_cases = {k: v for k, v in ground_truth.items() if v.get("split") == "test"}
    logger.info(f"Found {len(test_cases)} test cases.")

    if len(test_cases) == 0:
        logger.warning("No test cases found. Did you run data/generate_dataset.py?")
        return

    db = SessionLocal()

    tp = 0
    fp = 0
    tn = 0
    fn = 0

    results = []

    for idx, (case_id_str, truth) in enumerate(test_cases.items()):
        logger.info(f"Processing case {idx+1}/{len(test_cases)}: {case_id_str}")
        case_id = UUID(case_id_str)
        
        # Reset case to "new" to ensure clean run
        case = db.query(Case).filter(Case.id == case_id).first()
        if not case:
            logger.warning(f"Case {case_id_str} not found in DB, skipping.")
            continue
            
        # Prevent DB pollution by deleting existing derived records for this case.
        # Do NOT delete the Case itself, nor the synthetic Evidence required for testing.
        db.query(Claim).filter(Claim.case_id == case_id).delete()
        db.query(RuleFlag).filter(RuleFlag.case_id == case_id).delete()
        db.query(AuditLog).filter(AuditLog.case_id == case_id).delete()
        
        # Reset case status
        case.status = "new"
        case.completeness_score = None
        case.overall_confidence = None
        db.commit()
        
        # Run pipeline synchronously
        run_pipeline(case_id, db)
        
        # Re-fetch to get updated status
        db.refresh(case)
        status = case.status
        label = truth["label"]

        # Evaluation Logic Rationale:
        # The goal of this system is to auto-resolve clear cases (strong_case) 
        # and route unclear cases to human review (human_review/weak_case).
        # - Ground Truth "ambiguous": Requires human review (Positive class).
        # - Ground Truth "legitimate" / "fraudulent": Clear cases that should be auto-resolved (Negative class).
        # 
        # Therefore:
        # TP = Correctly routed to human review (was ambiguous)
        # FP = Unnecessarily routed to human review (was clear) -> Wasted effort
        # TN = Correctly auto-resolved (was clear)
        # FN = Dangerously auto-resolved (was ambiguous) -> Unsafe
        
        is_positive_pred = status in ["human_review", "weak_case"]
        is_positive_true = label == "ambiguous"

        if is_positive_true and is_positive_pred:
            tp += 1
            result_type = "TP (Correctly Flagged for Review)"
        elif not is_positive_true and is_positive_pred:
            fp += 1
            result_type = "FP (Unnecessarily Flagged for Review)"
        elif not is_positive_true and not is_positive_pred:
            tn += 1
            result_type = "TN (Correctly Auto-Resolved)"
        else: # is_positive_true and not is_positive_pred
            fn += 1
            result_type = "FN (Dangerously Auto-Resolved)"

        results.append({
            "case_id": case_id_str,
            "label": label,
            "status": status,
            "result_type": result_type
        })

    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    
    total_cost = fp * AVG_REVIEW_COST_USD
    cost_statement = f"{fp} clear dispute{'s' if fp != 1 else ''} would have been unnecessarily auto-flagged for human review, costing ${total_cost:.2f} in wasted manual review time (assuming ${AVG_REVIEW_COST_USD:.2f} per review)."
    
    if fn > 0:
        fn_statement = f"CRITICAL INCIDENT: {fn} ambiguous case{'s' if fn != 1 else ''} {'were' if fn != 1 else 'was'} incorrectly auto-resolved instead of being routed for human review. This is a high-severity failure (unsafe auto-resolve)."
    else:
        fn_statement = "0 ambiguous cases were improperly auto-resolved. System maintained strict boundaries."

    metrics = {
        "confusion_matrix": {
            "true_positives": tp,
            "false_positives": fp,
            "true_negatives": tn,
            "false_negatives": fn,
            "total": len(test_cases)
        },
        "rates": {
            "precision": round(precision, 4),
            "recall": round(recall, 4)
        },
        "business_impact": {
            "wasted_reviews": fp,
            "cost_statement": cost_statement,
            "unsafe_resolves": fn,
            "unsafe_statement": fn_statement
        },
        "case_details": results
    }

    out_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'eval_metrics.json')
    with open(out_path, 'w') as f:
        json.dump(metrics, f, indent=2)

    logger.info("Evaluation complete.")
    logger.info(f"Precision: {precision:.2%}, Recall: {recall:.2%}")
    logger.info(f"TP: {tp}, FP: {fp}, TN: {tn}, FN: {fn}")
    logger.info(f"Cost Statement: {cost_statement}")
    logger.info(f"Severity Statement: {fn_statement}")
    logger.info(f"Metrics written to {out_path}")

if __name__ == "__main__":
    evaluate()
