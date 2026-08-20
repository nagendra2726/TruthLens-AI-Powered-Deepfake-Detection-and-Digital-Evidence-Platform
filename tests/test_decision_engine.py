"""
TruthLens — Decision Engine Unit Tests

Tests every major decision combination as specified in Task 3.
The Decision Engine is pure Python — no model calls, no HTTP calls.
"""
import sys
import os

# Allow running from repo root or tests/ directory
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "api"))

import pytest
from services.decision_engine import (
    run_decision_engine,
    CAT_LIKELY_AUTHENTIC,
    CAT_POTENTIAL_DEEPFAKE,
    CAT_BOTH_SYNTHETIC,
    CAT_AI_DIFF_PERSON,
    CAT_SYNTH_REF_AUTH_SUS,
    CAT_AUTH_DIFF_PERSON,
    CAT_INCONCLUSIVE,
    CAT_UNABLE_TO_VERIFY,
    RISK_HIGH,
    RISK_MEDIUM,
    RISK_LOW,
    RISK_UNKNOWN,
)

# ---------------------------------------------------------------------------
# Helpers for building mock analysis dicts matching Task 1/2 schemas
# ---------------------------------------------------------------------------

def make_auth(prediction: str, ai_prob: float) -> dict:
    return {
        "status": "completed",
        "prediction": prediction,
        "ai_probability": ai_prob,
        "real_probability": round(1.0 - ai_prob, 4),
        "confidence": "HIGH",
    }


def make_face(result: str, score: float = 0.88, match: bool = True, count: int = 1) -> dict:
    return {
        "status": "completed",
        "reference_face_detected": True,
        "suspected_face_detected": True,
        "reference_faces_count": 1,
        "suspected_faces_count": count,
        "best_match_score": score,
        "best_match_face_index": 1,
        "match": match,
        "result": result,
        "threshold_used": 0.65,
        "message": None,
    }


def make_face_unable() -> dict:
    return {
        "status": "unable_to_verify",
        "reference_face_detected": False,
        "suspected_face_detected": False,
        "reference_faces_count": 0,
        "suspected_faces_count": 0,
        "best_match_score": None,
        "best_match_face_index": None,
        "match": None,
        "result": "UNABLE_TO_VERIFY",
        "threshold_used": 0.65,
        "message": "No usable face detected.",
    }


def make_inconclusive_auth() -> dict:
    return {
        "status": "completed",
        "prediction": "INCONCLUSIVE",
        "ai_probability": 0.50,
        "real_probability": 0.50,
        "confidence": "LOW",
    }


# ---------------------------------------------------------------------------
# TEST 1: Real + Real + Same → LIKELY_AUTHENTIC
# ---------------------------------------------------------------------------
def test_real_real_same_person():
    result = run_decision_engine(
        reference_analysis=make_auth("LIKELY_REAL", 0.05),
        suspected_analysis=make_auth("LIKELY_REAL", 0.04),
        face_verification=make_face("LIKELY_SAME_PERSON", score=0.95),
    )
    assert result.category == CAT_LIKELY_AUTHENTIC
    assert result.risk_level == RISK_LOW
    assert len(result.explanation) > 0
    assert result.signals.face_verification == "LIKELY_SAME_PERSON"


# ---------------------------------------------------------------------------
# TEST 2: Real + AI + Same → POTENTIAL_DEEPFAKE
# ---------------------------------------------------------------------------
def test_real_ai_same_person():
    result = run_decision_engine(
        reference_analysis=make_auth("LIKELY_REAL", 0.04),
        suspected_analysis=make_auth("LIKELY_AI_GENERATED", 0.96),
        face_verification=make_face("LIKELY_SAME_PERSON", score=0.94),
    )
    assert result.category == CAT_POTENTIAL_DEEPFAKE
    assert result.risk_level == RISK_HIGH
    assert "authentic" in result.explanation.lower() or "real" in result.explanation.lower()
    assert result.signals.suspected_authenticity == "LIKELY_AI_GENERATED"


# ---------------------------------------------------------------------------
# TEST 3: AI + AI + Same → BOTH_MEDIA_APPEAR_SYNTHETIC
# ---------------------------------------------------------------------------
def test_ai_ai_same_person():
    result = run_decision_engine(
        reference_analysis=make_auth("LIKELY_AI_GENERATED", 0.95),
        suspected_analysis=make_auth("LIKELY_AI_GENERATED", 0.93),
        face_verification=make_face("LIKELY_SAME_PERSON", score=0.88),
    )
    assert result.category == CAT_BOTH_SYNTHETIC
    assert result.risk_level == RISK_MEDIUM
    # Must NOT say "deepfake detected"
    assert "deepfake detected" not in result.explanation.lower()


