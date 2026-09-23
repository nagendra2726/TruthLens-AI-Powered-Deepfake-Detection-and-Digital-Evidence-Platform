import io
import json
import zipfile
import pytest
from pypdf import PdfReader

from api.services.report.case_store import build_case
from api.services.report.summary_builder import build_summary_pdf
from api.services.report.case_package import build_case_metadata_json, build_case_zip


def _sample_evidence_case():
    return build_case(
        case_id="TL-2026-CFTEST1",
        request_id="req-casefile-1001",
        created_at="2026-08-27T12:00:00Z",
        completed_at="2026-08-27T12:00:03Z",
        processing_seconds=2.8,
        reference_filename="ref_sample.jpg",
        reference_content_type="image/jpeg",
        reference_size_bytes=100000,
        reference_width=800,
        reference_height=600,
        reference_sha256="1" * 64,
        reference_preview_b64=None,
        suspected_filename="sus_sample.jpg",
        suspected_content_type="image/jpeg",
        suspected_size_bytes=100000,
        suspected_width=800,
        suspected_height=600,
        suspected_sha256="2" * 64,
        suspected_preview_b64=None,
        reference_analysis={"prediction": "LIKELY_REAL", "ai_probability": 0.03, "confidence": "HIGH"},
        suspected_analysis={"prediction": "LIKELY_AI_GENERATED", "ai_probability": 0.94, "confidence": "HIGH"},
        face_verification={"result": "LIKELY_SAME_PERSON", "best_match_score": 0.88, "reference_faces_count": 1, "suspected_faces_count": 1},
        assessment={"category": "POTENTIAL_DEEPFAKE", "risk_level": "HIGH", "confidence": "HIGH", "explanation": "Case file module test."},
        model_info={"ai_detection_models": "npr_deepfakedetection", "ensemble_method": "voting"},
    )


def test_build_summary_pdf_generation():
    case = _sample_evidence_case()
    pdf_bytes = build_summary_pdf(case)
    assert isinstance(pdf_bytes, bytes)
    assert len(pdf_bytes) > 1000

    reader = PdfReader(io.BytesIO(pdf_bytes))
    assert len(reader.pages) == 1

    text = "\n".join(p.extract_text() for p in reader.pages)
    assert "TL-2026-CFTEST1" in text
    assert "Digital Media Analysis Case Summary" in text
    assert "TruthLens provides AI-assisted digital media analysis" in text


def test_build_case_metadata_json():
    case = _sample_evidence_case()
    meta = build_case_metadata_json(case)
    assert meta["caseId"] == "TL-2026-CFTEST1"
    assert meta["status"] == "Case File Ready"
    assert meta["media"]["referenceSha256"] == "1" * 64
    assert meta["analysis"]["riskLevel"] == "HIGH"
    assert meta["faceVerification"]["performed"] is True


def test_build_case_zip_archive():
    case = _sample_evidence_case()
    zip_bytes = build_case_zip(case)
    assert isinstance(zip_bytes, bytes)
    assert len(zip_bytes) > 2000

    with zipfile.ZipFile(io.BytesIO(zip_bytes), "r") as zf:
        namelist = zf.namelist()
        prefix = "TruthLens_Case_TL-2026-CFTEST1/"
        assert f"{prefix}TL-2026-CFTEST1_Summary.pdf" in namelist
        assert f"{prefix}TL-2026-CFTEST1_Report.pdf" in namelist
        assert f"{prefix}TL-2026-CFTEST1_Metadata.json" in namelist
        assert f"{prefix}README.txt" in namelist


def test_get_case_details_endpoint():
    import random
    from fastapi.testclient import TestClient
    from api.main import app
    from api.database import SessionLocal
    from api.services.report.case_store import save_case, EvidenceCase

    rand_seq = random.randint(100000, 999999)
    test_case_id = f"TL-2026-{rand_seq}"
    req_id = f"req-test-{rand_seq}"

    case = build_case(
        case_id=test_case_id,
        request_id=req_id,
        created_at="2026-08-27T12:00:00Z",
        completed_at="2026-08-27T12:00:03Z",
        processing_seconds=2.5,
        reference_filename="ref.jpg",
        reference_content_type="image/jpeg",
        reference_size_bytes=50000,
        reference_width=800,
        reference_height=600,
        reference_sha256="a" * 64,
        reference_preview_b64=None,
        suspected_filename="sus.jpg",
        suspected_content_type="image/jpeg",
        suspected_size_bytes=60000,
        suspected_width=800,
        suspected_height=600,
        suspected_sha256="b" * 64,
        suspected_preview_b64=None,
        reference_analysis={"prediction": "LIKELY_REAL", "ai_probability": 0.05, "confidence": "HIGH"},
        suspected_analysis={"prediction": "LIKELY_AI_GENERATED", "ai_probability": 0.95, "confidence": "HIGH"},
        face_verification={"result": "LIKELY_SAME_PERSON", "best_match_score": 0.9},
        assessment={"category": "POTENTIAL_DEEPFAKE", "risk_level": "HIGH", "confidence": "HIGH"},
        model_info={"ai_detection_models": "npr_deepfakedetection"},
    )
    db = SessionLocal()
    try:
        save_case(db, case)
    finally:
        db.close()

    try:
        client = TestClient(app)
        resp = client.get(f"/cases/{test_case_id}")
        assert resp.status_code == 200
        data = resp.json()
        assert data["case_id"] == test_case_id
        assert data["reference_filename"] == "ref.jpg"
        assert data["assessment"]["category"] == "POTENTIAL_DEEPFAKE"
        assert data["suspected_analysis"]["prediction"] == "LIKELY_AI_GENERATED"

        # Also test /api/cases/{case_id} alias
        resp_alias = client.get(f"/api/cases/{test_case_id}")
        assert resp_alias.status_code == 200
        assert resp_alias.json()["case_id"] == test_case_id

        # Test 404
        resp_404 = client.get("/cases/TL-2026-000000")
        assert resp_404.status_code == 404
    finally:
        cleanup_db = SessionLocal()
        try:
            cleanup_db.query(EvidenceCase).filter(EvidenceCase.case_id == test_case_id).delete()
            cleanup_db.commit()
        finally:
            cleanup_db.close()

