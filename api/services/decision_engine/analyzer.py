"""
TruthLens Decision Engine — Orchestrator

Consumes the raw Task 1 (authenticity) and Task 2 (face verification) dicts
that are already present in the /analyze/compare response payload.
Does NOT call any AI model or face recognition service.
"""
from __future__ import annotations

import logging
from typing import Any, Dict, Optional

from .rules import (
    apply_rules,
    build_explanation,
    derive_confidence,
    UNABLE_VERIFY,
    CAT_UNABLE_TO_VERIFY,
    CAT_INCONCLUSIVE,
    RISK_UNKNOWN,
    CONF_LOW,
    INCONCLUSIVE,
)
from .schemas import AssessmentResult, EvidenceSignals

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Helpers — safely extract fields from existing Task 1/2 dicts
# ---------------------------------------------------------------------------

def _safe_str(d: Optional[Dict], key: str, default: str = "") -> str:
    if not d:
        return default
    return str(d.get(key, default))


def _safe_float(d: Optional[Dict], key: str) -> Optional[float]:
    if not d:
        return None
    v = d.get(key)
    try:
        return float(v) if v is not None else None
    except (TypeError, ValueError):
        return None


def _safe_int(d: Optional[Dict], key: str) -> Optional[int]:
    if not d:
        return None
    v = d.get(key)
    try:
        return int(v) if v is not None else None
    except (TypeError, ValueError):
        return None


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def run_decision_engine(
    reference_analysis: Optional[Dict[str, Any]],
    suspected_analysis: Optional[Dict[str, Any]],
    face_verification: Optional[Dict[str, Any]],
) -> AssessmentResult:
    """
    Run the TruthLens Decision Engine.

    Parameters
    ----------
    reference_analysis  : dict produced by Task 1 for the reference media
    suspected_analysis  : dict produced by Task 1 for the suspected media
    face_verification   : dict produced by Task 2

    Returns
    -------
    AssessmentResult with category, risk_level, confidence, explanation, signals
    """

    # --- Extract signals from Task 1 ---
    ref_status = _safe_str(reference_analysis, "status")
    sus_status = _safe_str(suspected_analysis, "status")

    ref_prediction = _safe_str(reference_analysis, "prediction", INCONCLUSIVE)
    sus_prediction = _safe_str(suspected_analysis, "prediction", INCONCLUSIVE)
    ref_ai_prob = _safe_float(reference_analysis, "ai_probability")
    sus_ai_prob = _safe_float(suspected_analysis, "ai_probability")

    # Mark as INCONCLUSIVE when analysis itself failed
    if ref_status == "failed" or not ref_prediction:
        ref_prediction = INCONCLUSIVE
    if sus_status == "failed" or not sus_prediction:
        sus_prediction = INCONCLUSIVE

    # --- Extract signals from Task 2 ---
    face_result = _safe_str(face_verification, "result", UNABLE_VERIFY)
    face_score = _safe_float(face_verification, "best_match_score")
    face_match = face_verification.get("match") if face_verification else None
    suspected_faces_count = _safe_int(face_verification, "suspected_faces_count")

    # Guard against unexpected token values
    if not face_result:
        face_result = UNABLE_VERIFY

    logger.debug(
        "Decision Engine inputs — ref:%s sus:%s face:%s score:%.3f",
        ref_prediction, sus_prediction, face_result, face_score or 0.0,
    )

    # --- Apply priority-ordered rules ---
    category, risk_level = apply_rules(
        ref_prediction=ref_prediction,
        sus_prediction=sus_prediction,
        face_result=face_result,
        ref_ai_prob=ref_ai_prob,
        sus_ai_prob=sus_ai_prob,
        face_score=face_score,
        face_count=suspected_faces_count,
    )

    # --- Derive overall confidence ---
    confidence = derive_confidence(
        ref_prediction=ref_prediction,
        sus_prediction=sus_prediction,
        face_result=face_result,
        ref_ai_prob=ref_ai_prob,
        sus_ai_prob=sus_ai_prob,
        face_score=face_score,
    )

    # --- Generate human-readable explanation from actual values ---
    explanation = build_explanation(
        category=category,
        ref_prediction=ref_prediction,
        sus_prediction=sus_prediction,
        face_result=face_result,
        ref_ai_prob=ref_ai_prob,
        sus_ai_prob=sus_ai_prob,
        face_score=face_score,
        face_count=suspected_faces_count,
    )

    # --- Assemble transparent evidence signals ---
    signals = EvidenceSignals(
        reference_authenticity=ref_prediction,
        suspected_authenticity=sus_prediction,
        face_verification=face_result,
        reference_ai_probability=ref_ai_prob,
        suspected_ai_probability=sus_ai_prob,
        face_similarity_score=face_score,
        face_match=face_match,
    )

    return AssessmentResult(
        category=category,
        risk_level=risk_level,
        confidence=confidence,
        explanation=explanation,
        signals=signals,
    )
