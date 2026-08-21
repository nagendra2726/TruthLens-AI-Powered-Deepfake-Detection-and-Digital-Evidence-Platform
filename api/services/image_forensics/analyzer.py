"""
TruthLens — Image Forensics Analyzer
Orchestrates multi-signal pixel-level forensic feature extraction, metadata analysis, and evidence fusion.
"""
from __future__ import annotations

import io
import logging
from PIL import Image
from .schemas import (
    PixelForensicsResult,
    EvidenceFusionResult,
    SignalQuality,
)
from .noise import extract_noise_signals
from .texture import extract_texture_signals
from .color import extract_color_signals
from .edges import extract_edge_signals
from .frequency import extract_frequency_signals
from .metadata import extract_metadata_signals
from .fusion import compute_forensic_score, fuse_evidence

logger = logging.getLogger("truthlens.image_forensics")


class ImageForensicsAnalyzer:
    """High-level analyzer for pixel forensics, EXIF supporting analysis, and evidence fusion."""

    @staticmethod
    def analyze_image(image_bytes: bytes) -> PixelForensicsResult:
        """
        Extracts multi-signal forensic features and supporting metadata from raw image bytes.
        """
        img = Image.open(io.BytesIO(image_bytes))
        rgb_img = img.convert("RGB")
        w, h = rgb_img.size

        # Image quality / reliability check
        if w < 64 or h < 64:
            quality = SignalQuality.FORENSIC_ANALYSIS_LIMITED
        elif w < 200 or h < 200:
            quality = SignalQuality.LOW
        elif w < 600 or h < 600:
            quality = SignalQuality.FAIR
        else:
            quality = SignalQuality.GOOD

        # 1. Feature extraction across all forensic domains
        noise_signals = extract_noise_signals(rgb_img)
        texture_signals = extract_texture_signals(rgb_img)
        color_signals = extract_color_signals(rgb_img)
        edge_signals = extract_edge_signals(rgb_img)
        frequency_signals = extract_frequency_signals(rgb_img)

        # 2. Supporting EXIF metadata (strictly non-deterministic)
        metadata_signals = extract_metadata_signals(image_bytes)

        # 3. Statistical forensic score computation
        forensic_score, forensic_pred = compute_forensic_score(
            noise=noise_signals,
            texture=texture_signals,
            color=color_signals,
            edges=edge_signals,
            frequency=frequency_signals,
        )

        return PixelForensicsResult(
            score=forensic_score,
            prediction=forensic_pred,
            signal_quality=quality,
            noise=noise_signals,
            texture=texture_signals,
            color=color_signals,
            edges=edge_signals,
            frequency=frequency_signals,
            metadata=metadata_signals,
        )

    @staticmethod
    def fuse_signals(
        ai_model_score: float,
        ai_model_prediction: str,
        forensic_result: PixelForensicsResult,
        ai_weight: float = 0.70,
        forensic_weight: float = 0.30,
        threshold: float = 0.50,
    ) -> EvidenceFusionResult:
        """Fuses AI model ensemble output with pixel forensic result."""
        return fuse_evidence(
            ai_model_score=ai_model_score,
            ai_model_prediction=ai_model_prediction,
            forensic_score=forensic_result.score,
            forensic_prediction=forensic_result.prediction,
            ai_weight=ai_weight,
            forensic_weight=forensic_weight,
            threshold=threshold,
        )
