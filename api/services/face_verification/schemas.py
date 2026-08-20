from typing import Optional
from pydantic import BaseModel, Field


class FaceVerificationResult(BaseModel):
    """Structured result for biometric face identity verification."""
    status: str = Field(
        ...,
        description="Status of verification: 'completed', 'unable_to_verify', or 'failed'"
    )
    reference_face_detected: bool = Field(
        default=False,
        description="Whether a valid face was detected in reference media"
    )
    suspected_face_detected: bool = Field(
        default=False,
        description="Whether at least one valid face was detected in suspected media"
    )
    reference_faces_count: int = Field(
        default=0,
        description="Total number of faces detected in reference media"
    )
    suspected_faces_count: int = Field(
        default=0,
        description="Total number of faces detected in suspected media"
    )
    best_match_score: Optional[float] = Field(
        default=None,
        description="Highest cosine similarity score between reference and suspected faces (0.0 to 1.0)"
    )
    best_match_face_index: Optional[int] = Field(
        default=None,
        description="1-indexed indicator of the face in suspected media that yielded the best match"
    )
    match: Optional[bool] = Field(
        default=None,
        description="True if best_match_score >= threshold, False otherwise. None if unable to verify."
    )
    result: str = Field(
        ...,
        description="Verdict: 'LIKELY_SAME_PERSON', 'LIKELY_DIFFERENT_PERSON', or 'UNABLE_TO_VERIFY'"
    )
    threshold_used: float = Field(
        default=0.65,
        description="Cosine similarity decision threshold"
    )
    message: Optional[str] = Field(
        default=None,
        description="Explanatory or diagnostic message (e.g. why verification was unable to proceed)"
    )
