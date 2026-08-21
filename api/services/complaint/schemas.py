"""
TruthLens — Cybercrime Complaint Assistance Schemas
Defines request models, validation rules, status enums, and structured complaint draft models.
"""
from __future__ import annotations

import html
import re
from enum import Enum
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field, field_validator


class ComplaintEligibilityStatus(str, Enum):
    """Status indicating whether complaint assistance is recommended or user-initiated."""
    NOT_REQUIRED = "NOT_REQUIRED"
    REVIEW_RECOMMENDED = "REVIEW_RECOMMENDED"
    DRAFT_AVAILABLE = "DRAFT_AVAILABLE"
    USER_REVIEW_REQUIRED = "USER_REVIEW_REQUIRED"


def _sanitize_string(val: Optional[str], max_length: int = 2000) -> Optional[str]:
    """Strip malicious control characters and truncate to max length."""
    if val is None:
        return None
    cleaned = val.strip()
    if not cleaned:
        return None
    if len(cleaned) > max_length:
        cleaned = cleaned[:max_length]
    cleaned = html.escape(cleaned)
    return cleaned


class UserIncidentInput(BaseModel):
    """User-provided incident facts for the complaint draft."""
    incident_date: Optional[str] = Field(
        None,
        description="Date when the incident occurred or was discovered (YYYY-MM-DD)",
        max_length=20,
    )
    incident_time: Optional[str] = Field(
        None,
        description="Time of the incident (e.g., 14:30 or 02:30 PM)",
        max_length=20,
    )
    platform: Optional[str] = Field(
        None,
        description="Platform where media appeared (e.g., Instagram, Facebook, WhatsApp, YouTube, X/Twitter, Other)",
        max_length=100,
    )
    platform_url: Optional[str] = Field(
        None,
        description="Direct link to post/video/profile",
        max_length=1000,
    )
    suspected_account: Optional[str] = Field(
        None,
        description="Username, handle, or identifier of suspected poster/distributor",
        max_length=150,
    )
    incident_description: str = Field(
        ...,
        min_length=10,
        max_length=4000,
        description="User-authored description of what occurred and how manipulation was identified",
    )
    impact_description: Optional[str] = Field(
        None,
        max_length=2000,
        description="Description of any observed reputation, financial, or personal impact",
    )
    additional_info: Optional[str] = Field(
        None,
        max_length=2000,
        description="Any additional context or evidentiary notes from user",
    )

    @field_validator("incident_date")
    @classmethod
    def validate_date(cls, v: Optional[str]) -> Optional[str]:
        if not v:
            return None
        v = v.strip()
        if not re.match(r"^\d{4}-\d{2}-\d{2}$", v):
            if len(v) > 20:
                raise ValueError("Date string exceeds 20 characters")
        return html.escape(v)

    @field_validator("incident_time")
    @classmethod
    def validate_time(cls, v: Optional[str]) -> Optional[str]:
        if not v:
            return None
        return html.escape(v.strip()[:20])

    @field_validator("platform")
    @classmethod
    def validate_platform(cls, v: Optional[str]) -> Optional[str]:
        return _sanitize_string(v, max_length=100)

    @field_validator("platform_url")
    @classmethod
    def validate_url(cls, v: Optional[str]) -> Optional[str]:
        if not v:
            return None
        v = v.strip()
        if len(v) > 1000:
            raise ValueError("URL exceeds maximum length of 1000 characters")
        if not (v.startswith("http://") or v.startswith("https://")):
            v = "https://" + v
        if not re.match(r"^https?://[a-zA-Z0-9\-._~:/?#\[\]@!$&'()*+,;=%]+$", v):
            raise ValueError("Invalid URL format")
        return html.escape(v)

    @field_validator("suspected_account")
    @classmethod
    def validate_account(cls, v: Optional[str]) -> Optional[str]:
        return _sanitize_string(v, max_length=150)

    @field_validator("incident_description")
    @classmethod
    def validate_description(cls, v: str) -> str:
        cleaned = v.strip()
        if len(cleaned) < 10:
            raise ValueError("Incident description must be at least 10 characters")
        if len(cleaned) > 4000:
            cleaned = cleaned[:4000]
        return html.escape(cleaned)

    @field_validator("impact_description")
    @classmethod
    def validate_impact(cls, v: Optional[str]) -> Optional[str]:
        return _sanitize_string(v, max_length=2000)

    @field_validator("additional_info")
    @classmethod
    def validate_additional(cls, v: Optional[str]) -> Optional[str]:
        return _sanitize_string(v, max_length=2000)


class ComplaintDraftSections(BaseModel):
    """Structured sections forming the neutral, professional complaint draft."""
    subject: str = Field(..., description="Subject line for the complaint")
    case_id: str = Field(..., description="TruthLens Case ID reference")
    incident_summary: str = Field(..., description="High-level incident summary")
    incident_details: str = Field(..., description="User-provided factual description")
    user_provided_info: Dict[str, Any] = Field(
        ...,
        description="Structured key-value pairs of incident parameters (platform, date, time, etc.)",
    )
    analysis_summary: Dict[str, Any] = Field(
        ...,
        description="Summary of AI detection, face verification, risk level, and decision category",
    )
    evidence_summary: Dict[str, Any] = Field(
        ...,
        description="Cryptographic SHA-256 hashes and file metadata",
    )
    user_declaration: str = Field(
        ...,
        description="Affirmation by user regarding the truthfulness of submitted incident details",
    )
    legal_disclaimer: str = Field(
        ...,
        description="Standard TruthLens disclaimer on AI assistance and non-official status",
    )
    full_text: str = Field(
        ...,
        description="Plain text compiled complaint draft ready for copy/download",
    )


class ComplaintDraftResponse(BaseModel):
    """Response payload for complaint draft generation and preview."""
    case_id: str
    status: ComplaintEligibilityStatus
    status_message: str
    eligibility_notes: str
    draft: ComplaintDraftSections
    official_portal_url: str
    generated_at: str


class ComplaintEligibilityResponse(BaseModel):
    """Response payload for checking complaint eligibility status."""
    case_id: str
    status: ComplaintEligibilityStatus
    status_message: str
    assessment_category: str
    risk_level: str
    recommendation_text: str
    can_prepare_draft: bool
