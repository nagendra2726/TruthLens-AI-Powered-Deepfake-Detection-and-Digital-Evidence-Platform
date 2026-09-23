import io
import pytest
from fastapi.testclient import TestClient
from api.main import app
from api.database import SessionLocal
from api.services.report.case_store import EvidenceCase

client = TestClient(app)


def test_truthlens_health_endpoint():
    """Verify GET /api/health satisfies TruthLens Phase 22."""
    resp = client.get("/api/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"
    assert data["service"] == "TruthLens"
    assert "timestamp" in data
    assert "ai_model_loaded" in data


def test_truthlens_analyze_endpoint_real_image():
    """Verify POST /api/analyze executes full Vision Transformer pipeline with forensics & SHA-256."""
    with open("tests/sample_image.jpg", "rb") as f:
        img_bytes = f.read()

    resp = client.post(
        "/api/analyze",
        files={"image": ("sample_image.jpg", io.BytesIO(img_bytes), "image/jpeg")},
    )
    assert resp.status_code == 200
    data = resp.json()

    assert data["success"] is True
    assert "case_id" in data
    case_id = data["case_id"]
    assert case_id.startswith("TL-")

    # Result structure
    res = data["result"]
    assert res["classification"] in ["Likely Real", "Likely AI-Generated", "Inconclusive"]
    assert 0.0 <= res["ai_probability"] <= 1.0
    assert 0.0 <= res["real_probability"] <= 1.0
    assert abs((res["ai_probability"] + res["real_probability"]) - 1.0) < 0.01
    assert res["confidence"] in ["LOW", "MEDIUM", "HIGH", "VERY_HIGH"]

    # SHA-256
    assert len(data["hash"]["sha256"]) == 64
    assert "digital fingerprint" in data["hash"]["explanation"]

    # Image Analysis
    img_analysis = data["image_analysis"]
    assert "file_information" in img_analysis
    assert "optical_characteristics" in img_analysis
    assert "ela_analysis" in img_analysis
    assert "spectral_analysis" in img_analysis
    assert img_analysis["file_information"]["resolution"] == "300 × 300"

    # Verify case was persisted in DB
    db = SessionLocal()
    try:
        ev = db.query(EvidenceCase).filter(EvidenceCase.case_id == case_id).first()
        assert ev is not None
        assert ev.suspected_sha256 == data["hash"]["sha256"]
    finally:
        db.query(EvidenceCase).filter(EvidenceCase.case_id == case_id).delete()
        db.commit()
        db.close()


def test_truthlens_analyze_corrupted_file():
    """Verify POST /api/analyze handles corrupted files with friendly HTTP 415."""
    corrupted_bytes = b"NOT_A_REAL_IMAGE_FILE_CORRUPTED"
    resp = client.post(
        "/api/analyze",
        files={"image": ("bad.jpg", io.BytesIO(corrupted_bytes), "image/jpeg")},
    )
    assert resp.status_code == 415
    assert "valid JPG, PNG, JPEG, or WEBP" in resp.json()["detail"]


def test_truthlens_analyze_missing_file():
    """Verify POST /api/analyze handles missing file with HTTP 400."""
    resp = client.post("/api/analyze")
    assert resp.status_code == 400
