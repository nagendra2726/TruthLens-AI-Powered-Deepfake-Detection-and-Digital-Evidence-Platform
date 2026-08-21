"""
TruthLens — Task 5: Cybercrime Complaint Assistance Test Suite
Tests eligibility evaluation, draft generation, input validation, security sanitization,
TXT/PDF downloads, ZIP packaging, and regression integrity.
"""
import io
import json
import zipfile
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "api"))

import pytest
from fastapi.testclient import TestClient

from main import app
from services.report.case_store import build_case, save_case, get_case, init_evidence_table
from database import get_db, SessionLocal
from services.complaint.schemas import ComplaintEligibilityStatus


@pytest.fixture(scope="module", autouse=True)
def setup_db():
    init_evidence_table()


@pytest.fixture
def db_session():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture
def client():
    return TestClient(app)


def _create_mock_case(
    db,
    case_id: str,
    ref_status="LIKELY_REAL",
    sus_status="LIKELY_AI_GENERATED",
    face_result="LIKELY_SAME_PERSON",
    sim_score=0.883,
    category="POTENTIAL_DEEPFAKE",
    risk_level="HIGH",
    confidence="HIGH",
):
    case = build_case(
        case_id=case_id,
        request_id=f"req_{case_id}",
        created_at="2026-08-21T10:00:00Z",
        completed_at="2026-08-21T10:00:02Z",
        processing_seconds=2.0,
        reference_filename="reference_sample.jpg",
        reference_content_type="image/jpeg",
        reference_size_bytes=10240,
        reference_width=800,
        reference_height=600,
        reference_sha256="abcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890",
        reference_preview_b64=None,
        suspected_filename="suspected_sample.jpg",
        suspected_content_type="image/jpeg",
        suspected_size_bytes=12240,
        suspected_width=800,
        suspected_height=600,
        suspected_sha256="9876543210fedcba9876543210fedcba9876543210fedcba9876543210fedcba",
        suspected_preview_b64=None,
        reference_analysis={"status": ref_status, "ensemble_probability": 0.05},
        suspected_analysis={"status": sus_status, "ensemble_probability": 0.95},
        face_verification={
            "result": face_result,
            "similarity_score": sim_score,
            "match": True,
        },
        assessment={
            "category": category,
            "risk_level": risk_level,
            "confidence": confidence,
            "explanation": "Reference appears real while suspected appears synthetic with high identity similarity.",
            "signals": {
                "reference_authenticity": ref_status,
                "suspected_authenticity": sus_status,
                "face_verification": face_result,
                "face_similarity_score": sim_score,
            },
        },
        model_info={"version": "1.0"},
    )
    existing = get_case(db, case_id)
    if existing:
        db.delete(existing)
        db.commit()
    save_case(db, case)
    return case


# --- Test 1: Potential Deepfake + High Risk ---
def test_eligibility_high_risk_case(client, db_session):
    case_id = "TL-2026-000101"
    _create_mock_case(
        db_session,
        case_id,
        category="POTENTIAL_DEEPFAKE",
        risk_level="HIGH",
    )
    
    resp = client.get(f"/cases/{case_id}/complaint-eligibility")
    assert resp.status_code == 200
    data = resp.json()
    assert data["case_id"] == case_id
    assert data["status"] == ComplaintEligibilityStatus.REVIEW_RECOMMENDED.value
    assert "Potential high-risk case" in data["status_message"]
    assert data["can_prepare_draft"] is True


# --- Test 2: Likely Authentic + Low Risk ---
def test_eligibility_likely_authentic(client, db_session):
    case_id = "TL-2026-000102"
    _create_mock_case(
        db_session,
        case_id,
        ref_status="LIKELY_REAL",
        sus_status="LIKELY_REAL",
        category="LIKELY_AUTHENTIC",
        risk_level="LOW",
    )

    resp = client.get(f"/cases/{case_id}/complaint-eligibility")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == ComplaintEligibilityStatus.NOT_REQUIRED.value
    assert "does not automatically recommend a complaint" in data["recommendation_text"]


# --- Test 3: Both Media Appear Synthetic (Negative Test) ---
def test_eligibility_both_synthetic_does_not_claim_crime(client, db_session):
    case_id = "TL-2026-000103"
    _create_mock_case(
        db_session,
        case_id,
        ref_status="LIKELY_AI_GENERATED",
        sus_status="LIKELY_AI_GENERATED",
        category="BOTH_MEDIA_APPEAR_SYNTHETIC",
        risk_level="MEDIUM",
    )

    resp = client.get(f"/cases/{case_id}/complaint-eligibility")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == ComplaintEligibilityStatus.NOT_REQUIRED.value
    assert "Review the circumstances" in data["recommendation_text"]
    assert "crime" not in data["status_message"].lower()


# --- Test 4: Missing Case ID ---
def test_missing_case_returns_404(client):
    resp = client.get("/cases/TL-2026-999999/complaint-eligibility")
    assert resp.status_code == 404
    assert resp.json()["detail"] == "Case not found."


# --- Test 5: Validation Error (short description) ---
def test_validation_error_short_description(client, db_session):
    case_id = "TL-2026-000104"
    _create_mock_case(db_session, case_id)

    payload = {
        "incident_description": "short",  # < 10 chars
    }
    resp = client.post(f"/cases/{case_id}/complaint-draft", json=payload)
    assert resp.status_code == 422


