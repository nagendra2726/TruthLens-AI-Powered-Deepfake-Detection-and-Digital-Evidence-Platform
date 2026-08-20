"""
TruthLens — Task 4 Unit Tests: Digital Evidence Report

Tests cover:
1. Case ID generation format
2. SHA-256 hashing correctness
3. Path traversal prevention
4. Evidence case building
5. PDF generation
6. PDF contains Case ID
7. PDF contains SHA-256
8. PDF contains assessment result
9. Invalid case ID → 404
10. Task 1–3 regression still works
"""
import sys
import os
import hashlib
import tempfile

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "api"))

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock


# ── Import report service modules ─────────────────────────────────────────────
from services.report.hasher import sha256_of_bytes
from services.report.case_store import (
    sanitize_case_id,
    build_case,
    EvidenceCase,
    init_evidence_table,
)
from services.report.pdf_builder import build_pdf


# ── TEST 1: Case ID Format ────────────────────────────────────────────────────
def test_case_id_format_valid():
    """sanitize_case_id must accept valid TL-YYYY-NNNNNN IDs."""
    assert sanitize_case_id("TL-2026-000001") == "TL-2026-000001"
    assert sanitize_case_id("TL-2026-999999") == "TL-2026-999999"


def test_case_id_format_invalid():
    """sanitize_case_id must reject malformed or path-traversal IDs."""
    bad_ids = [
        "../../etc/passwd",
        "TL-2026-1",            # too short
        "TL-26-000001",         # year too short
        "TL_2026_000001",       # wrong separators
        "2026-000001",          # missing prefix
        "../TL-2026-000001",
        "TL-2026-00000A",       # non-numeric sequence
        "",
    ]
    for bad in bad_ids:
        with pytest.raises(ValueError):
            sanitize_case_id(bad)


# ── TEST 2: SHA-256 Hashing ───────────────────────────────────────────────────
def test_sha256_known_value():
    """SHA-256 of b'hello world' must equal the known hex digest."""
    expected = hashlib.sha256(b"hello world").hexdigest()
    assert sha256_of_bytes(b"hello world") == expected


def test_sha256_empty_bytes():
    expected = hashlib.sha256(b"").hexdigest()
    assert sha256_of_bytes(b"") == expected


def test_sha256_large_data_chunked():
    """sha256_of_bytes must produce the same result as stdlib for >64KB data."""
    data = b"X" * (200 * 1024)   # 200 KB
    expected = hashlib.sha256(data).hexdigest()
    assert sha256_of_bytes(data) == expected


def test_sha256_returns_64_hex_chars():
    digest = sha256_of_bytes(b"truthlens")
    assert len(digest) == 64
    assert all(c in "0123456789abcdef" for c in digest)


# ── TEST 3: Evidence Case Construction ────────────────────────────────────────
def _sample_case() -> EvidenceCase:
    return build_case(
        case_id="TL-2026-000001",
        request_id="test-uuid-1234",
        created_at="2026-08-20T18:00:00Z",
        completed_at="2026-08-20T18:00:03Z",
        processing_seconds=2.63,
        reference_filename="reference.jpg",
        reference_content_type="image/jpeg",
        reference_size_bytes=110080,
        reference_width=960,
        reference_height=1280,
        reference_sha256="a" * 64,
        reference_preview_b64=None,
        suspected_filename="suspected.png",
        suspected_content_type="image/png",
        suspected_size_bytes=251000,
        suspected_width=1254,
        suspected_height=1254,
        suspected_sha256="b" * 64,
        suspected_preview_b64=None,
        reference_analysis={
            "status": "completed",
            "prediction": "LIKELY_REAL",
            "ai_probability": 0.04,
            "real_probability": 0.96,
            "confidence": "HIGH",
        },
        suspected_analysis={
            "status": "completed",
            "prediction": "LIKELY_AI_GENERATED",
            "ai_probability": 0.96,
            "real_probability": 0.04,
            "confidence": "HIGH",
        },
        face_verification={
            "status": "completed",
            "reference_face_detected": True,
            "suspected_face_detected": True,
            "reference_faces_count": 1,
            "suspected_faces_count": 1,
            "best_match_score": 0.887,
            "best_match_face_index": 1,
            "match": True,
            "result": "LIKELY_SAME_PERSON",
            "threshold_used": 0.65,
            "message": None,
        },
        assessment={
            "category": "POTENTIAL_DEEPFAKE",
            "risk_level": "HIGH",
            "confidence": "HIGH",
            "explanation": "The reference media appears authentic while the suspected appears AI-generated with a highly similar face.",
            "signals": {
                "reference_authenticity": "LIKELY_REAL",
                "suspected_authenticity": "LIKELY_AI_GENERATED",
                "face_verification": "LIKELY_SAME_PERSON",
                "face_similarity_score": 0.887,
                "reference_ai_probability": 0.04,
                "suspected_ai_probability": 0.96,
                "face_match": True,
            },
            "disclaimer": "This assessment is an AI-assisted forensic screening result.",
        },
        model_info={
            "ai_detection_models": "npr_deepfakedetection",
            "ensemble_method": "voting",
            "threshold": "0.5",
            "face_threshold": "0.65",
            "decision_engine": "TruthLens Rule-Based Engine v1.0",
        },
    )


