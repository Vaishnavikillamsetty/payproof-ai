"""
Verifier Agent — verifies one claim against available evidence.

Modes:
  MOCK_VERIFIER=true  -> deterministic local mock verifier (no API cost)
  MOCK_VERIFIER=false -> real Anthropic API verifier
"""

import json
import logging
import re

import anthropic

from app.config import settings

logger = logging.getLogger(__name__)


VERIFIER_PROMPT = """\
You are a claims verifier for a payment dispute case.

Given a claim and the evidence records below, output ONLY valid JSON.
Do not include a preamble, markdown fences, or any text outside JSON.

Claim: {claim_text}

Evidence:
{evidence_json}

Return EXACTLY this JSON shape:

{{
  "verdict": "supported" | "contradicted" | "unverifiable",
  "confidence": <float between 0.0 and 1.0>,
  "reasoning": "<one sentence, plain language>"
}}
"""


VALID_VERDICTS = {
    "supported",
    "contradicted",
    "unverifiable",
}


class VerifierParseError(Exception):
    """Raised when verifier output is invalid."""


# ============================================================
# MOCK VERIFIER
# ============================================================

def mock_verify_claim(claim_text: str, evidence: list[dict]) -> dict:
    """
    Deterministic local verifier used when MOCK_VERIFIER=true.

    This does NOT call an LLM.
    It exists so the complete pipeline can be tested without API credits.
    """

    claim_lower = claim_text.lower()

    if not evidence:
        return {
            "verdict": "unverifiable",
            "confidence": 0.0,
            "reasoning": "No evidence records are available to verify this claim.",
        }

    # --------------------------------------------------------
    # Product delivered claim
    # --------------------------------------------------------
    if "product was delivered" in claim_lower:

        deliveries = [
            e for e in evidence
            if e.get("evidence_type") == "delivery"
        ]

        if not deliveries:
            return {
                "verdict": "unverifiable",
                "confidence": 0.3,
                "reasoning": "No delivery evidence was found.",
            }

        for delivery in deliveries:
            content = delivery.get("content", {})

            if content.get("status") == "delivered":
                return {
                    "verdict": "supported",
                    "confidence": 0.9,
                    "reasoning": "Delivery evidence shows the product was delivered.",
                }

            if content.get("status") == "lost_in_transit":
                return {
                    "verdict": "contradicted",
                    "confidence": 0.9,
                    "reasoning": "Delivery evidence shows the product was lost in transit.",
                }

    # --------------------------------------------------------
    # Transaction authorization claim
    # --------------------------------------------------------
    if "transaction was authorized" in claim_lower:

        otp_records = [
            e for e in evidence
            if e.get("evidence_type") == "otp"
        ]

        if not otp_records:
            return {
                "verdict": "unverifiable",
                "confidence": 0.3,
                "reasoning": "No OTP verification evidence was found.",
            }

        for otp in otp_records:
            content = otp.get("content", {})

            if content.get("verified") is True:
                return {
                    "verdict": "supported",
                    "confidence": 0.9,
                    "reasoning": "OTP verification was successfully completed.",
                }

            if content.get("verified") is False:
                return {
                    "verdict": "contradicted",
                    "confidence": 0.9,
                    "reasoning": "OTP verification was not successful.",
                }

    # --------------------------------------------------------
    # Duplicate charge claim
    # --------------------------------------------------------
    if "charged more than once" in claim_lower:

        payments = [
            e for e in evidence
            if e.get("evidence_type") == "payment"
        ]

        if len(payments) >= 2:
            return {
                "verdict": "supported",
                "confidence": 0.9,
                "reasoning": "Multiple payment records were found.",
            }

        return {
            "verdict": "contradicted",
            "confidence": 0.85,
            "reasoning": "Only one payment record was found.",
        }

    # --------------------------------------------------------
    # Subscription cancellation claim
    # --------------------------------------------------------
    if "requested cancellation" in claim_lower:

        communications = [
            e for e in evidence
            if e.get("evidence_type") == "communication"
        ]

        for communication in communications:

            content = communication.get("content", {})
            message = str(content.get("message", "")).lower()

            if "cancel" in message:
                return {
                    "verdict": "supported",
                    "confidence": 0.8,
                    "reasoning": "Communication evidence contains a cancellation request.",
                }

        return {
            "verdict": "unverifiable",
            "confidence": 0.3,
            "reasoning": "No cancellation communication was found.",
        }

    # --------------------------------------------------------
    # Product matches description claim
    # --------------------------------------------------------
    if "matched the merchant" in claim_lower:

        communications = [
            e for e in evidence
            if e.get("evidence_type") == "communication"
        ]

        if not communications:
            return {
                "verdict": "unverifiable",
                "confidence": 0.3,
                "reasoning": "No communication or product comparison evidence was found.",
            }

        return {
            "verdict": "unverifiable",
            "confidence": 0.5,
            "reasoning": "Available evidence is insufficient to determine whether the product matched the description.",
        }

    # --------------------------------------------------------
    # Amount matches payment claim
    # --------------------------------------------------------
    if "disputed amount" in claim_lower and "matches the payment record" in claim_lower:

        payments = [
            e for e in evidence
            if e.get("evidence_type") == "payment"
        ]

        if not payments:
            return {
                "verdict": "unverifiable",
                "confidence": 0.0,
                "reasoning": "No payment evidence was found.",
            }

        return {
            "verdict": "supported",
            "confidence": 0.7,
            "reasoning": "A payment record is available for verification.",
        }

    # Default
    return {
        "verdict": "unverifiable",
        "confidence": 0.2,
        "reasoning": "The available evidence is insufficient to verify the claim.",
    }