# --- Test 6: Draft Generation with User Incident Details ---
def test_draft_generation_success(client, db_session):
    case_id = "TL-2026-000105"
    _create_mock_case(
        db_session,
        case_id,
        sim_score=0.883,
        category="POTENTIAL_DEEPFAKE",
        risk_level="HIGH",
    )

    payload = {
        "incident_date": "2026-08-20",
        "incident_time": "14:30",
        "platform": "Instagram",
        "platform_url": "https://instagram.com/p/test123",
        "suspected_account": "@impostor_account",
        "incident_description": "Found a manipulated video claiming to be me on Instagram reels.",
        "impact_description": "Reputational concern and unauthorized identity usage.",
        "additional_info": "Reported to platform support already.",
    }

    resp = client.post(f"/cases/{case_id}/complaint-draft", json=payload)
    assert resp.status_code == 200
    data = resp.json()

    assert data["case_id"] == case_id
    assert data["status"] == ComplaintEligibilityStatus.USER_REVIEW_REQUIRED.value
    draft = data["draft"]
    assert case_id in draft["subject"]
    assert "88.3%" in draft["analysis_summary"]["face_similarity"]
    assert draft["user_provided_info"]["platform"] == "Instagram"
    assert "@impostor_account" in draft["user_provided_info"]["suspected_account"]
    assert "Found a manipulated video" in draft["incident_details"]
    assert "TruthLens does not automatically submit complaints." in draft["legal_disclaimer"]


# --- Test 7: Malicious URL / XSS Sanitization ---
def test_xss_sanitization(client, db_session):
    case_id = "TL-2026-000106"
    _create_mock_case(db_session, case_id)

    payload = {
        "platform": "<script>alert('xss')</script>Twitter",
        "incident_description": "<b>Manipulated video</b> with potential script tag injection.",
    }
    resp = client.post(f"/cases/{case_id}/complaint-draft", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert "<script>" not in data["draft"]["user_provided_info"]["platform"]
    assert "&lt;script&gt;" in data["draft"]["user_provided_info"]["platform"]


# --- Test 8: Path Traversal Attempt ---
def test_path_traversal_rejection(client):
    invalid_cases = [
        "TL-2026-../../../etc/passwd",
        "TL-2026-0001;DROP TABLE;",
        "invalid_case_id",
    ]
    for bad_id in invalid_cases:
        resp = client.get(f"/cases/{bad_id}/complaint-eligibility")
        assert resp.status_code in (400, 404)


# --- Test 9: Download TXT and PDF Drafts ---
def test_download_txt_and_pdf_drafts(client, db_session):
    case_id = "TL-2026-000107"
    _create_mock_case(db_session, case_id)

    payload = {
        "incident_date": "2026-08-21",
        "platform": "WhatsApp",
        "incident_description": "Circulated via unauthorized WhatsApp forwarded video message.",
    }

    # TXT download
    txt_resp = client.post(
        f"/cases/{case_id}/complaint-draft/download?format=txt",
        json=payload,
    )
    assert txt_resp.status_code == 200
    assert "text/plain" in txt_resp.headers["content-type"]
    assert f"TruthLens_Complaint_Draft_{case_id}.txt" in txt_resp.headers["content-disposition"]
    assert case_id.encode("utf-8") in txt_resp.content

    # PDF download
    pdf_resp = client.post(
        f"/cases/{case_id}/complaint-draft/download?format=pdf",
        json=payload,
    )
    assert pdf_resp.status_code == 200
    assert "application/pdf" in pdf_resp.headers["content-type"]
    assert f"TruthLens_Complaint_Draft_{case_id}.pdf" in pdf_resp.headers["content-disposition"]
    assert pdf_resp.content.startswith(b"%PDF")


# --- Test 10: Evidence Package ZIP Download ---
def test_download_evidence_package_zip(client, db_session):
    case_id = "TL-2026-000108"
    _create_mock_case(db_session, case_id)

    payload = {
        "incident_date": "2026-08-21",
        "platform": "YouTube",
        "incident_description": "Unauthorized deepfake video published on channel.",
    }

    zip_resp = client.post(
        f"/cases/{case_id}/evidence-package/download",
        json=payload,
    )
    assert zip_resp.status_code == 200
    assert "application/zip" in zip_resp.headers["content-type"]
    assert f"TruthLens_Evidence_{case_id}.zip" in zip_resp.headers["content-disposition"]

    # Verify ZIP contents
    with zipfile.ZipFile(io.BytesIO(zip_resp.content), "r") as zf:
        namelist = zf.namelist()
        assert f"TruthLens_Complaint_Draft_{case_id}.txt" in namelist
        assert f"TruthLens_Complaint_Draft_{case_id}.pdf" in namelist
        assert f"TruthLens_Forensic_Report_{case_id}.pdf" in namelist
        assert f"Evidence_Manifest_{case_id}.json" in namelist

        # Inspect manifest JSON
        manifest_bytes = zf.read(f"Evidence_Manifest_{case_id}.json")
        manifest = json.loads(manifest_bytes)
        assert manifest["case_id"] == case_id
        assert "evidence_integrity" in manifest
        assert "server_secrets" not in manifest
        assert "embeddings" not in manifest
