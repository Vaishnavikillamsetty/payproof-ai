# PayProof AI

PayProof AI is an AI-assisted payment risk analysis and review system developed as a full-stack web application. The main purpose of the project is to help organize and review payment-related cases in a simple and structured way.

The system allows a reviewer to create payment cases, add evidence and claims, check risk indicators, and review the available information before making a decision. Rule-based checks are used to identify possible risk conditions, while AI is used to provide additional analysis and support during the review process.

The system follows a human-in-the-loop approach. This means that AI does not make the final decision by itself. A human reviewer can check the case information, evidence, claims, rule flags, and AI analysis before taking the final action.

PayProof AI also maintains an audit log to record important activities and case status changes. This makes the review process easier to track and understand.

The frontend of the application is developed using React, TypeScript, Vite, and Tailwind CSS. The backend is developed using FastAPI. PostgreSQL is used as the database and SQLAlchemy is used for database operations. OpenRouter is used for AI-assisted analysis. The frontend and backend are deployed using Vercel and Render.

Overall, PayProof AI demonstrates how full-stack development, database management, rule-based analysis, AI assistance, and human review can be combined to build a practical payment-risk review system.

---

## 🚀 Live Demo

**PayProof AI:** https://payproof-frontend.vercel.app/

---

## Core Features

- **Case Management:** Reviewers can create payment cases and organize them by attaching relevant evidence (e.g., gateway logs, delivery confirmations, OTP logs) and claims.
- **Rule-Based Analysis:** Deterministic rule-based checks automatically scan incoming cases to identify possible risk conditions and contradictions.
- **AI-Assisted Investigation:** Leverages OpenRouter to process complex evidence and produce structured recommendations, alongside a confidence score.
- **Human-in-the-Loop:** Flags cases for manual review. A human reviewer checks case information, evidence, claims, rule flags, and AI analysis before taking the final action.
- **Audit Log:** Automatically maintains a secure audit log to record important activities and case status changes for transparency.

## Architecture

1. **Backend (`/payproof-backend`)**: A FastAPI Python backend utilizing SQLAlchemy for PostgreSQL, featuring a custom rule engine and OpenRouter AI agents pipeline.
2. **Frontend (`/payproof-frontend`)**: A React + Vite application written in TypeScript, leveraging Tailwind CSS for styling and Recharts for live dashboard metrics.

### System Flow
1. **Case Ingestion:** Cases are created and enter the system.
2. **Data Collection:** Evidence and claims are attached to the case.
3. **Rule Engine:** Deterministic timelines and basic contradictions are flagged.
4. **AI Investigation:** OpenRouter processes the evidence and outputs a `recommended_action`, `confidence`, and analysis summary.
5. **Human Review:** Analysts review the findings on the frontend, choosing to approve or override the AI recommendation before taking the final action.
6. **Audit Logging:** Final decisions and state changes are recorded in the system's audit log.

## Setup Instructions

### Prerequisites
- Python 3.10+
- Node.js 18+
- PostgreSQL
- OpenRouter API Key

### Backend Setup
```bash
cd payproof-backend
pip install -r requirements.txt

# Run initial migrations
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

### Environment Variables
Create a `.env` file in the `payproof-backend` directory:
```
ENVIRONMENT=development
DEMO_MODE=true
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/payproof
OPENROUTER_API_KEY=your_openrouter_api_key_here
```

## Testing

The backend includes a comprehensive pytest suite covering the API, rule engine, orchestrator, and AI agent fallback behaviors.

```bash
cd payproof-backend
pytest -v
```
