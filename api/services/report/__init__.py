"""TruthLens — Report Service package."""

from .hasher import sha256_of_bytes
from .case_store import (
    EvidenceCase,
    init_evidence_table,
    generate_case_id,
    sanitize_case_id,
    save_case,
    get_case,
    build_case,
)
from .pdf_builder import build_pdf

__all__ = [
    "sha256_of_bytes",
    "EvidenceCase",
    "init_evidence_table",
    "generate_case_id",
    "sanitize_case_id",
    "save_case",
    "get_case",
    "build_case",
    "build_pdf",
]
