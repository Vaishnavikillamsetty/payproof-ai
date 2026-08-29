# PayProof AI — Full Build Plan
### Evidence-First Chargeback & Dispute Defense Agent — Razorpay AI Buildathon, Track 02 (AI Risk Manager)
**Deadline: Sept 5, 2026 (7 days from today, Aug 29, 2026)**

---

## 0. The one sentence you build everything around

> **PayProof AI doesn't ask an LLM whether a transaction is fraudulent. It collects evidence for a disputed transaction, verifies each claim against its source record, checks timelines with deterministic rules, scores how complete the evidence is, and only drafts a response when it's confident enough — otherwise it says so and asks for a human.**

Every feature below either serves that sentence or gets cut. If you're ever unsure whether to build something, ask "does this make the system more honest, or just more impressive-looking?" Build the honest ones first.

---

## 1. Locked MVP Scope (build only this for days 1–5)

| # | Feature | Why it's in |
|---|---------|-------------|
| 1 | Case intake (a disputed transaction enters the system) | Entry point |
| 2 | Evidence Collector agent — gathers payment, order, delivery, and message records for the case | Perception layer |
| 3 | Rule Engine — deterministic timeline/logic checks (refund-before-payment, delivery-before-cancellation, amount mismatch) | This is what makes it *not* "just an LLM guessing" — your strongest talking point |
| 4 | Verifier agent — LLM checks each claim against its evidence, assigns confidence, flags contradictions | Reasoning layer |
| 5 | Evidence Completeness Score (0–100%) with named missing items | Your best demo moment |
| 6 | Policy Gate — auto-draft response only if completeness + confidence clear a threshold; otherwise routes to "Human Review Required" | Bounded autonomy — matches Razorpay's exact language |
| 7 | Case dashboard (list + detail view with clickable evidence trail) | Your audit trail, visually |
| 8 | Synthetic dataset (150–200 labeled cases) + held-out test split + precision/recall/false-positive cost report | Required — "measured precision/recall" is explicitly graded |

**Explicitly cut from v1** (mention only as "designed for, not built" in your pitch — this shows scope discipline, which reads *well* to reviewers):
- Multi-agent debate (merchant-side vs customer-side agents)
- Fraud ring / abuse-cluster graph detection
- Neo4j / graph database
- Merchant Trust Passport (that's a different project — don't merge two ideas into one)

Day 6 is buffer. Day 7 is submission only. If you're behind on Day 4, cut #7's polish before you cut #3–#6 — the rule engine + policy gate + completeness score are your actual thesis.

---

## 2. Tech Stack (exact, no substitutions needed)

**Backend**
- Python 3.11 + **FastAPI** (you already know this from the SCRC bridge server)
- **Pydantic** for request/response schemas
- **SQLAlchemy** + **PostgreSQL** for the case database
- **Anthropic API** (`claude-sonnet-4-6` — call it directly per the API pattern below) for the Verifier agent's reasoning and response drafting
- Plain Python for the Rule Engine — no ML library needed, these are `if/else` timeline checks

**Frontend**
- **React** + **TypeScript** + **Vite** (fast dev server, judges will run this live)
- **Tailwind CSS** for styling
- **Framer Motion** for the handful of deliberate animations (see design section)
- **Recharts** for the precision/recall and completeness visualizations

**Why not React Native / mobile:** judges need to open a browser tab and see it working in 10 seconds. A web dashboard is the right call here — save React Native for a future project.

---

## 3. System Architecture

```
                    ┌─────────────────────┐
                    │   React Dashboard   │
                    └──────────┬──────────┘
                               │ REST (JSON)
                    ┌──────────▼──────────┐
                    │   FastAPI Backend   │
                    └──────────┬──────────┘
                               │
                    ┌──────────▼──────────┐
                    │   Case Orchestrator │  ← receives a dispute, runs the pipeline below
                    └──────────┬──────────┘
                               │
              ┌────────────────┼────────────────┐
              ▼                                  ▼
    ┌──────────────────┐              ┌──────────────────┐
    │ Evidence Collector │              │   Rule Engine    │
    │      (agent)       │              │  (deterministic) │
    └──────────┬─────────┘              └─────────┬────────┘
               │                                   │
               └────────────────┬──────────────────┘
                                 ▼
                       ┌──────────────────┐
                       │  Verifier Agent   │  ← LLM: checks claims vs evidence,
                       │       (LLM)       │     assigns per-claim confidence
                       └─────────┬─────────┘
                                 ▼
                       ┌──────────────────┐
                       │ Completeness Score│
                       └─────────┬─────────┘
                                 ▼
                       ┌──────────────────┐
                       │   Policy Gate     │  ← threshold check
                       └─────────┬─────────┘
                          ┌──────┴──────┐
                          ▼             ▼
                  Draft Response   Human Review Required
                          │             │
                          └──────┬──────┘
                                 ▼
                       ┌──────────────────┐
                       │    Audit Log      │  ← every step, every claim, timestamped
                       └──────────────────┘
```

