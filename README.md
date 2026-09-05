# PayProof AI

PayProof AI is an intelligent dispute resolution platform designed to automatically investigate and resolve chargebacks and payment disputes. By integrating a deterministic rule engine with advanced LLM capabilities (Anthropic's Claude), PayProof AI achieves high accuracy in classifying dispute evidence and making automated recommendations, minimizing manual human review.

## 🚀 Live Demo

**PayProof AI:** https://payproof-frontend.vercel.app/

## Features

- **Automated Evidence Gathering:** Simulates retrieval of payment gateway logs, delivery confirmations, OTP logs, and merchant communications.
- **AI-Powered Investigation:** Leverages Anthropic's Claude to analyze complex, contradictory evidence and produce structured recommendations.
- **Deterministic Safety Fallback:** Seamlessly falls back to a deterministic rule-based engine if live AI is unavailable, ensuring the pipeline never fails.
- **Human-in-the-Loop Review:** Flags high-risk or low-confidence cases for manual review. AI recommendations are safely preserved independently of human override decisions.
- **Real-Time Metrics:** Live dashboard tracking case lifecycle, automated resolution rates, contradiction frequencies, and AI confidence levels.
- **Dynamic Currency Support:** Fully handles international transaction data natively without hardcoded currency assumptions.

## Architecture

The project consists of two main components:
1. **Backend (`/payproof-backend`)**: A FastAPI Python backend utilizing SQLAlchemy for SQLite/PostgreSQL, featuring a custom orchestrator and AI agents pipeline.
2. **Frontend (`/payproof-frontend`)**: A React + Vite application leveraging Framer Motion for animations and Recharts for live dashboard metrics.

### System Flow
1. **Case Ingestion:** Cases enter via API (e.g., from a Webhook).
2. **Evidence Collection:** Relevant transaction data is queried.
3. **Rule Engine:** Deterministic timelines and basic contradictions are flagged.
4. **AI Investigation:** Claude (or the rule-engine fallback) processes the evidence and outputs a `recommended_action`, `confidence`, and `risk_level`.
5. **Policy Gate:** Final system status is assigned based on completeness, AI confidence, and contradictions.
6. **Human Review:** Analysts review the findings on the frontend, choosing to approve or override the AI recommendation.

## Setup Instructions

### Prerequisites
- Python 3.10+
- Node.js 18+
- (Optional) Anthropic API Key

### Backend Setup
```bash
cd payproof-backend
pip install -r requirements.txt

# Run initial migrations (if needed)
python migrate_db.py

# Seed demo data
python seed_evidence_db.py

# Start the API server
uvicorn app.main:app --reload
```

### Frontend Setup
```bash
cd payproof-frontend
npm install

# Start the dev server
npm run dev
```

### Environment Variables (Backend)
Create a `.env` file in the `payproof-backend` directory:
```
ENVIRONMENT=development
DEMO_MODE=true
ANTHROPIC_API_KEY=your_api_key_here  # Optional: Will use deterministic fallback if omitted
```

## Data Integrity & Lifecycle

- `status`: The lifecycle state of a case (e.g., `new`, `investigating`, `resolved`).
- `ai_recommendation`: The unedited output from the AI (e.g., `contest`, `request_more_evidence`).
- `final_action`: The actual business action decided by a human reviewer. 
- `contradiction_detected`: Native boolean flag indicating conflicting evidence (e.g., Payment cleared but OTP failed).

## Testing

The backend includes a comprehensive pytest suite covering the API, rule engine, orchestrator, and AI agent fallback behaviors.

```bash
cd payproof-backend
pytest -v
```

All agent tests natively bypass the live LLM to prevent accidental API consumption during CI/CD.
