import os
import json
from fastapi import APIRouter, HTTPException

router = APIRouter(prefix="/metrics", tags=["metrics"])

@router.get("/")
def get_metrics():
    """
    Returns the evaluation metrics computed by scripts/evaluate.py.
    """
    file_path = os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'eval_metrics.json')
    
    if not os.path.exists(file_path):
        # Return a clean 404 or a placeholder if the script hasn't been run yet
        raise HTTPException(status_code=404, detail="Metrics not found. Please run scripts/evaluate.py first.")
        
    with open(file_path, 'r') as f:
        data = json.load(f)
        
    return data
