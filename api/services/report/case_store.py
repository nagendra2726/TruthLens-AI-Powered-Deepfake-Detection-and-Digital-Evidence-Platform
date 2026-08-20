"""
TruthLens — Case Store
SQLAlchemy model and CRUD helpers for EvidenceCase records.
Extends the existing database WITHOUT touching the AnalysisHistory table.
"""
from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from sqlalchemy import Column, Integer, String, Text, DateTime, Float, create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# Import the existing Base and engine so we share the same database file
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from database import Base, engine, SessionLocal


# ---------------------------------------------------------------------------
# ORM Model
# ---------------------------------------------------------------------------

class EvidenceCase(Base):
    """Stores a complete TruthLens analysis case for forensic reporting."""
    __tablename__ = "evidence_cases"

    id = Column(Integer, primary_key=True, autoincrement=True)
    case_id = Column(String(32), unique=True, index=True, nullable=False)
    request_id = Column(String(64), unique=True, index=True, nullable=False)

    # Timestamps (UTC ISO-8601 strings for portability)
    created_at = Column(String(32), nullable=False)
    completed_at = Column(String(32), nullable=False)
    processing_seconds = Column(Float, nullable=True)

    # Reference media metadata
    reference_filename = Column(String(512), nullable=True)
    reference_content_type = Column(String(64), nullable=True)
    reference_size_bytes = Column(Integer, nullable=True)
    reference_width = Column(Integer, nullable=True)
    reference_height = Column(Integer, nullable=True)
    reference_sha256 = Column(String(64), nullable=True)
    reference_preview_b64 = Column(Text, nullable=True)   # small JPEG preview

    # Suspected media metadata
    suspected_filename = Column(String(512), nullable=True)
    suspected_content_type = Column(String(64), nullable=True)
    suspected_size_bytes = Column(Integer, nullable=True)
    suspected_width = Column(Integer, nullable=True)
    suspected_height = Column(Integer, nullable=True)
    suspected_sha256 = Column(String(64), nullable=True)
    suspected_preview_b64 = Column(Text, nullable=True)

    # Analysis results (stored as JSON strings)
    reference_analysis_json = Column(Text, nullable=True)
    suspected_analysis_json = Column(Text, nullable=True)
    face_verification_json = Column(Text, nullable=True)
    assessment_json = Column(Text, nullable=True)

    # Model info
    model_info_json = Column(Text, nullable=True)

    # Report generation tracking
    report_version = Column(String(8), default="1.0", nullable=False)
    report_generated_at = Column(String(32), nullable=True)


def init_evidence_table() -> None:
    """Create the evidence_cases table if it does not already exist."""
    EvidenceCase.__table__.create(bind=engine, checkfirst=True)


# ---------------------------------------------------------------------------
# Case ID generation
# ---------------------------------------------------------------------------

def _next_case_number(db) -> int:
    """Return a strictly incrementing integer for case ID sequencing."""
    count = db.query(EvidenceCase).count()
    return count + 1


def generate_case_id(db) -> str:
    """
    Generate a human-readable TruthLens Case ID: TL-YYYY-NNNNNN
    Uses the existing SQLite row count so IDs are sequential, not random.
    """
    year = datetime.now(timezone.utc).year
    seq = _next_case_number(db)
    return f"TL-{year}-{seq:06d}"


# ---------------------------------------------------------------------------
# CRUD helpers
# ---------------------------------------------------------------------------

_SAFE_CASE_ID_RE = re.compile(r"^TL-\d{4}-\d{6}$")


def sanitize_case_id(case_id: str) -> str:
    """
    Validate that the case_id matches the expected format to prevent
    path traversal or injection attacks.
    Raises ValueError if invalid.
    """
    if not _SAFE_CASE_ID_RE.match(case_id):
        raise ValueError(f"Invalid case ID format: {case_id!r}")
    return case_id


def save_case(db, case: EvidenceCase) -> EvidenceCase:
    """Persist a new EvidenceCase record."""
    db.add(case)
    db.commit()
    db.refresh(case)
    return case


def get_case(db, case_id: str) -> Optional[EvidenceCase]:
    """Retrieve an EvidenceCase by case_id. Returns None if not found."""
    try:
        sanitize_case_id(case_id)
    except ValueError:
        return None
    return db.query(EvidenceCase).filter(EvidenceCase.case_id == case_id).first()


def build_case(
    *,
    case_id: str,
    request_id: str,
    created_at: str,
    completed_at: str,
    processing_seconds: float,
    reference_filename: Optional[str],
    reference_content_type: Optional[str],
    reference_size_bytes: Optional[int],
    reference_width: Optional[int],
    reference_height: Optional[int],
    reference_sha256: Optional[str],
    reference_preview_b64: Optional[str],
    suspected_filename: Optional[str],
    suspected_content_type: Optional[str],
    suspected_size_bytes: Optional[int],
    suspected_width: Optional[int],
    suspected_height: Optional[int],
    suspected_sha256: Optional[str],
    suspected_preview_b64: Optional[str],
    reference_analysis: Optional[Dict[str, Any]],
    suspected_analysis: Optional[Dict[str, Any]],
    face_verification: Optional[Dict[str, Any]],
    assessment: Optional[Dict[str, Any]],
    model_info: Optional[Dict[str, Any]],
) -> EvidenceCase:
    """Construct an EvidenceCase ORM object from structured inputs."""
    return EvidenceCase(
        case_id=case_id,
        request_id=request_id,
        created_at=created_at,
        completed_at=completed_at,
        processing_seconds=processing_seconds,
        reference_filename=reference_filename,
        reference_content_type=reference_content_type,
        reference_size_bytes=reference_size_bytes,
        reference_width=reference_width,
        reference_height=reference_height,
        reference_sha256=reference_sha256,
        reference_preview_b64=reference_preview_b64,
        suspected_filename=suspected_filename,
        suspected_content_type=suspected_content_type,
        suspected_size_bytes=suspected_size_bytes,
        suspected_width=suspected_width,
        suspected_height=suspected_height,
        suspected_sha256=suspected_sha256,
        suspected_preview_b64=suspected_preview_b64,
        reference_analysis_json=json.dumps(reference_analysis) if reference_analysis else None,
        suspected_analysis_json=json.dumps(suspected_analysis) if suspected_analysis else None,
        face_verification_json=json.dumps(face_verification) if face_verification else None,
        assessment_json=json.dumps(assessment) if assessment else None,
        model_info_json=json.dumps(model_info) if model_info else None,
        report_version="1.0",
        report_generated_at=None,
    )
