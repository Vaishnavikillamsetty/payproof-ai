# PayProof AI
### Evidence-First Dispute Defense — Razorpay AI Buildathon, Track 02 (AI Risk Manager)

> PayProof AI doesn't ask an LLM whether a transaction is fraudulent. It collects evidence for a disputed transaction from source systems, verifies each claim against that evidence, checks timelines with deterministic rules, scores how complete the evidence is, and only drafts a response when it's confident enough — otherwise it says so and routes to a human.

---

## The problem

When a customer disputes a payment, the evidence proving or disproving their claim — payment records, delivery confirmation, OTP logs, merchant communication — is scattered across systems. Merchants either respond too slowly (missed dispute deadlines) or respond with weak, incomplete evidence (lost disputes that should have been won). Fully automating the decision with an LLM is unsafe: a confidently wrong AI response is worse than a slow human one.

## What PayProof AI does

```
Dispute submitted
       ↓
Evidence Collector — fetches records from source systems (payment gateway,
                      courier, OTP service, merchant CRM)
       ↓
Rule Engine — deterministic checks (timeline conflicts, amount mismatches,
              direct contradictions between claim and evidence)
       ↓
Verifier Agent (LLM) — checks each individual claim against its evidence,
                        assigns a confidence score, flags contradictions
       ↓
Completeness Score — how many evidence categories are actually available
       ↓
Policy Gate — auto-draft a response only if completeness AND confidence
              clear a threshold, AND no rule engine contradiction fired
       ↓
   ┌───────────────┴───────────────┐
   ▼                               ▼
Auto-drafted response      Human Review Required
   ▼                               ▼
        Audit Log (every step, every claim, timestamped)
```

## Why this design, not a simpler one

The obvious version of this project is: transaction data → LLM → "fraud: yes/no." We deliberately didn't build that, because:

- **An LLM's confidence is not proof.** A model can sound certain while working from incomplete or misleading information.
- **Deterministic rules catch what an LLM might rationalize past.** Our Verifier agent can score a claim at 0.8 confidence with 100% evidence completeness — and the system will still force human review if the deterministic rule engine detects a direct contradiction (e.g. customer claims "not received," delivery record says "delivered, signed by customer"). The rule engine is a hard override the LLM cannot talk its way around.
- **Insufficient evidence is a valid, safe answer.** When evidence completeness is too low, the system explicitly refuses to auto-respond rather than guessing.

## AI safety boundary

| Claude (the LLM) can | Claude cannot |
|---|---|
| Extract and structure claims from dispute text | Invent evidence that wasn't retrieved |
| Assess how well a claim is supported by given evidence | Treat a customer's claim as evidence of itself |
| Assign a confidence score with stated reasoning | Override a deterministic rule engine flag |
| Draft a response, once the policy gate approves it | Auto-resolve a case with insufficient or contradictory evidence |

Final routing decisions are always constrained by evidence completeness, deterministic rules, and confidence thresholds — never by the LLM's judgment alone.

## Where evidence comes from

This prototype's Evidence Collector queries a **seeded database simulating four external systems** (payment gateway, courier/delivery, OTP verification, merchant communication) by transaction ID — architecturally identical to how it would query real APIs. Every simulated record is labeled `[DEMO — simulated]` in the UI so this is never presented as live production data. In production, these four lookups would be replaced with real integrations to a payment gateway, logistics/courier API, authentication/OTP service, and merchant support system — the rest of the pipeline (rules, verification, scoring, policy gate) would not need to change.

## Results (held-out evaluation, 30 labeled test cases)

| Metric | Value |
|---|---|
| Precision | 42.3% |
| Recall | 100% |
| Unsafe auto-resolves | **0** |
| Unnecessary human reviews (false positives) | 15 (est. $75 in review time at $5/review) |

**Read this honestly, not defensively:** the system is deliberately conservative. It never once let an ambiguous case slip through as auto-resolved (0 unsafe resolves) — its only failure mode is over-caution, flagging some legitimate cases for review that a human would have cleared quickly. That's the correct tradeoff for a financial risk system: the cost of an unnecessary review is small and recoverable; the cost of an unsafe automated decision is not. Policy threshold tuning is the clear next step to reduce false positives without reintroducing unsafe resolves.

A representative example: one false positive had a completeness score of 60/60 and LLM confidence of 0.8 — both well above the auto-resolve threshold — but was still routed to human review because the rule engine detected the customer's "not received" claim directly contradicted a signed delivery record. This is the system working as designed, not a bug.

## Architecture

- **Backend:** Python, FastAPI, SQLAlchemy, PostgreSQL
- **LLM:** Anthropic Claude (claude-sonnet-4-6) via the Messages API, used only for claim verification and response drafting — never for the final routing decision
- **Frontend:** React, TypeScript, Vite, Tailwind CSS, Framer Motion, Recharts
- **Rule Engine:** plain deterministic Python — no ML, fully explainable

## Running locally

```bash
# Backend
cd payproof-backend
pip install -r requirements.txt
# set ANTHROPIC_API_KEY and DATABASE_URL in .env
python data/seed_evidence_db.py   # populate mock external systems
python data/generate_dataset.py   # generate the 180-case evaluation set
uvicorn app.main:app --reload

# Frontend
cd payproof-frontend
npm install
npm run dev
```

Run the evaluation: `python scripts/evaluate.py`

## Demo transaction IDs

| Transaction ID | Dispute Reason | Outcome |
|---|---|---|
| `DEMO_TXN_REVIEW_1` | product not received | Human review — rule engine overrides a high-confidence, high-completeness case due to a direct contradiction |
| `DEMO_TXN_STRONG_1` | subscription not cancelled | Auto-resolved — full evidence, high confidence |
| `DEMO_TXN_WEAK_2` | product not as described | Weak case — insufficient evidence, safely deferred |
| `DEMO_TXN_EMPTY_1` | any | Human review — no evidence found at all |

## What's deliberately out of scope for this build

Built with the same rigor as the rest of the system, but scoped out to keep the MVP honest and complete rather than broad and half-finished:
- Multi-agent debate (separate merchant-favoring / customer-favoring agents)
- Fraud ring / coordinated-abuse graph detection across multiple cases
- Real payment gateway, courier, and OTP integrations (currently seeded mock data, architecturally ready to swap in)

## Team

Built solo by Vaishnavi, final-year B.Tech IT student, for Razorpay's AI Buildathon (Track 02 — AI Risk Manager).
