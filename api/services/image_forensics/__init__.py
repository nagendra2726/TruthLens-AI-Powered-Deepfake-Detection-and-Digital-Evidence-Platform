"""
TruthLens Image Forensics Package
Multi-signal pixel-level forensics, EXIF supporting analysis, and evidence fusion.
"""
from .schemas import (
    NoiseSignals,
    TextureSignals,
    ColorSignals,
    EdgeSignals,
    FrequencySignals,
    MetadataSignals,
    PixelForensicsResult,
    EvidenceFusionResult,
    SignalAgreement,
    SignalQuality,
)
from .analyzer import ImageForensicsAnalyzer
from .fusion import fuse_evidence, compute_forensic_score

__all__ = [
    "NoiseSignals",
    "TextureSignals",
    "ColorSignals",
    "EdgeSignals",
    "FrequencySignals",
    "MetadataSignals",
    "PixelForensicsResult",
    "EvidenceFusionResult",
    "SignalAgreement",
    "SignalQuality",
    "ImageForensicsAnalyzer",
    "fuse_evidence",
    "compute_forensic_score",
]
