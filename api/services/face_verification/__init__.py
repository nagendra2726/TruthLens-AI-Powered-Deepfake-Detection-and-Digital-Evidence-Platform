import logging
from typing import Optional
from .schemas import FaceVerificationResult
from .detector import FaceDetector
from .embedder import FaceEmbedder
from .verifier import FaceVerifier, DEFAULT_VERIFICATION_THRESHOLD

logger = logging.getLogger(__name__)

_face_verifier_instance: Optional[FaceVerifier] = None


def get_face_verifier() -> FaceVerifier:
    """Singleton getter for the shared FaceVerifier instance (loaded once on startup)."""
    global _face_verifier_instance
    if _face_verifier_instance is None:
        logger.info("Instantiating global FaceVerifier singleton...")
        _face_verifier_instance = FaceVerifier()
    return _face_verifier_instance


__all__ = [
    "FaceDetector",
    "FaceEmbedder",
    "FaceVerifier",
    "FaceVerificationResult",
    "get_face_verifier",
    "DEFAULT_VERIFICATION_THRESHOLD",
]