# ============================================================
# REAL ANTHROPIC VERIFIER
# ============================================================

def _verify_with_anthropic(
    claim_text: str,
    evidence: list[dict]
) -> dict:

    if not settings.anthropic_api_key:
        raise VerifierParseError(
            "ANTHROPIC_API_KEY is missing."
        )

    client = anthropic.Anthropic(
        api_key=settings.anthropic_api_key
    )

    prompt = VERIFIER_PROMPT.format(
        claim_text=claim_text,
        evidence_json=json.dumps(
            evidence,
            default=str,
            indent=2
        ),
    )

    try:
        message = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=300,
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ],
        )
    except anthropic.APIError as exc:
        logger.error(
            "Anthropic API error: %s",
            exc
        )

        raise VerifierParseError(
            f"Anthropic API error: {exc}"
        ) from exc

    raw_text = message.content[0].text.strip()

    # Remove accidental markdown fences
    fence_match = re.search(
        r"```(?:json)?\s*([\s\S]*?)\s*```",
        raw_text
    )

    if fence_match:
        raw_text = fence_match.group(1).strip()

    # Parse JSON
    try:
        result = json.loads(raw_text)

    except json.JSONDecodeError as exc:

        logger.error(
            "Verifier returned invalid JSON: %r",
            raw_text
        )

        raise VerifierParseError(
            f"LLM returned invalid JSON: {raw_text!r}"
        ) from exc

    # Validate structure
    verdict = result.get("verdict")
    confidence = result.get("confidence")
    reasoning = result.get("reasoning")

    if verdict not in VALID_VERDICTS:
        raise VerifierParseError(
            f"Invalid verdict: {verdict!r}"
        )

    if (
        not isinstance(confidence, (int, float))
        or not 0.0 <= float(confidence) <= 1.0
    ):
        raise VerifierParseError(
            f"Invalid confidence: {confidence!r}"
        )

    if not isinstance(reasoning, str) or not reasoning.strip():
        raise VerifierParseError(
            "Missing or empty reasoning."
        )

    return {
        "verdict": verdict,
        "confidence": float(confidence),
        "reasoning": reasoning.strip(),
    }


# ============================================================
# PUBLIC VERIFIER
# ============================================================

def verify_claim(
    claim_text: str,
    evidence: list[dict]
) -> dict:
    """
    Verify one claim.

    Uses the mock verifier locally when MOCK_VERIFIER=true.
    Otherwise calls Anthropic.
    """

    if settings.mock_verifier:

        logger.info(
            "Using MOCK verifier for claim: %s",
            claim_text
        )

        return mock_verify_claim(
            claim_text,
            evidence
        )

    return _verify_with_anthropic(
        claim_text,
        evidence
    )