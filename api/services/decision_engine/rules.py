"""
TruthLens Decision Engine — Rule Definitions

Each rule is a pure deterministic function.
No AI model calls. No face recognition calls.
Only consumes normalized signals from Task 1 and Task 2 outputs.
"""
from __future__ import annotations

from typing import Optional, Tuple


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# Task 1 prediction tokens
LIKELY_REAL = "LIKELY_REAL"
LIKELY_AI = "LIKELY_AI_GENERATED"
INCONCLUSIVE = "INCONCLUSIVE"

# Task 2 face result tokens
SAME_PERSON = "LIKELY_SAME_PERSON"
DIFF_PERSON = "LIKELY_DIFFERENT_PERSON"
UNABLE_VERIFY = "UNABLE_TO_VERIFY"

# Assessment categories
CAT_LIKELY_AUTHENTIC = "LIKELY_AUTHENTIC"
CAT_POTENTIAL_DEEPFAKE = "POTENTIAL_DEEPFAKE"
CAT_BOTH_SYNTHETIC = "BOTH_MEDIA_APPEAR_SYNTHETIC"
CAT_AI_DIFF_PERSON = "AI_GENERATED_MEDIA_DIFFERENT_PERSON"
CAT_SYNTH_REF_AUTH_SUS = "SYNTHETIC_REFERENCE_AUTHENTIC_SUSPECTED"
CAT_AUTH_DIFF_PERSON = "AUTHENTIC_MEDIA_DIFFERENT_PERSON"
CAT_INCONCLUSIVE = "INCONCLUSIVE"
CAT_UNABLE_TO_VERIFY = "UNABLE_TO_VERIFY"

# Risk levels
RISK_HIGH = "HIGH"
RISK_MEDIUM = "MEDIUM"
RISK_LOW = "LOW"
RISK_UNKNOWN = "UNKNOWN"

# Confidence levels
CONF_HIGH = "HIGH"
CONF_MEDIUM = "MEDIUM"
CONF_LOW = "LOW"


# ---------------------------------------------------------------------------
# Confidence derivation
# ---------------------------------------------------------------------------

def derive_confidence(
    ref_prediction: str,
    sus_prediction: str,
    face_result: str,
    ref_ai_prob: Optional[float],
    sus_ai_prob: Optional[float],
    face_score: Optional[float],
) -> str:
    """
    Derive decision-level confidence from three independent signal streams.

    HIGH   → all three signals are strong and mutually consistent
    MEDIUM → signals partially available or mildly conflicting
    LOW    → one or more critical signals missing or highly uncertain
    """
    # If any critical prediction is missing / inconclusive → LOW
    if ref_prediction == INCONCLUSIVE or sus_prediction == INCONCLUSIVE:
        return CONF_LOW

    # Face verification unavailable degrades confidence
    if face_result == UNABLE_VERIFY:
        # Without face information the classification is at best MEDIUM
        return CONF_MEDIUM

    # Measure per-signal strength
    ref_strong = ref_ai_prob is not None and (ref_ai_prob > 0.80 or ref_ai_prob < 0.20)
    sus_strong = sus_ai_prob is not None and (sus_ai_prob > 0.80 or sus_ai_prob < 0.20)
    face_strong = face_score is not None and (face_score > 0.80 or face_score < 0.40)

    strong_count = sum([ref_strong, sus_strong, face_strong])

    if strong_count == 3:
        return CONF_HIGH
    if strong_count >= 1:
        return CONF_MEDIUM
    return CONF_LOW


# ---------------------------------------------------------------------------
# Explanation builders — all generated from actual inputs
# ---------------------------------------------------------------------------

def _fmt_prob(p: Optional[float], label: str) -> str:
    if p is None:
        return ""
    return f" (AI probability: {p * 100:.1f}%)"


def _fmt_sim(s: Optional[float]) -> str:
    if s is None:
        return ""
    return f" (similarity: {s * 100:.1f}%)"


