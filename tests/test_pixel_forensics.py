"""
TruthLens — Task 6 Pixel-Level Forensics & Evidence Fusion Test Suite
Validates feature extraction, EXIF isolation, evidence fusion, and disagreement handling.
"""
import io
import os
import sys
import pytest
import numpy as np
from PIL import Image

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "api"))

from services.image_forensics.analyzer import ImageForensicsAnalyzer
from services.image_forensics.schemas import SignalAgreement, SignalQuality
from services.image_forensics.fusion import fuse_evidence, compute_forensic_score
from services.image_forensics.noise import extract_noise_signals
from services.image_forensics.texture import extract_texture_signals
from services.image_forensics.color import extract_color_signals
from services.image_forensics.edges import extract_edge_signals
from services.image_forensics.frequency import extract_frequency_signals
from services.image_forensics.metadata import extract_metadata_signals


@pytest.fixture
def sample_test_image_bytes():
    """Generates a synthetic 200x200 RGB test image."""
    img = Image.new("RGB", (200, 200), color=(120, 150, 200))
    # Add some high-frequency content
    arr = np.array(img)
    arr[50:150, 50:150] = [220, 100, 50]
    img = Image.fromarray(arr)
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    return buf.getvalue()


def test_noise_signals_extraction(sample_test_image_bytes):
    img = Image.open(io.BytesIO(sample_test_image_bytes))
    noise = extract_noise_signals(img)
    assert isinstance(noise.mean_residual, float)
    assert noise.residual_variance >= 0.0
    assert noise.spatial_consistency >= 0.0 and noise.spatial_consistency <= 1.0


def test_texture_signals_extraction(sample_test_image_bytes):
    img = Image.open(io.BytesIO(sample_test_image_bytes))
    texture = extract_texture_signals(img)
    assert texture.lbp_entropy >= 0.0
    assert texture.local_variance >= 0.0
    assert texture.gradient_texture_variance >= 0.0


def test_color_signals_extraction(sample_test_image_bytes):
    img = Image.open(io.BytesIO(sample_test_image_bytes))
    color = extract_color_signals(img)
    assert color.rgb_channel_std >= 0.0
    assert 0.0 <= color.hsv_saturation_mean <= 1.0
    assert color.chrominance_richness >= 0.0


def test_edge_signals_extraction(sample_test_image_bytes):
    img = Image.open(io.BytesIO(sample_test_image_bytes))
    edges = extract_edge_signals(img)
    assert 0.0 <= edges.edge_density <= 1.0
    assert edges.gradient_mean >= 0.0
    assert edges.orientation_entropy >= 0.0


def test_frequency_signals_extraction(sample_test_image_bytes):
    img = Image.open(io.BytesIO(sample_test_image_bytes))
    freq = extract_frequency_signals(img)
    assert 0.0 <= freq.low_freq_energy <= 1.0
    assert 0.0 <= freq.high_freq_energy <= 1.0
    assert freq.high_low_ratio >= 0.0


def test_metadata_extraction_supporting_only(sample_test_image_bytes):
    meta = extract_metadata_signals(sample_test_image_bytes)
    assert isinstance(meta.available, bool)
    assert isinstance(meta.supporting_observations, list)
    assert len(meta.supporting_observations) > 0


def test_full_image_forensics_analysis(sample_test_image_bytes):
    result = ImageForensicsAnalyzer.analyze_image(sample_test_image_bytes)
    assert 0.0 <= result.score <= 1.0
    assert result.prediction in ("LIKELY_REAL", "LIKELY_AI_GENERATED", "INCONCLUSIVE")
    assert result.signal_quality in (SignalQuality.GOOD, SignalQuality.FAIR, SignalQuality.LOW)


def test_evidence_fusion_agree():
    # Both AI and forensics agree on AI-generated
    fusion = fuse_evidence(
        ai_model_score=0.90,
        ai_model_prediction="LIKELY_AI_GENERATED",
        forensic_score=0.85,
        forensic_prediction="LIKELY_AI_GENERATED",
        ai_weight=0.70,
        forensic_weight=0.30,
    )
    assert fusion.signal_agreement == SignalAgreement.AGREE
    assert fusion.fused_prediction == "LIKELY_AI_GENERATED"
    assert fusion.fused_score == 0.885
    assert fusion.confidence in ("HIGH", "VERY_HIGH")


def test_evidence_fusion_disagree():
    # AI says fake (0.85), but Forensics says real (0.20)
    fusion = fuse_evidence(
        ai_model_score=0.85,
        ai_model_prediction="LIKELY_AI_GENERATED",
        forensic_score=0.20,
        forensic_prediction="LIKELY_REAL",
        ai_weight=0.70,
        forensic_weight=0.30,
        threshold=0.50,
    )
    assert fusion.signal_agreement == SignalAgreement.DISAGREE
    # Fused score = 0.70 * 0.85 + 0.30 * 0.20 = 0.595 + 0.060 = 0.655 (dist < 0.20) -> INCONCLUSIVE
    assert fusion.fused_prediction == "INCONCLUSIVE"
    assert "Signal conflict observed" in fusion.fusion_explanation


def test_small_image_quality_handling():
    # Create very small image (32x32)
    small_img = Image.new("RGB", (32, 32), color=(100, 100, 100))
    buf = io.BytesIO()
    small_img.save(buf, format="PNG")
    result = ImageForensicsAnalyzer.analyze_image(buf.getvalue())
    assert result.signal_quality == SignalQuality.FORENSIC_ANALYSIS_LIMITED
