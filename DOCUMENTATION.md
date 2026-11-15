# PayProof AI: Project Documentation

PayProof AI is an AI-assisted payment risk analysis and review system developed as a full-stack web application. The main purpose of the project is to help organize and review payment-related cases in a simple and structured way.

The system allows a reviewer to create payment cases, add evidence and claims, check risk indicators, and review the available information before making a decision. Rule-based checks are used to identify possible risk conditions, while AI is used to provide additional analysis and support during the review process.

The system follows a human-in-the-loop approach. This means that AI does not make the final decision by itself. A human reviewer can check the case information, evidence, claims, rule flags, and AI analysis before taking the final action.

PayProof AI also maintains an audit log to record important activities and case status changes. This makes the review process easier to track and understand.

The frontend of the application is developed using React, TypeScript, Vite, and Tailwind CSS. The backend is developed using FastAPI. PostgreSQL is used as the database and SQLAlchemy is used for database operations. OpenRouter is used for AI-assisted analysis. The frontend and backend are deployed using Vercel and Render.

Overall, PayProof AI demonstrates how full-stack development, database management, rule-based analysis, AI assistance, and human review can be combined to build a practical payment-risk review system.

---

## 1. Core Features

### Case Management
- **Create and Organize Cases:** Reviewers can easily create payment cases and organize them in a structured manner.
- **Evidence and Claims:** The system allows attaching relevant evidence (e.g., transaction logs, delivery confirmations, OTP logs) and claims to each specific case.

### Rule-Based Analysis
- **Risk Indicators:** Deterministic rule-based checks automatically scan incoming cases to identify possible risk conditions (e.g., timelines, data mismatches).
- **Safety Fallback:** If the AI service is unavailable, the pipeline relies on the rule engine to process cases without failing.

### AI-Assisted Analysis
- **Intelligent Investigation:** Uses OpenRouter to process complex, sometimes contradictory evidence.
- **Supportive Recommendations:** AI provides an analysis summary, a recommended action (e.g., `approve`, `decline`, `request_more_evidence`), and a confidence score to support the reviewer.

### Human-in-the-Loop
- **Reviewer Control:** AI does not make the final decision. A human analyst reviews case information, evidence, claims, rule flags, and AI analysis.
- **Final Action:** The human reviewer can either approve or override the AI's recommendation before taking the final action.

### Audit Log
- **Activity Tracking:** The system automatically maintains a secure audit log.
- **Transparency:** Records important activities, evidence submissions, and case status changes, making the entire review process transparent and easy to track over time.

---

## 2. Technology Stack

### Frontend
- **Framework:** React
- **Language:** TypeScript
- **Build Tool:** Vite
- **Styling:** Tailwind CSS (with Framer Motion for animations)
- **Deployment:** Vercel

### Backend
- **Framework:** FastAPI (Python 3.10+)
- **ORM:** SQLAlchemy
- **Deployment:** Render

### Database
- **Primary Database:** PostgreSQL
- **Operations:** SQLAlchemy for robust and scalable database operations.

### AI & Integrations
- **AI Provider:** OpenRouter (Providing access to modern LLMs for case analysis)

---

## 3. System Architecture & Flow

1. **Case Ingestion:** New payment dispute cases enter the system (via API/UI).
2. **Data Collection:** Reviewers or automated processes attach necessary evidence and claims to the case.
3. **Rule Engine Processing:** The system's deterministic rule engine checks for contradictions and flags standard risk indicators.
4. **AI Analysis:** OpenRouter processes the gathered evidence, outputting a recommended action and confidence score.
5. **Human Review (UI):** Reviewers interact with the React frontend to see a unified view of the case, rule flags, and the AI's suggestions.
6. **Final Decision & Audit:** The reviewer makes the final decision. The action and any status changes are immutably recorded in the system's Audit Log via PostgreSQL.

---

## 4. Setup Instructions

### Prerequisites
- Node.js 18+
- Python 3.10+
- PostgreSQL
- OpenRouter API Key

### Backend Setup
```bash
cd payproof-backend
pip install -r requirements.txt

# Configure your environment variables
cp .env.example .env
# Ensure you set your DATABASE_URL and OPENROUTER_API_KEY in the .env file

# Run database migrations
python migrate_db.py

# Seed initial demo data (Optional)
python seed_evidence_db.py

# Start the FastAPI server
uvicorn app.main:app --reload
```

### Frontend Setup
```bash
cd payproof-frontend
npm install

# Start the Vite development server
npm run dev
```

### Environment Variables (.env)
```env
ENVIRONMENT=development
DEMO_MODE=true
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/payproof
OPENROUTER_API_KEY=your_openrouter_api_key_here
```