def build_explanation(
    category: str,
    ref_prediction: str,
    sus_prediction: str,
    face_result: str,
    ref_ai_prob: Optional[float],
    sus_ai_prob: Optional[float],
    face_score: Optional[float],
    face_count: Optional[int] = None,
) -> str:
    """Generate a plain-English explanation from actual signal values."""
    r_label = "authentic" if ref_prediction == LIKELY_REAL else (
        "AI-generated" if ref_prediction == LIKELY_AI else "inconclusive"
    )
    s_label = "authentic" if sus_prediction == LIKELY_REAL else (
        "AI-generated" if sus_prediction == LIKELY_AI else "inconclusive"
    )

    r_prob_str = _fmt_prob(ref_ai_prob, "reference")
    s_prob_str = _fmt_prob(sus_ai_prob, "suspected")
    sim_str = _fmt_sim(face_score)
    faces_note = ""
    if face_count is not None and face_count > 1:
        faces_note = f" ({face_count} faces detected; highest-similarity match selected.)"

    if category == CAT_LIKELY_AUTHENTIC:
        return (
            f"Both the reference{r_prob_str} and suspected{s_prob_str} media appear {r_label}. "
            f"The detected faces are likely the same person{sim_str}. "
            "No significant authenticity discrepancy was found."
        )

    if category == CAT_POTENTIAL_DEEPFAKE:
        return (
            f"The reference media appears {r_label}{r_prob_str}, while the suspected media appears "
            f"{s_label}{s_prob_str}. The detected face is highly similar to the reference{sim_str}{faces_note}. "
            "This combination is consistent with a potential deepfake, but the result is not definitive proof."
        )

    if category == CAT_BOTH_SYNTHETIC:
        face_note_both = (
            f"The detected faces are likely the same person{sim_str}." if face_result == SAME_PERSON
            else f"The detected faces appear to be different individuals{sim_str}."
        )
        return (
            f"Both the reference{r_prob_str} and suspected{s_prob_str} media appear {r_label}. "
            f"{face_note_both} "
            "Because both media are already synthetic, face similarity alone does not establish "
            "that the suspected media is a deepfake of the reference."
        )

    if category == CAT_AI_DIFF_PERSON:
        return (
            f"The reference media appears {r_label}{r_prob_str}. "
            f"The suspected media appears {s_label}{s_prob_str}, "
            f"but the detected face does not sufficiently match the reference{sim_str}{faces_note}. "
            "The suspected media does not appear to be a deepfake of the reference person."
        )

    if category == CAT_SYNTH_REF_AUTH_SUS:
        return (
            f"The reference media appears {r_label}{r_prob_str} while the suspected media appears "
            f"{s_label}{s_prob_str}. The detected faces are likely the same person{sim_str}. "
            "Because the reference itself appears AI-generated, the suspected media cannot be "
            "classified as a deepfake of an authentic reference."
        )

    if category == CAT_AUTH_DIFF_PERSON:
        return (
            f"Both the reference{r_prob_str} and suspected{s_prob_str} media appear authentic. "
            f"However, the detected faces do not sufficiently match{sim_str}{faces_note}. "
            "This is consistent with two different individuals captured in authentic media."
        )

    if category == CAT_INCONCLUSIVE:
        if face_result == UNABLE_VERIFY:
            return (
                f"The reference media appears {r_label}{r_prob_str} and the suspected media appears "
                f"{s_label}{s_prob_str}. However, face verification could not be completed, "
                "so a relationship between the two identities cannot be established."
            )
        return (
            "The available AI authenticity and face-verification signals are insufficient "
            "or contradictory to form a reliable contextual assessment."
        )

    if category == CAT_UNABLE_TO_VERIFY:
        return (
            "One or more required analysis components could not produce a usable result. "
            "The assessment cannot be determined from the available evidence."
        )

    return "Assessment could not be determined."


# ---------------------------------------------------------------------------
# Main rule engine (priority-ordered)
# ---------------------------------------------------------------------------

def apply_rules(
    ref_prediction: str,
    sus_prediction: str,
    face_result: str,
    ref_ai_prob: Optional[float],
    sus_ai_prob: Optional[float],
    face_score: Optional[float],
    face_count: Optional[int] = None,
) -> Tuple[str, str]:
    """
    Apply priority-ordered rules to determine (category, risk_level).

    Priority order (highest first):
      1. Missing / failed analysis → UNABLE_TO_VERIFY
      2. Either prediction inconclusive → INCONCLUSIVE
      3. Face verification unable → INCONCLUSIVE (modified explanation)
      4. Both media synthetic → BOTH_MEDIA_APPEAR_SYNTHETIC
      5. Real + AI + Same person → POTENTIAL_DEEPFAKE
      6. Real + AI + Different person → AI_GENERATED_MEDIA_DIFFERENT_PERSON
      7. Synthetic ref + Authentic suspected + Same → SYNTHETIC_REFERENCE_AUTHENTIC_SUSPECTED
      8. Both real + Same → LIKELY_AUTHENTIC
      9. Both real + Different → AUTHENTIC_MEDIA_DIFFERENT_PERSON
     10. Fallthrough → INCONCLUSIVE
    """

    # Rule 1 — Missing / null predictions (failed analysis)
    if not ref_prediction or not sus_prediction:
        return CAT_UNABLE_TO_VERIFY, RISK_UNKNOWN

    # Rule 2 — Either authenticity result is inconclusive
    if ref_prediction == INCONCLUSIVE or sus_prediction == INCONCLUSIVE:
        return CAT_INCONCLUSIVE, RISK_UNKNOWN

    # Rule 3 — Face verification unavailable (cannot correlate identity)
    if face_result == UNABLE_VERIFY or face_result is None:
        return CAT_INCONCLUSIVE, RISK_UNKNOWN

    # Rule 4 — Both media appear synthetic
    if ref_prediction == LIKELY_AI and sus_prediction == LIKELY_AI:
        return CAT_BOTH_SYNTHETIC, RISK_MEDIUM

    # Rule 5 — POTENTIAL DEEPFAKE: real reference + AI suspected + same person
    if ref_prediction == LIKELY_REAL and sus_prediction == LIKELY_AI and face_result == SAME_PERSON:
        return CAT_POTENTIAL_DEEPFAKE, RISK_HIGH

    # Rule 6 — AI suspected but different person → not a deepfake of reference
    if ref_prediction == LIKELY_REAL and sus_prediction == LIKELY_AI and face_result == DIFF_PERSON:
        return CAT_AI_DIFF_PERSON, RISK_LOW

    # Rule 7 — Synthetic reference + authentic suspected
    if ref_prediction == LIKELY_AI and sus_prediction == LIKELY_REAL:
        return CAT_SYNTH_REF_AUTH_SUS, RISK_LOW

    # Rule 8 — Both authentic + same person
    if ref_prediction == LIKELY_REAL and sus_prediction == LIKELY_REAL and face_result == SAME_PERSON:
        return CAT_LIKELY_AUTHENTIC, RISK_LOW

    # Rule 9 — Both authentic + different person
    if ref_prediction == LIKELY_REAL and sus_prediction == LIKELY_REAL and face_result == DIFF_PERSON:
        return CAT_AUTH_DIFF_PERSON, RISK_LOW

    # Rule 10 — Any remaining combination → INCONCLUSIVE
    return CAT_INCONCLUSIVE, RISK_UNKNOWN