---

## 4. Database Schema (PostgreSQL)

```sql
-- A disputed transaction
CREATE TABLE cases (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    transaction_id TEXT NOT NULL,
    dispute_reason TEXT NOT NULL,          -- e.g. "product not received"
    customer_claim TEXT NOT NULL,
    merchant_id TEXT NOT NULL,
    amount NUMERIC NOT NULL,
    status TEXT NOT NULL DEFAULT 'new',    -- new | investigating | strong_case | weak_case | human_review | resolved
    completeness_score NUMERIC,
    overall_confidence NUMERIC,
    created_at TIMESTAMP DEFAULT now(),
    updated_at TIMESTAMP DEFAULT now()
);

-- Every piece of evidence gathered for a case
CREATE TABLE evidence (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    case_id UUID REFERENCES cases(id),
    evidence_type TEXT NOT NULL,           -- payment | order | delivery | communication | otp
    source_id TEXT,                        -- e.g. "SHIP_82391"
    content JSONB NOT NULL,
    event_timestamp TIMESTAMP,             -- when the real-world event happened
    collected_at TIMESTAMP DEFAULT now()
);

-- Each individual claim the Verifier checks, with its own confidence
CREATE TABLE claims (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    case_id UUID REFERENCES cases(id),
    claim_text TEXT NOT NULL,              -- "product was delivered"
    supporting_evidence_ids UUID[],
    contradicting_evidence_ids UUID[],
    confidence NUMERIC,                    -- 0.0–1.0
    verdict TEXT                           -- supported | contradicted | unverifiable
);

-- Deterministic rule check results
CREATE TABLE rule_flags (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    case_id UUID REFERENCES cases(id),
    rule_name TEXT NOT NULL,               -- "refund_before_payment"
    triggered BOOLEAN NOT NULL,
    detail TEXT
);

-- Immutable audit trail — every action the system took
CREATE TABLE audit_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    case_id UUID REFERENCES cases(id),
    step TEXT NOT NULL,                    -- "evidence_collected" | "rule_checked" | "claim_verified" | "policy_decision"
    detail JSONB,
    timestamp TIMESTAMP DEFAULT now()
);
```

---

## 5. Backend Folder Structure

```
payproof-backend/
├── app/
│   ├── main.py                 # FastAPI app, route registration
│   ├── config.py                # env vars, API keys
│   ├── db/
│   │   ├── models.py            # SQLAlchemy models (mirrors schema above)
│   │   └── session.py
│   ├── routers/
│   │   ├── cases.py             # POST /cases, GET /cases, GET /cases/{id}
│   │   └── evidence.py          # GET /cases/{id}/evidence
│   ├── agents/
│   │   ├── evidence_collector.py
│   │   └── verifier.py          # calls Anthropic API
│   ├── rules/
│   │   └── engine.py            # deterministic timeline/logic checks
│   ├── orchestrator.py          # runs the full pipeline in order, writes audit_log
│   └── schemas.py               # Pydantic request/response models
├── data/
│   └── generate_dataset.py      # synthetic case generator
├── tests/
│   └── test_rule_engine.py
├── requirements.txt
└── .env
```

### Key endpoints

```
POST   /cases                    → submit a new dispute, triggers orchestrator
GET    /cases                    → list all cases (for the dashboard table)
GET    /cases/{id}               → full case detail: evidence, claims, rule flags, verdict
GET    /cases/{id}/audit         → full audit trail for that case
POST   /cases/{id}/override      → human reviewer approves/rejects the draft
GET    /metrics                  → precision, recall, false-positive rate on the test set
```

---

## 6. Agent & Rule Engine Logic

### 6.1 Rule Engine (write this first — it's pure Python, no API calls, and it's your fastest win)

```python
# app/rules/engine.py

def check_timeline_rules(case, evidence_list):
    flags = []

    payment_evt = next((e for e in evidence_list if e.evidence_type == "payment"), None)
    delivery_evt = next((e for e in evidence_list if e.evidence_type == "delivery"), None)
    refund_evt = next((e for e in evidence_list if e.evidence_type == "refund"), None)

    if refund_evt and payment_evt and refund_evt.event_timestamp < payment_evt.event_timestamp:
        flags.append(("refund_before_payment", True, "Refund timestamp precedes payment timestamp"))

    if delivery_evt and case.dispute_reason == "product not received" and delivery_evt is not None:
        flags.append(("delivery_evidence_exists_but_disputed", True,
                       "Delivery record exists despite non-receipt claim — needs verifier review"))

    if payment_evt and case.amount != payment_evt.content.get("amount"):
        flags.append(("amount_mismatch", True, "Disputed amount does not match payment record"))

    return flags
```

