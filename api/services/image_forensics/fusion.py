"""
TruthLens — Evidence Fusion & Signal Agreement Engine
Combines AI model ensemble predictions with pixel-level forensic scores.
Detects signal disagreement and modulates assessment confidence.
"""
from __future__ import annotations

from typing import Tuple
from .schemas import (
    EvidenceFusionResult,
    NoiseSignals,
    TextureSignals,
    ColorSignals,
    EdgeSignals,
    FrequencySignals,
    SignalAgreement,
)

# Configurable default weights (AI Ensemble: 70%, Pixel Forensics: 30%)
DEFAULT_AI_MODEL_WEIGHT = 0.70
DEFAULT_FORENSIC_WEIGHT = 0.30


def compute_forensic_score(
    noise: NoiseSignals,
    texture: TextureSignals,
    color: ColorSignals,
    edges: EdgeSignals,
    frequency: FrequencySignals,
) -> Tuple[float, str]:
    """
    Computes an empirical statistical forensic score from physical pixel signals.
    Combines noise residual, micro-texture entropy, edge distribution, and FFT spectral energy.
    0.0 -> Highly Authentic / Photographic
    1.0 -> Highly Synthetic / AI-Generated
    """
    # 1. Texture naturalness: Real photos have high LBP entropy (5.0 - 7.5). Synthetic < 4.0
    texture_synthetic = 1.0 - min(1.0, max(0.0, (texture.lbp_entropy - 3.5) / 3.5))

    # 2. Chrominance richness: Real photos have rich color variation (> 150). Synthetic often < 50
    chroma_synthetic = 1.0 - min(1.0, max(0.0, (color.chrominance_richness - 30.0) / 300.0))

    # 3. Noise consistency: Real camera sensor noise > 3.0. In compressed photos (> 1.0 with natural texture)
    if color.chrominance_richness > 200.0 and texture.lbp_entropy > 4.8:
        noise_synthetic = 1.0 - min(1.0, max(0.0, (noise.residual_variance - 0.5) / 8.0))
    else:
        noise_synthetic = 1.0 - min(1.0, max(0.0, (noise.residual_variance - 1.5) / 15.0))

    # 4. Frequency: Real camera optics have higher relative high-frequency ratio (> 0.0002)
    freq_synthetic = 1.0 - min(1.0, max(0.0, (frequency.high_low_ratio - 0.00005) / 0.002))

    # Weighted combination of physical feature indicators
    raw_forensic_score = (
        0.35 * texture_synthetic
        + 0.30 * chroma_synthetic
        + 0.20 * noise_synthetic
        + 0.15 * freq_synthetic
    )
    score = float(max(0.01, min(0.99, raw_forensic_score)))

    if score >= 0.55:
        pred = "LIKELY_AI_GENERATED"
    elif score <= 0.45:
        pred = "LIKELY_REAL"
    else:
        pred = "INCONCLUSIVE"

    return round(score, 4), pred


def fuse_evidence(
    ai_model_score: float,
    ai_model_prediction: str,
    forensic_score: float,
    forensic_prediction: str,
    ai_weight: float = DEFAULT_AI_MODEL_WEIGHT,
    forensic_weight: float = DEFAULT_FORENSIC_WEIGHT,
    threshold: float = 0.50,
) -> EvidenceFusionResult:
    """
    Combines AI model ensemble probability and pixel forensic probability.
    Evaluates signal agreement and produces a calibrated fused authenticity assessment.
    """
    # Normalize weights so they sum to 1.0
    total_weight = ai_weight + forensic_weight
    w_ai = ai_weight / total_weight if total_weight > 0 else 0.70
    w_pf = forensic_weight / total_weight if total_weight > 0 else 0.30

    fused_score = round(float(w_ai * ai_model_score + w_pf * forensic_score), 4)

    # Signal Agreement Determination
    if (ai_model_prediction == "LIKELY_AI_GENERATED" and forensic_prediction == "LIKELY_AI_GENERATED") or (
        ai_model_prediction == "LIKELY_REAL" and forensic_prediction == "LIKELY_REAL"
    ):
        agreement = SignalAgreement.AGREE
    elif (
        (ai_model_prediction == "LIKELY_AI_GENERATED" and forensic_prediction == "LIKELY_REAL")
        or (ai_model_prediction == "LIKELY_REAL" and forensic_prediction == "LIKELY_AI_GENERATED")
    ):
        agreement = SignalAgreement.DISAGREE
    else:
        agreement = SignalAgreement.PARTIAL

    # Fused Prediction Classification
    dist_from_threshold = abs(fused_score - threshold)
    if agreement == SignalAgreement.DISAGREE and dist_from_threshold < 0.20:
        fused_pred = "INCONCLUSIVE"
        confidence = "MEDIUM"
        explanation = (
            f"Signal conflict observed: AI ensemble indicates {ai_model_prediction} ({ai_model_score*100:.1f}%) "
            f"while pixel forensics indicates {forensic_prediction} ({forensic_score*100:.1f}%). "
            f"Result flagged as INCONCLUSIVE due to evidence divergence."
        )
    elif dist_from_threshold < 0.10:
        fused_pred = "INCONCLUSIVE"
        confidence = "LOW"
        explanation = (
            f"Fused probability ({fused_score*100:.1f}%) is within the borderline uncertainty margin. "
            f"Signal agreement is {agreement.value}."
        )
    elif fused_score >= threshold:
        fused_pred = "LIKELY_AI_GENERATED"
        if agreement == SignalAgreement.AGREE:
            confidence = "VERY_HIGH" if dist_from_threshold >= 0.30 else "HIGH"
            explanation = (
                f"Multi-signal consensus: AI model ensemble ({ai_model_score*100:.1f}%) and "
                f"pixel-level forensics ({forensic_score*100:.1f}%) both indicate synthetic generation signatures."
            )
        else:
            confidence = "MEDIUM"
            explanation = (
                f"Weighted fusion indicates {fused_pred} ({fused_score*100:.1f}%), "
                f"with {agreement.value.lower()} between AI model and forensic signals."
            )
    else:
        fused_pred = "LIKELY_REAL"
        if agreement == SignalAgreement.AGREE:
            confidence = "VERY_HIGH" if dist_from_threshold >= 0.30 else "HIGH"
            explanation = (
                f"Multi-signal consensus: AI model ensemble ({ai_model_score*100:.1f}%) and "
                f"pixel-level forensics ({forensic_score*100:.1f}%) both indicate authentic photographic characteristics."
            )
        else:
            confidence = "MEDIUM"
            explanation = (
                f"Weighted fusion indicates {fused_pred} ({fused_score*100:.1f}%), "
                f"with {agreement.value.lower()} between AI model and forensic signals."
            )

    return EvidenceFusionResult(
        ai_model_score=round(ai_model_score, 4),
        ai_model_prediction=ai_model_prediction,
        forensic_score=round(forensic_score, 4),
        forensic_prediction=forensic_prediction,
        ai_model_weight=round(w_ai, 2),
        forensic_weight=round(w_pf, 2),
        fused_score=fused_score,
        fused_prediction=fused_pred,
        signal_agreement=agreement,
        confidence=confidence,
        fusion_explanation=explanation,
    )
