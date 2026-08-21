"""
TruthLens — Image Forensics Schemas
Defines structured forensic signal models, EXIF metadata representations, and evidence fusion contracts.
"""
from __future__ import annotations

from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class SignalAgreement(str, Enum):
    """Indicates agreement between the AI model ensemble and pixel-level forensic signals."""
    AGREE = "AGREE"
    DISAGREE = "DISAGREE"
    PARTIAL = "PARTIAL"


class SignalQuality(str, Enum):
    """Quality of the media for forensic evaluation."""
    GOOD = "GOOD"
    FAIR = "FAIR"
    LOW = "LOW"
    FORENSIC_ANALYSIS_LIMITED = "FORENSIC_ANALYSIS_LIMITED"


class NoiseSignals(BaseModel):
    """Noise residual signals extracted via spatial filtering."""
    mean_residual: float = Field(..., description="Mean of the residual difference between original and denoised image")
    residual_variance: float = Field(..., description="Variance of the noise residual (sensor noise level)")
    mean_absolute_residual: float = Field(..., description="Mean absolute deviation of high-frequency noise")
    spatial_consistency: float = Field(..., description="Spatial uniformity of residual variance across image tiles (0 to 1)")


class TextureSignals(BaseModel):
    """Micro-texture and Local Binary Pattern (LBP) statistics."""
    lbp_entropy: float = Field(..., description="Shannon entropy of the Local Binary Pattern histogram")
    local_variance: float = Field(..., description="Mean local spatial variance across small image neighborhoods")
    gradient_texture_variance: float = Field(..., description="Variance of horizontal and vertical spatial derivatives")


class ColorSignals(BaseModel):
    """RGB and HSV color space distribution statistics."""
    rgb_channel_std: float = Field(..., description="Average standard deviation across R, G, B color channels")
    hsv_saturation_mean: float = Field(..., description="Mean saturation level in HSV color space (0 to 1)")
    hsv_saturation_std: float = Field(..., description="Standard deviation of saturation")
    chrominance_richness: float = Field(..., description="Variance between opposing color channels (natural skin & scene chrominance)")


class EdgeSignals(BaseModel):
    """Edge and gradient structural metrics."""
    edge_density: float = Field(..., description="Ratio of strong edge pixels detected via Canny algorithm (0 to 1)")
    gradient_mean: float = Field(..., description="Mean gradient magnitude across the image")
    gradient_variance: float = Field(..., description="Variance of spatial gradient magnitude")
    orientation_entropy: float = Field(..., description="Entropy of edge orientation distribution")


class FrequencySignals(BaseModel):
    """2D Fourier transform (FFT) spectral energy distribution."""
    low_freq_energy: float = Field(..., description="Energy concentrated in low-frequency spectral bands")
    high_freq_energy: float = Field(..., description="Energy concentrated in high-frequency spectral bands")
    high_low_ratio: float = Field(..., description="Ratio of high-frequency to low-frequency spectral energy")
    spectral_entropy: float = Field(..., description="Spectral entropy of the 2D power spectrum")


class MetadataSignals(BaseModel):
    """
    EXIF metadata extracted strictly as SUPPORTING EVIDENCE.
    Never determines authenticity on its own.
    """
    available: bool = Field(..., description="Whether EXIF or container metadata is present")
    camera_make: Optional[str] = Field(None, description="Camera or device manufacturer (if present)")
    camera_model: Optional[str] = Field(None, description="Camera or device model (if present)")
    software: Optional[str] = Field(None, description="Software or editor tag (if present)")
    creation_date: Optional[str] = Field(None, description="Image creation/capture date (if present)")
    gps_present: bool = Field(False, description="Whether GPS coordinates are tagged (flag only, no raw coords logged)")
    supporting_observations: List[str] = Field(
        default_factory=list,
        description="Forensic observations regarding metadata presence or editing signatures",
    )


class PixelForensicsResult(BaseModel):
    """Combined pixel-level statistical forensic evaluation."""
    score: float = Field(..., description="Statistical forensic likelihood score P(fake/AI) in [0.0, 1.0]")
    prediction: str = Field(..., description="Forensic prediction: LIKELY_REAL, LIKELY_AI_GENERATED, or INCONCLUSIVE")
    signal_quality: SignalQuality = Field(..., description="Assessment of image quality for forensic reliability")
    noise: NoiseSignals = Field(..., description="Noise residual features")
    texture: TextureSignals = Field(..., description="Texture and LBP statistics")
    color: ColorSignals = Field(..., description="Color space statistics")
    edges: EdgeSignals = Field(..., description="Edge and gradient features")
    frequency: FrequencySignals = Field(..., description="2D FFT spectral features")
    metadata: MetadataSignals = Field(..., description="Supporting EXIF metadata")


class EvidenceFusionResult(BaseModel):
    """Transparent evidence fusion combining AI Model Ensemble + Pixel Forensics."""
    ai_model_score: float = Field(..., description="Probability from existing AI model ensemble P(fake)")
    ai_model_prediction: str = Field(..., description="Prediction from AI model ensemble")
    forensic_score: float = Field(..., description="Probability from pixel forensic analysis P(fake)")
    forensic_prediction: str = Field(..., description="Prediction from pixel forensics")
    ai_model_weight: float = Field(..., description="Weight assigned to AI model ensemble score")
    forensic_weight: float = Field(..., description="Weight assigned to pixel forensic score")
    fused_score: float = Field(..., description="Final fused probability P(fake) in [0.0, 1.0]")
    fused_prediction: str = Field(..., description="Final fused prediction (LIKELY_REAL, LIKELY_AI_GENERATED, INCONCLUSIVE)")
    signal_agreement: SignalAgreement = Field(..., description="Agreement status: AGREE, DISAGREE, or PARTIAL")
    confidence: str = Field(..., description="Overall decision confidence: VERY_HIGH, HIGH, MEDIUM, or LOW")
    fusion_explanation: str = Field(..., description="Human-readable explanation of how signals agreed or conflicted")