Add 4–6 rules like this. Each one is a single, explainable `if` check — this is exactly what "deterministic, not hallucinated" means in your pitch.

### 6.2 Verifier Agent (LLM call)

Structure the prompt to force **structured output only** — this is non-negotiable, it's what makes the system auditable instead of a black box:

```python
# app/agents/verifier.py
import anthropic

client = anthropic.Anthropic()  # reads ANTHROPIC_API_KEY from env

VERIFIER_PROMPT = """You are a claims verifier for a payment dispute case.
Given a claim and the evidence records below, output ONLY valid JSON — no preamble.

Claim: {claim_text}

Evidence:
{evidence_json}

Return exactly this JSON shape:
{{
  "verdict": "supported" | "contradicted" | "unverifiable",
  "confidence": <float 0.0-1.0>,
  "reasoning": "<one sentence, plain language>"
}}
"""

def verify_claim(claim_text: str, evidence: list[dict]) -> dict:
    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=300,
        messages=[{
            "role": "user",
            "content": VERIFIER_PROMPT.format(claim_text=claim_text, evidence_json=evidence)
        }]
    )
    # parse message.content[0].text as JSON, strip ```json fences if present
    ...
```

### 6.3 Completeness Score

```python
CRITICAL_EVIDENCE = {"payment": 30, "delivery": 30, "otp": 20, "communication": 20}

def completeness_score(evidence_list):
    present_types = {e.evidence_type for e in evidence_list}
    score = sum(weight for etype, weight in CRITICAL_EVIDENCE.items() if etype in present_types)
    missing = [etype for etype in CRITICAL_EVIDENCE if etype not in present_types]
    return score, missing
```

### 6.4 Policy Gate

```python
def policy_decision(completeness, avg_confidence, contradictions_found):
    if contradictions_found:
        return "human_review", "Contradicting evidence detected"
    if completeness >= 70 and avg_confidence >= 0.75:
        return "strong_case", "Auto-draft approved"
    if completeness < 40:
        return "human_review", "Insufficient evidence — do not auto-respond"
    return "weak_case", "Borderline — recommend human review before response"
```

This function, plus the rule engine, is what you show first in your pitch video. It's the whole "bounded autonomy" story in ~15 lines.

---

## 7. Dataset & Evaluation Plan

Don't build 1,000 cases — build **180 well-labeled ones**. Honesty on a smaller set beats a huge sloppy one.

- **150 training/dev cases** — use to tune your completeness weights and policy thresholds
- **30 held-out test cases** — never look at these while tuning; run once at the end

**How to generate them credibly:**
1. Write a Python script that generates synthetic disputes across 4–5 categories: product not received, product not as described, duplicate charge, subscription not cancelled, unauthorized transaction.
2. For each case, randomly decide the "ground truth" (genuinely fraudulent claim / genuinely legitimate claim / ambiguous) and *then* generate evidence that's consistent with that truth — sometimes with a piece deliberately missing or a timestamp deliberately contradictory, so your rule engine and completeness score have real signal to catch.
3. Store the ground truth label separately from what your system sees, so you can score against it honestly.

**Report these numbers, exactly as Razorpay's brief asks for:**
- Precision, recall on the test set
- False-positive cost in plain language: "X legitimate customers would have been auto-flagged, costing Y in review time / trust"
- A confusion matrix (use Recharts or just a clean table)

---

## 8. Frontend Design — "The Case File" direction

### Why this direction (not a generic dashboard)

Generic fintech dashboards default to one of three looks: cream+serif+terracotta, black+neon-green, or newspaper-hairline-grid. None of those *mean* anything for a project whose entire thesis is "evidence, verification, audit trail." So the design should look and feel like an **investigator's case file** — because that's literally what the product is. Every visual choice below ties back to that metaphor, not decoration for its own sake.

### Design tokens

**Color**
| Name | Hex | Use |
|---|---|---|
| Ink | `#0E1420` | Background, headers |
| Paper | `#F6F2E9` | Evidence cards, light surfaces |
| Verified Teal | `#3FA796` | Supported claims, "strong case" |
| Flag Amber | `#E0A339` | Weak/borderline, missing evidence |
| Contradiction Red | `#D6483C` | Contradicted claims, timeline conflicts |
| Slate | `#5B6B7C` | Secondary text, metadata |