# ---------------------------------------------------------------------------
# TEST 4: Real + AI + Different → AI_GENERATED_MEDIA_DIFFERENT_PERSON
# ---------------------------------------------------------------------------
def test_real_ai_different_person():
    result = run_decision_engine(
        reference_analysis=make_auth("LIKELY_REAL", 0.06),
        suspected_analysis=make_auth("LIKELY_AI_GENERATED", 0.91),
        face_verification=make_face("LIKELY_DIFFERENT_PERSON", score=0.21, match=False),
    )
    assert result.category == CAT_AI_DIFF_PERSON
    assert result.risk_level == RISK_LOW
    # Must NOT say "deepfake detected"
    assert "deepfake detected" not in result.explanation.lower()


# ---------------------------------------------------------------------------
# TEST 5: AI + Real + Same → SYNTHETIC_REFERENCE_AUTHENTIC_SUSPECTED
# ---------------------------------------------------------------------------
def test_ai_ref_real_suspected_same_person():
    result = run_decision_engine(
        reference_analysis=make_auth("LIKELY_AI_GENERATED", 0.92),
        suspected_analysis=make_auth("LIKELY_REAL", 0.03),
        face_verification=make_face("LIKELY_SAME_PERSON", score=0.87),
    )
    assert result.category == CAT_SYNTH_REF_AUTH_SUS
    assert result.risk_level == RISK_LOW


# ---------------------------------------------------------------------------
# TEST 6: Real + Real + Different → AUTHENTIC_MEDIA_DIFFERENT_PERSON
# ---------------------------------------------------------------------------
def test_real_real_different_person():
    result = run_decision_engine(
        reference_analysis=make_auth("LIKELY_REAL", 0.04),
        suspected_analysis=make_auth("LIKELY_REAL", 0.07),
        face_verification=make_face("LIKELY_DIFFERENT_PERSON", score=0.18, match=False),
    )
    assert result.category == CAT_AUTH_DIFF_PERSON
    assert result.risk_level == RISK_LOW
    # Not a deepfake
    assert "deepfake" not in result.explanation.lower()


# ---------------------------------------------------------------------------
# TEST 7: Inconclusive reference + AI suspected + Same → INCONCLUSIVE
# ---------------------------------------------------------------------------
def test_inconclusive_ref_ai_sus_same():
    result = run_decision_engine(
        reference_analysis=make_inconclusive_auth(),
        suspected_analysis=make_auth("LIKELY_AI_GENERATED", 0.91),
        face_verification=make_face("LIKELY_SAME_PERSON", score=0.88),
    )
    assert result.category == CAT_INCONCLUSIVE
    assert result.risk_level == RISK_UNKNOWN


# ---------------------------------------------------------------------------
# TEST 8: Real + AI + Unable To Verify → INCONCLUSIVE
# ---------------------------------------------------------------------------
def test_real_ai_unable_to_verify_face():
    result = run_decision_engine(
        reference_analysis=make_auth("LIKELY_REAL", 0.04),
        suspected_analysis=make_auth("LIKELY_AI_GENERATED", 0.95),
        face_verification=make_face_unable(),
    )
    assert result.category == CAT_INCONCLUSIVE
    assert result.risk_level == RISK_UNKNOWN
    # Must NOT call it deepfake
    assert "deepfake" not in result.explanation.lower()


# ---------------------------------------------------------------------------
# TEST 9: AI + AI + Different → BOTH_MEDIA_APPEAR_SYNTHETIC
# ---------------------------------------------------------------------------
def test_ai_ai_different_person():
    result = run_decision_engine(
        reference_analysis=make_auth("LIKELY_AI_GENERATED", 0.90),
        suspected_analysis=make_auth("LIKELY_AI_GENERATED", 0.88),
        face_verification=make_face("LIKELY_DIFFERENT_PERSON", score=0.15, match=False),
    )
    assert result.category == CAT_BOTH_SYNTHETIC
    assert result.risk_level == RISK_MEDIUM
    # Must NOT call it deepfake
    assert "deepfake detected" not in result.explanation.lower()


# ---------------------------------------------------------------------------
# EDGE CASES
# ---------------------------------------------------------------------------

def test_none_reference_analysis():
    result = run_decision_engine(
        reference_analysis=None,
        suspected_analysis=make_auth("LIKELY_AI_GENERATED", 0.91),
        face_verification=make_face("LIKELY_SAME_PERSON", score=0.88),
    )
    assert result.category in (CAT_INCONCLUSIVE, CAT_UNABLE_TO_VERIFY)


