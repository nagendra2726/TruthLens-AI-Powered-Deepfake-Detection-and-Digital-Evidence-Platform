from typing import Optional
from pydantic import BaseModel, Field


class EvidenceSignals(BaseModel):
    """Normalized evidence signals consumed by the Decision Engine."""
    reference_authenticity: str = Field(..., description="Reference prediction (e.g. LIKELY_REAL)")
    suspected_authenticity: str = Field(..., description="Suspected prediction (e.g. LIKELY_AI_GENERATED)")
    face_verification: str = Field(..., description="Face match verdict (e.g. LIKELY_SAME_PERSON)")
    reference_ai_probability: Optional[float] = Field(None, description="P(fake) for reference media")
    suspected_ai_probability: Optional[float] = Field(None, description="P(fake) for suspected media")
    face_similarity_score: Optional[float] = Field(None, description="Cosine similarity score (0.0 to 1.0)")
    face_match: Optional[bool] = Field(None, description="Whether face similarity meets threshold")


class AssessmentResult(BaseModel):
    """Contextual explainable assessment produced by the TruthLens Decision Engine."""
    category: str = Field(
        ...,
        description="Assessment Category: POTENTIAL_DEEPFAKE, LIKELY_AUTHENTIC, BOTH_MEDIA_APPEAR_SYNTHETIC, etc."
    )
    risk_level: str = Field(
        ...,
        description="Risk Level: LOW, MEDIUM, HIGH, or UNKNOWN"
    )
    confidence: str = Field(
        ...,
        description="Overall Decision Confidence: HIGH, MEDIUM, or LOW"
    )
    explanation: str = Field(
        ...,
        description="Human-readable forensic explanation justifying the assessment"
    )
    signals: EvidenceSignals = Field(
        ...,
        description="Transparent breakdown of all supporting signals"
    )
    disclaimer: str = Field(
        default=(
            "This assessment is an AI-assisted forensic screening result and should not be "
            "treated as definitive proof of manipulation, identity, or criminal activity."
        ),
        description="Standard legal / forensic limitation disclaimer"
    )
