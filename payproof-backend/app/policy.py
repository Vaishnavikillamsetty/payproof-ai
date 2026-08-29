"""
Completeness Score and Policy Gate — deterministic, no LLM.

These two functions are the heart of "bounded autonomy":
  - completeness_score() returns (int 0-100, list[str] missing types)
  - policy_decision() returns (status str, reason str)

Neither function makes any external call.
"""

# --------------------------------------------------------------------------- #
# Section 6.3 — Completeness Score                                            #
# --------------------------------------------------------------------------- #
CRITICAL_EVIDENCE = {
    "payment": 30,
    "delivery": 30,
    "otp": 20,
    "communication": 20,
}


def completeness_score(evidence_list) -> tuple[int, list[str]]:
    """
    Score how complete the evidence set is (0–100).

    Returns:
        score   – integer 0-100
        missing – list of evidence type names that were absent
    """
    present_types = {e.evidence_type for e in evidence_list}
    score = sum(
        weight
        for etype, weight in CRITICAL_EVIDENCE.items()
        if etype in present_types
    )
    missing = [etype for etype in CRITICAL_EVIDENCE if etype not in present_types]
    return score, missing


# --------------------------------------------------------------------------- #
# Section 6.4 — Policy Gate                                                   #
# --------------------------------------------------------------------------- #
COMPLETENESS_THRESHOLD = 70   # tunable against dev set
CONFIDENCE_THRESHOLD = 0.75   # tunable against dev set
MIN_COMPLETENESS = 40          # below this, always human review


def policy_decision(
    completeness: int,
    avg_confidence: float,
    contradictions_found: bool,
) -> tuple[str, str]:
    """
    Deterministic threshold check — decides case status.

    Returns:
        status – "strong_case" | "weak_case" | "human_review"
        reason – plain-language explanation
    """
    if contradictions_found:
        return "human_review", "Contradicting evidence detected — do not auto-respond"
    if completeness >= COMPLETENESS_THRESHOLD and avg_confidence >= CONFIDENCE_THRESHOLD:
        return "strong_case", "Auto-draft approved: evidence complete and confidence high"
    if completeness < MIN_COMPLETENESS:
        return "human_review", "Insufficient evidence — do not auto-respond"
    return "weak_case", "Borderline case — recommend human review before response"