def test_none_suspected_analysis():
    result = run_decision_engine(
        reference_analysis=make_auth("LIKELY_REAL", 0.04),
        suspected_analysis=None,
        face_verification=make_face("LIKELY_SAME_PERSON", score=0.88),
    )
    assert result.category in (CAT_INCONCLUSIVE, CAT_UNABLE_TO_VERIFY)


def test_none_face_verification():
    result = run_decision_engine(
        reference_analysis=make_auth("LIKELY_REAL", 0.04),
        suspected_analysis=make_auth("LIKELY_AI_GENERATED", 0.91),
        face_verification=None,
    )
    assert result.category == CAT_INCONCLUSIVE


def test_failed_reference_analysis():
    result = run_decision_engine(
        reference_analysis={"status": "failed", "error": "Model unavailable"},
        suspected_analysis=make_auth("LIKELY_AI_GENERATED", 0.91),
        face_verification=make_face("LIKELY_SAME_PERSON", score=0.88),
    )
    assert result.category in (CAT_INCONCLUSIVE, CAT_UNABLE_TO_VERIFY)


def test_disclaimer_always_present():
    """Every assessment must carry a disclaimer."""
    result = run_decision_engine(
        reference_analysis=make_auth("LIKELY_REAL", 0.04),
        suspected_analysis=make_auth("LIKELY_AI_GENERATED", 0.96),
        face_verification=make_face("LIKELY_SAME_PERSON", score=0.94),
    )
    assert result.disclaimer
    assert "should not be treated" in result.disclaimer.lower()


def test_no_hardcoded_filename_dependency():
    """Decision Engine must be deterministic based on predictions, not filenames."""
    r1 = run_decision_engine(
        reference_analysis={**make_auth("LIKELY_REAL", 0.05), "filename": "real_alice.jpg"},
        suspected_analysis={**make_auth("LIKELY_AI_GENERATED", 0.95), "filename": "fake_alice.png"},
        face_verification=make_face("LIKELY_SAME_PERSON", score=0.92),
    )
    r2 = run_decision_engine(
        reference_analysis={**make_auth("LIKELY_REAL", 0.05), "filename": "unknown_file_xyz.mp4"},
        suspected_analysis={**make_auth("LIKELY_AI_GENERATED", 0.95), "filename": "another_unknown.jpg"},
        face_verification=make_face("LIKELY_SAME_PERSON", score=0.92),
    )
    assert r1.category == r2.category, "Category must not depend on filenames"
    assert r1.risk_level == r2.risk_level


def test_multi_face_suspected():
    """Multi-face suspicious media must still work correctly."""
    result = run_decision_engine(
        reference_analysis=make_auth("LIKELY_REAL", 0.05),
        suspected_analysis=make_auth("LIKELY_AI_GENERATED", 0.93),
        face_verification=make_face("LIKELY_SAME_PERSON", score=0.91, count=3),
    )
    assert result.category == CAT_POTENTIAL_DEEPFAKE
    assert result.signals.face_similarity_score == pytest.approx(0.91)


def test_explanation_not_empty_for_all_categories():
    """Every possible category must generate a non-empty explanation."""
    cases = [
        (make_auth("LIKELY_REAL", 0.05), make_auth("LIKELY_REAL", 0.04), make_face("LIKELY_SAME_PERSON")),
        (make_auth("LIKELY_REAL", 0.05), make_auth("LIKELY_AI_GENERATED", 0.95), make_face("LIKELY_SAME_PERSON")),
        (make_auth("LIKELY_AI_GENERATED", 0.92), make_auth("LIKELY_AI_GENERATED", 0.91), make_face("LIKELY_SAME_PERSON")),
        (make_auth("LIKELY_REAL", 0.05), make_auth("LIKELY_AI_GENERATED", 0.91), make_face("LIKELY_DIFFERENT_PERSON", score=0.20, match=False)),
        (make_auth("LIKELY_AI_GENERATED", 0.92), make_auth("LIKELY_REAL", 0.04), make_face("LIKELY_SAME_PERSON")),
        (make_auth("LIKELY_REAL", 0.05), make_auth("LIKELY_REAL", 0.04), make_face("LIKELY_DIFFERENT_PERSON", score=0.18, match=False)),
        (make_inconclusive_auth(), make_auth("LIKELY_AI_GENERATED", 0.91), make_face("LIKELY_SAME_PERSON")),
        (make_auth("LIKELY_REAL", 0.05), make_auth("LIKELY_AI_GENERATED", 0.95), make_face_unable()),
    ]
    for ref, sus, face in cases:
        result = run_decision_engine(ref, sus, face)
        assert result.explanation.strip(), f"Empty explanation for category {result.category}"
