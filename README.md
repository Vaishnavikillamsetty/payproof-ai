# PayProof AI
### Evidence-First Dispute Defense — Razorpay AI Buildathon, Track 02 (AI Risk Manager)

> PayProof AI doesn't ask an LLM whether a transaction is fraudulent. It collects evidence for a disputed transaction from source systems, verifies each claim against that evidence, checks timelines with deterministic rules, scores how complete the evidence is, and recommends an action — but it always defers the final financial decision to a human.

---

## The problem

When a customer disputes a payment, the evidence proving or disproving their claim — payment records, delivery confirmation, OTP logs, merchant communication — is scattered across systems. Merchants either respond too slowly (missed dispute deadlines) or respond with weak, incomplete evidence (lost disputes that should have been won). Fully automating the decision with an LLM is unsafe: a confidently wrong AI response is worse than a slow human one.

## What PayProof AI does

```
Dispute submitted (Razorpay Webhook or Manual Demo)
       ↓
Evidence Collector — fetches records from source systems 
                      (Live Razorpay API + Simulated merchant systems)
       ↓
Rule Engine — deterministic checks (timeline conflicts, amount mismatches,
              direct contradictions between claim and evidence)
       ↓
Bounded AI Agent (LLM) — calls tools (max 5 steps) to gather data, checks 
                         each claim, and outputs a structured recommendation
       ↓
Completeness Score — how many evidence categories are actually available
       ↓
Policy Gate — deterministic safety check to enforce human review 
              if the rule engine detects a contradiction
       ↓
   ┌───────────────┴───────────────┐
   ▼                               ▼
AI Recommends Action        Missing Data / Contradiction
(Contest/Accept)            (More Evidence / Escalate)
   ▼                               ▼
        Audit Log (every tool call, every event, timestamped)
```

## Why this design, not a simpler one

The obvious version of this project is: transaction data → LLM → "fraud: yes/no." We deliberately didn't build that, because:

- **An LLM's confidence is not proof.** A model can sound certain while working from incomplete or misleading information.
- **Deterministic rules catch what an LLM might rationalize past.** Our AI agent can score a claim at 0.8 confidence with 100% evidence completeness — and the system will still force human escalation if the deterministic rule engine detects a direct contradiction (e.g. customer claims "not received," delivery record says "delivered, signed by customer"). The rule engine is a hard override the LLM cannot talk its way around.
- **Insufficient evidence is a valid, safe answer.** When evidence completeness is too low, the system explicitly recommends requesting more evidence rather than guessing.

## AI Agent & Safety Boundary

The system uses a **Bounded Read-Only AI Investigation Agent**. It leverages Anthropic's native tool-calling loop (bounded to a maximum of 5 steps) to gather evidence and produce a structured JSON output. If the LLM fails, hallucinates, or returns invalid JSON, the system safely falls back to a deterministic rule-based output.

| Claude (the LLM) can | Claude cannot |
|---|---|
| Call tools to lookup payments and read evidence | Invent evidence that wasn't retrieved |
| Assess how well a claim is supported by given evidence | Treat a customer's claim as evidence of itself |
| Recommend an action with a confidence score | Override a deterministic rule engine flag |
| Summarize the case findings | Automatically execute Accept/Contest API actions |

### Human Control
**The AI recommends an action. It does not automatically accept or contest a financial dispute.** The frontend makes it explicitly clear that a human must review the AI's findings (which are strictly separated from verified Razorpay data) before any API mutation occurs. 

## Integration Status: Real vs Mocked Capabilities

To demonstrate both real-world integration skills and complex risk scenarios, this project uses a mix of live Razorpay APIs and simulated merchant data.

### REAL IMPLEMENTED CAPABILITIES
The backend contains a fully functional `LiveRazorpayProvider` and webhook handler. When configured with live credentials, the following are real integrations:
- **Payment lookup** (Real Razorpay API)
- **Refund lookup** (Real Razorpay API)
- **Dispute lookup** (Real Razorpay API)
- **Webhook signature verification** (Raw-byte HMAC SHA-256 validation)
- **Dispute lifecycle event handling** (Idempotent processing of `payment.dispute.created`, `won`, `lost`, `closed`, etc.)

### DEMO / SIMULATED CAPABILITIES
Because we do not have access to real merchant databases, the following are simulated. In the UI, these are strictly separated from "Verified by Razorpay" data.
- **Seeded demo disputes**
- **Delivery evidence**
- **OTP evidence**
- **Communication evidence**
- **Mock Razorpay provider data** (used only when `MOCK_VERIFIER=true` for safe local hackathon testing without credentials)

## Integration Matrix

| Capability | Implementation | Verification Status |
| :--- | :--- | :--- |
| Payment lookup | Live Provider + Demo Provider | CODE-READY / VERIFIED |
| Refund lookup | Live Provider + Demo Provider | CODE-READY / VERIFIED |
| Dispute lookup | Live Provider + Demo Provider | CODE-READY / VERIFIED |
| Webhook signature | HMAC SHA-256 | UNIT TESTED / VERIFIED |
| Webhook delivery | Razorpay webhook endpoint | NOT YET DEPLOYMENT VERIFIED |
| AI investigation | Anthropic native tool use | IMPLEMENTED |
| Demo evidence | Seeded DB | DEMO |

## Demo transaction IDs

Tested manually via the UI:

| Transaction ID | Dispute Reason | AI Recommendation |
|---|---|---|
| `DEMO_TXN_REVIEW_1` | product not received | **Escalation Recommended** — rule engine overrides a high-confidence case due to a direct contradiction |
| `DEMO_TXN_STRONG_1` | subscription not cancelled | **Contest Recommended** — full evidence, high confidence |
| `DEMO_TXN_WEAK_2` | unauthorized transaction | **More Evidence Requested** — insufficient evidence |
| `DEMO_TXN_EMPTY_1` | product not as described | **More Evidence Requested** — no evidence found at all |

## Production Roadmap

If this were deployed to production beyond the Buildathon, the following architectural upgrades would be required:
1. **Persistent background job queue:** Replace FastAPI `BackgroundTasks` with Celery, Redis, or SQS to ensure investigation tasks survive pod restarts.
2. **Proper database migrations:** Replace the hackathon `init_db.py` script with Alembic.
3. **Real merchant integrations:** Connect the Evidence Collector to real Shopify/Shiprocket/Zendesk APIs instead of the seeded mock DB.
4. **Human approval workflow before mutation APIs:** Wire the UI's "Accept" and "Contest" buttons to actually trigger Razorpay's Dispute Accept/Contest mutation APIs, guarded by authentication.
5. **Production webhook monitoring:** Implement a robust dead-letter queue and retry mechanism for failed webhooks.

## Architecture

- **Backend:** Python, FastAPI, SQLAlchemy, PostgreSQL
- **LLM:** Anthropic Claude via native tool-calling
- **Frontend:** React, TypeScript, Vite, Tailwind CSS, Framer Motion
- **Rule Engine:** plain deterministic Python — no ML, fully explainable

## Team

Built solo by Vaishnavi, final-year B.Tech IT student, for Razorpay's AI Buildathon (Track 02 — AI Risk Manager).