def test_case_all_fields_present():
    """All required fields must be populated on the EvidenceCase object."""
    case = _sample_case()
    assert case.case_id == "TL-2026-000001"
    assert case.reference_sha256 == "a" * 64
    assert case.suspected_sha256 == "b" * 64
    assert case.reference_width == 960
    assert case.suspected_height == 1254
    assert case.report_version == "1.0"


# ── TEST 4 + 5: PDF Generation & Case ID ─────────────────────────────────────
def test_pdf_generation_produces_bytes():
    """build_pdf must return a non-empty bytes object starting with %PDF."""
    case = _sample_case()
    pdf = build_pdf(case)
    assert isinstance(pdf, bytes)
    assert len(pdf) > 1000
    assert pdf[:4] == b"%PDF"


def test_pdf_contains_case_id():
    """The generated PDF must contain the Case ID string."""
    case = _sample_case()
    pdf = build_pdf(case)
    assert b"TL-2026-000001" in pdf


import zlib
import base64

def _extract_pdf_text(pdf_bytes: bytes) -> bytes:
    """Extract all decompressed stream content from a PDF for text searching."""
    collected = [pdf_bytes]  # also include raw document bytes
    pos = 0
    while True:
        s = pdf_bytes.find(b"stream\n", pos)
        if s == -1:
            s = pdf_bytes.find(b"stream\r\n", pos)
        if s == -1:
            break
        s = pdf_bytes.find(b"\n", s) + 1
        e = pdf_bytes.find(b"endstream", s)
        if e == -1:
            break
        raw = pdf_bytes[s:e].strip()
        if raw.startswith(b"<~") and raw.endswith(b"~>"):
            raw = raw[2:-2]
        try:
            dec = zlib.decompress(base64.a85decode(raw, adobe=True))
            collected.append(dec)
        except Exception:
            try:
                dec = zlib.decompress(raw)
                collected.append(dec)
            except Exception:
                collected.append(raw)
        pos = e + 9
    return b" ".join(collected)


def test_pdf_contains_sha256_hashes():
    """The generated PDF must contain both SHA-256 hash strings."""
    case = _sample_case()
    pdf = build_pdf(case)
    text = _extract_pdf_text(pdf)
    assert b"aaaaaaaaaa" in text   # reference hash prefix
    assert b"bbbbbbbbbb" in text   # suspected hash prefix


def test_pdf_contains_assessment_category():
    """The PDF must mention POTENTIAL DEEPFAKE."""
    case = _sample_case()
    pdf = build_pdf(case)
    text = _extract_pdf_text(pdf)
    assert b"POTENTIAL DEEPFAKE" in text or b"Potential Deepfake" in text


def test_pdf_contains_disclaimer():
    """The PDF must contain the standard forensic disclaimer."""
    case = _sample_case()
    pdf = build_pdf(case)
    text = _extract_pdf_text(pdf)
    assert b"AI-assisted" in text or b"forensic screening" in text


# ── TEST 9: Invalid Case ID → API 400/404 ────────────────────────────────────
def test_invalid_case_id_rejected_by_api():
    """The download endpoint must reject malformed Case IDs with 400."""
    import os
    os.environ.setdefault("DEEPSAFE_CONFIG_FILE_PATH",
                          os.path.join(os.path.dirname(__file__), "..", "config", "deepsafe_config.json"))
    from main import app
    client = TestClient(app, raise_server_exceptions=False)
    resp = client.get("/reports/../../etc/passwd/download")
    assert resp.status_code in (400, 404)


def test_nonexistent_case_id_returns_404():
    """A valid-format but nonexistent Case ID must return 404."""
    import os
    os.environ.setdefault("DEEPSAFE_CONFIG_FILE_PATH",
                          os.path.join(os.path.dirname(__file__), "..", "config", "deepsafe_config.json"))
    from main import app
    client = TestClient(app, raise_server_exceptions=False)
    resp = client.get("/reports/TL-9999-999999/download")
    assert resp.status_code == 404


# ── TEST 10: Regression — Tasks 1–3 still work ───────────────────────────────
def test_decision_engine_regression():
    """Decision Engine must still return POTENTIAL_DEEPFAKE for real+AI+same."""
    from services.decision_engine import run_decision_engine, CAT_POTENTIAL_DEEPFAKE

    result = run_decision_engine(
        reference_analysis={"status": "completed", "prediction": "LIKELY_REAL", "ai_probability": 0.04},
        suspected_analysis={"status": "completed", "prediction": "LIKELY_AI_GENERATED", "ai_probability": 0.96},
        face_verification={"result": "LIKELY_SAME_PERSON", "best_match_score": 0.88, "match": True},
    )
    assert result.category == CAT_POTENTIAL_DEEPFAKE


def test_decision_engine_both_synthetic_regression():
    """AI+AI+Same must remain BOTH_MEDIA_APPEAR_SYNTHETIC."""
    from services.decision_engine import run_decision_engine, CAT_BOTH_SYNTHETIC

    result = run_decision_engine(
        reference_analysis={"status": "completed", "prediction": "LIKELY_AI_GENERATED", "ai_probability": 0.95},
        suspected_analysis={"status": "completed", "prediction": "LIKELY_AI_GENERATED", "ai_probability": 0.93},
        face_verification={"result": "LIKELY_SAME_PERSON", "best_match_score": 0.88, "match": True},
    )
    assert result.category == CAT_BOTH_SYNTHETIC
