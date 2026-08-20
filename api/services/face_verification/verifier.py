import logging
from typing import Optional
from PIL import Image
import torch
import torch.nn.functional as F

from .detector import FaceDetector
from .embedder import FaceEmbedder
from .schemas import FaceVerificationResult

logger = logging.getLogger(__name__)

DEFAULT_VERIFICATION_THRESHOLD: float = 0.65


class FaceVerifier:
    """
    Orchestrates face detection, embedding extraction, and multi-face identity comparison.
    Loaded once at service startup and reused across requests.
    """

    def __init__(self, device: Optional[torch.device] = None):
        self.device = device or torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.detector = FaceDetector(device=self.device)
        self.embedder = FaceEmbedder(device=self.device)
        logger.info("FaceVerifier initialized successfully.")

    def verify_faces(
        self,
        reference_image: Image.Image,
        suspected_image: Image.Image,
        threshold: float = DEFAULT_VERIFICATION_THRESHOLD,
    ) -> FaceVerificationResult:
        """
        Independently detects faces in reference and suspected images, generates identity
        embeddings, and computes multi-face cosine similarity matching.
        """
        try:
            # 1. Detect faces in reference media
            ref_tensors, ref_count = self.detector.detect_and_crop(reference_image)
            ref_detected = ref_count > 0

            # 2. Detect faces in suspected media
            sus_tensors, sus_count = self.detector.detect_and_crop(suspected_image)
            sus_detected = sus_count > 0

            # Handle no-face cases
            if not ref_detected and not sus_detected:
                return FaceVerificationResult(
                    status="unable_to_verify",
                    reference_face_detected=False,
                    suspected_face_detected=False,
                    reference_faces_count=0,
                    suspected_faces_count=0,
                    result="UNABLE_TO_VERIFY",
                    threshold_used=threshold,
                    message="No usable face detected in either reference or suspected media.",
                )

            if not ref_detected:
                return FaceVerificationResult(
                    status="unable_to_verify",
                    reference_face_detected=False,
                    suspected_face_detected=True,
                    reference_faces_count=0,
                    suspected_faces_count=sus_count,
                    result="UNABLE_TO_VERIFY",
                    threshold_used=threshold,
                    message="No usable face detected in reference media.",
                )

            if not sus_detected:
                return FaceVerificationResult(
                    status="unable_to_verify",
                    reference_face_detected=True,
                    suspected_face_detected=False,
                    reference_faces_count=ref_count,
                    suspected_faces_count=0,
                    result="UNABLE_TO_VERIFY",
                    threshold_used=threshold,
                    message="No usable face detected in suspected media.",
                )

            # 3. Extract embeddings
            # For reference, use the primary face (index 0)
            ref_embeddings = self.embedder.extract_embeddings(ref_tensors)
            ref_primary_emb = ref_embeddings[0:1]  # Shape: (1, 512)

            # For suspected, extract embeddings for all detected faces (Shape: N, 512)
            sus_embeddings = self.embedder.extract_embeddings(sus_tensors)

            # 4. Multi-face pairwise cosine similarity
            # Compute cosine similarity between ref_primary_emb and each suspected face
            similarities = F.cosine_similarity(ref_primary_emb, sus_embeddings, dim=1)  # Shape: (N,)

            best_score_tensor, best_idx_tensor = torch.max(similarities, dim=0)
            raw_score = float(best_score_tensor.item())

            # Clamp similarity between 0.0 and 1.0 (cosine can be negative for orthogonal/opposite vectors)
            clamped_score = round(max(0.0, min(1.0, raw_score)), 4)
            best_face_index = int(best_idx_tensor.item()) + 1  # 1-indexed for human readability

            is_match = clamped_score >= threshold
            verdict = "LIKELY_SAME_PERSON" if is_match else "LIKELY_DIFFERENT_PERSON"

            logger.info(
                f"Face verification result: {verdict} (Score: {clamped_score:.4f}, "
                f"Threshold: {threshold}, Suspected Face #{best_face_index} of {sus_count})"
            )

            return FaceVerificationResult(
                status="completed",
                reference_face_detected=True,
                suspected_face_detected=True,
                reference_faces_count=ref_count,
                suspected_faces_count=sus_count,
                best_match_score=clamped_score,
                best_match_face_index=best_face_index,
                match=is_match,
                result=verdict,
                threshold_used=threshold,
            )

        except Exception as e:
            logger.exception(f"Unhandled error in FaceVerifier: {e}")
            return FaceVerificationResult(
                status="failed",
                reference_face_detected=False,
                suspected_face_detected=False,
                result="UNABLE_TO_VERIFY",
                threshold_used=threshold,
                message="An internal error occurred during face verification.",
            )
