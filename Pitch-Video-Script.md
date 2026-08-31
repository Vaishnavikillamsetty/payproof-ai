# PayProof AI — 5-Minute Pitch Video Script

General notes before you record:
- Practice out loud 2-3 times before recording — don't read it word for word on camera, know the beats.
- Screen-record the actual live site for the demo section, with your face optional (voiceover is fine).
- Keep a stopwatch running once — this script is timed to land at ~5:00. If you're rushed, cut from Section 5 first, never Section 3.

---

## 1. The problem (0:00–0:30)

**Say:**
"When a customer disputes a payment — 'I never received this,' 'I was charged twice' — the evidence that actually proves or disproves that claim is scattered across systems: payment records, delivery confirmation, OTP logs, support chats. Merchants either respond too slowly and lose the dispute automatically, or respond with weak evidence and lose it anyway. The obvious fix is 'let AI decide' — but a confidently wrong AI decision is worse than a slow human one. That's the problem I built PayProof AI to solve."

---

## 2. The thesis, stated explicitly (0:30–1:00)

**Say, and consider putting this exact line on screen as text:**
"PayProof AI doesn't ask an LLM whether a transaction is fraudulent. It collects evidence, checks it against deterministic rules, has the LLM verify individual claims with a confidence score, scores how complete the evidence is, and only auto-drafts a response if all of that clears a bar — otherwise it says so honestly and routes to a human."

This is your one sentence. Say it clearly and don't rush it — it's the thing you want a judge to remember.

---

## 3. Live demo — lead with the strongest case (1:00–3:00)

**Case A — the contradiction override (lead with this one):**
Submit `DEMO_TXN_REVIEW_1`, reason "product not received."

**Say while it processes:**
"Watch what happens here. This case has a payment record and a delivery record — completeness score of 60 out of 60, and the LLM verifier is 80% confident. By the numbers alone, this should auto-resolve."

**When the result shows human_review:**
"But it doesn't. Why? Because the customer's claim — 'I didn't receive it' — directly contradicts the delivery record, which shows it was signed for. My deterministic rule engine catches that contradiction and overrides the score, no matter how confident the LLM was. This is the core safety guarantee of the system: high confidence never overrides a hard contradiction."

**Case B — proving it can say yes:**
Submit `DEMO_TXN_STRONG_1`, reason "subscription not cancelled."

**Say:**
"Now the opposite case — full evidence, no contradictions. The system confidently auto-resolves. It's not just cautious by default — it acts when it actually has grounds to."

**Case C — brief, insufficient evidence:**
Submit `DEMO_TXN_EMPTY_1`.

**Say:**
"And when there's no evidence at all, it says exactly that — insufficient evidence, human review required — instead of guessing."

---

## 4. Architecture, quickly (3:00–3:45)

Show the pipeline diagram from the README (dispute → evidence collector → rule engine → verifier → completeness score → policy gate → audit log).

**Say:**
"Evidence comes from a seeded database standing in for four real systems — payment gateway, courier, OTP service, merchant chat — architecturally identical to how it would query real APIs in production, and clearly labeled as demo data in the UI so it's never mistaken for something live. The LLM's role is narrow and explicit: it verifies individual claims and drafts responses. It never makes the final routing decision — that's owned by the deterministic rule engine and the policy gate."

---

## 5. Honest metrics (3:45–4:30)

Show the Metrics page.

**Say:**
"On a held-out set of 30 labeled test cases: 100% recall, and zero unsafe auto-resolves — the system never once let an ambiguous case through as automated. The tradeoff is precision — 42% — because it's conservative: 15 legitimate cases were unnecessarily flagged for human review. I'm stating that plainly rather than hiding it, because in a risk system, an unnecessary review costs a few minutes; an unsafe automated decision costs real money and trust. That's the right tradeoff to start from, and threshold tuning is the clear next lever to pull to improve precision without reintroducing unsafe resolves."

---

## 6. What's next / close (4:30–5:00)

**Say:**
"Scoped deliberately for this build: real payment gateway and courier integrations in place of the seeded demo data, multi-agent evidence debate for ambiguous cases, and fraud-ring detection across multiple disputes. All of that fits into the same architecture without changing the core safety guarantee — evidence first, deterministic rules as a hard floor, and the AI never deciding alone. Thanks for watching."

---

## Quick checklist before you hit record

- [ ] All 4 demo transaction IDs tested once right before recording (data can shift if you re-seed)
- [ ] Metrics page numbers match what you say out loud
- [ ] Screen resolution/zoom level makes text readable on a small screen
- [ ] Total run-time close to 5:00 — trim Section 6 first if you're running long, never Section 3