**Type**
- Display / headers / data labels: **IBM Plex Mono** — a typewriter-adjacent monospace that reads as "case file," used at restraint (headers, case IDs, timestamps, stamps only — never body paragraphs)
- Body: **Inter** — clean, highly legible, does the actual reading work
- Set a clear scale: 13px metadata → 15px body → 20px section headers → 32px case titles

**Layout concept**
- The case list is a stack of **index-card-style rows**, not a dense data table — each row has a left edge colored by verdict (teal/amber/red), like a filing tab
- The case detail view is a **two-column case file**: left column is the evidence trail (a vertical timeline of collected evidence, each item a small "pinned card"), right column is the verdict panel — completeness score, confidence, the policy decision, and the draft response
- Every claim is clickable and expands inline to show its supporting/contradicting evidence — this is your audit trail made visible, don't hide it behind a modal

**The signature element**
A **rotated confidence stamp** — literally styled like a rubber ink stamp (slightly rotated 3–5°, a subtly textured/grainy border, bold monospace text) — appears on every case card and reads e.g. `VERIFIED · 94%` in teal ink, or `INSUFFICIENT EVIDENCE` in red, or `HUMAN REVIEW` in amber. This is the one bold, memorable visual moment — everything else on the page stays quiet and disciplined so this stamp reads clearly every time. Judges will remember this.

**Motion — used deliberately, not scattered**
- On case load: evidence cards animate in one-by-one along the timeline (staggered ~80ms), as if being pinned up in front of you — this *demonstrates* the collection process rather than just showing a finished state
- The confidence stamp does a single quick "stamp down" scale+rotate animation when a verdict is reached — one satisfying moment, not a looping effect
- Respect `prefers-reduced-motion` — disable the above for users who need it

### Page-by-page

1. **Dashboard (case list)** — index-card rows, filter by verdict, a small summary strip at top (total cases, avg completeness, precision/recall from your test run)
2. **Case detail** — the two-column case file described above; this is where you'll spend your demo time
3. **Metrics page** — precision/recall/confusion matrix from your held-out test set, presented cleanly with Recharts; this page is what makes reviewers trust your numbers instead of asking "on what dataset?"
4. **"Insufficient Evidence" demo case** — pin one specific case in your dataset that deliberately triggers the `human_review` / insufficient-evidence path, and lead your pitch video with it. It's your best 20 seconds.

---

## 9. Day-by-Day Plan (Aug 29 → Sep 5)

| Day | Date | Focus | Deliverable by end of day |
|---|---|---|---|
| 1 | Fri Aug 29 (today) | Repo setup, Postgres schema, FastAPI skeleton, `/cases` POST+GET working with dummy data | API returns a hardcoded case via Postman/curl |
| 2 | Sat Aug 30 | Rule Engine (all rules) + synthetic dataset generator script | 180 generated cases sitting in the DB, rules running against them |
| 3 | Sun Aug 31 | Verifier agent (Anthropic API integration) + Completeness Score + Policy Gate | Full backend pipeline runs end-to-end on one case |
| 4 | Mon Sep 1 | React scaffold, design tokens in Tailwind config, case list page | Dashboard shows real case data from the API |
| 5 | Tue Sep 2 | Case detail page (evidence trail + verdict panel + stamp animation) | Full click-through demo works locally |
| 6 | Wed Sep 3 | Run the held-out test evaluation, build the Metrics page, fix bugs, polish the "insufficient evidence" case | Numbers are real, UI is demo-ready |
| 7 | Thu Sep 4 | Record 5-min pitch video, write README, deploy (Vercel for frontend, Render/Railway for backend), final test of live links | Submission-ready |
| — | Fri Sep 5 | Submit early in the day — never submit at the deadline | Submitted |

**Cardinal rule for the week:** if you're behind schedule on any given day, cut frontend polish before you cut the rule engine, policy gate, or the honest metrics report. Those three things *are* the project. The stamp animation is nice; the deterministic rule engine is the thesis.

---

## 10. Submission Checklist

- [ ] Public GitHub repo with a clear README (problem → architecture diagram → how to run it locally → your metrics table)
- [ ] Architecture diagram (you can reuse the one in section 3 — redraw it cleanly)
- [ ] 5-minute pitch video: 30s problem framing → 2min live demo (lead with the insufficient-evidence case) → 1min architecture walkthrough → 1min metrics/honesty → 30s what you'd build next (mention the cut features here — fraud ring detection, multi-agent debate — as *deliberate* future scope)
- [ ] Live deployed link if possible (judges are far more convinced by something they can click than a video alone)
- [ ] Your one-sentence thesis (Section 0) stated explicitly in the README and said out loud in the video

Want me to write the actual `generate_dataset.py` synthetic case generator next, or scaffold the FastAPI project files so you can start running code today?
