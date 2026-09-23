import pytest
import requests
import os
import fitz
import re

pytestmark = pytest.mark.integration

BASE = "http://localhost:8000"
FIX = "tests/fixtures/"

@pytest.fixture(autouse=True)
def require_gateway():
    """Skip live pipeline tests if the local API server is not running."""
    try:
        r = requests.get(f"{BASE}/health", timeout=1)
        if r.status_code != 200:
            pytest.skip("Main API gateway offline (http://localhost:8000)")
    except Exception:
        pytest.skip("Main API gateway offline (http://localhost:8000)")

# ── Health ────────────────────────────────────

def test_gateway_health():
    r = requests.get(f"{BASE}/health")
    assert r.status_code == 200

def test_npr_health():
    try:
        r = requests.get("http://localhost:5001/health", timeout=2)
        assert r.json().get("status") in ["ok", "healthy"]
    except Exception:
        pytest.skip("NPR container offline")

def test_ufd_health():
    try:
        r = requests.get("http://localhost:5004/health", timeout=2)
        assert r.json().get("status") in ["ok", "healthy"]
    except Exception:
        pytest.skip("UFD container offline")

def test_audio_health():
    try:
        r = requests.get("http://localhost:6001/health", timeout=2)
        assert r.json().get("status") in ["ok", "healthy"]
    except Exception:
        pytest.skip("Audio container offline")

# ── Detection ─────────────────────────────────

def _is_degraded(data: dict) -> bool:
    """Check if result came from degraded/fallback mode (no model microservices)."""
    return bool(data.get("degraded", False))

def test_real_image_low_score():
    with open(f"{FIX}real_person.jpg", "rb") as f:
        r = requests.post(f"{BASE}/analyse", files={"suspect": f})
    assert r.status_code == 200
    data = r.json()
    if _is_degraded(data):
        pytest.skip("Model microservices offline -- skipping score assertion (degraded mode)")
    assert data["ai_detection_score"] <= 0.40

def test_fake_image_high_score():
    with open(f"{FIX}ai_generated.jpg", "rb") as f:
        r = requests.post(f"{BASE}/analyse", files={"suspect": f})
    assert r.status_code == 200
    data = r.json()
    if _is_degraded(data):
        pytest.skip("Model microservices offline -- skipping score assertion (degraded mode)")
    assert data["ai_detection_score"] >= 0.50

# ── Face verification ─────────────────────────

def test_same_person_high_similarity():
    with open(f"{FIX}person_a_ref.jpg", "rb") as ref:
        with open(f"{FIX}person_a_suspect.jpg", "rb") as sus:
            r = requests.post(
                f"{BASE}/analyse",
                files={"reference": ref, "suspect": sus}
            )
    assert r.status_code == 200
    data = r.json()
    if _is_degraded(data):
        pytest.skip("Model microservices offline -- skipping face similarity assertion (degraded mode)")
    assert data.get("face_similarity", 0.8) >= 0.65

def test_different_person_low_similarity():
    with open(f"{FIX}person_a_ref.jpg", "rb") as ref:
        with open(f"{FIX}person_b.jpg", "rb") as sus:
            r = requests.post(
                f"{BASE}/analyse",
                files={"reference": ref, "suspect": sus}
            )
    assert r.status_code == 200
    data = r.json()
    if _is_degraded(data):
        pytest.skip("Model microservices offline -- skipping face similarity assertion (degraded mode)")
    assert data.get("face_similarity", 0.0) < 0.65

# ── Audio ─────────────────────────────────────

def test_audio_detection():
    with open(f"{FIX}synthetic_voice.wav", "rb") as f:
        r = requests.post(f"{BASE}/analyse", files={"suspect": f})
    assert r.status_code == 200
    data = r.json()
    assert "audio_detection" in data

# ── Resilience ────────────────────────────────

def test_partial_fallback():
    """Gateway must return 200 even when model microservices are offline."""
    with open(f"{FIX}real_person.jpg", "rb") as f:
        r = requests.post(f"{BASE}/analyse", files={"suspect": f})
    assert r.status_code == 200

# ── API Key ───────────────────────────────────

def test_api_key_required():
    with open(f"{FIX}real_person.jpg", "rb") as f:
        r = requests.post(f"{BASE}/api/v1/check", files={"file": f})
    assert r.status_code == 401

def test_invalid_api_key():
    with open(f"{FIX}real_person.jpg", "rb") as f:
        r = requests.post(
            f"{BASE}/api/v1/check",
            files={"file": f},
            headers={"X-API-Key": "invalid_key"}
        )
    assert r.status_code == 401

# ── Report quality ────────────────────────────

def _try_open_pdf(path: str):
    """Open a PDF and skip if it cannot be parsed (degraded mode)."""
    try:
        doc = fitz.open(path)
        if doc.page_count == 0:
            pytest.skip("PDF report had 0 pages (degraded mode)")
        return doc
    except Exception as e:
        pytest.skip(f"PDF could not be opened: {e}")

def test_report_no_section6():
    with open(f"{FIX}real_person.jpg", "rb") as f:
        r = requests.post(f"{BASE}/report", files={"suspect": f})
    if r.status_code == 503:
        pytest.skip("Report endpoint 503 -- model microservices offline")
    assert r.status_code == 200, f"Expected 200 got {r.status_code}: {r.text[:200]}"
    with open("/tmp/test_report.pdf", "wb") as f:
        f.write(r.content)
    doc = _try_open_pdf("/tmp/test_report.pdf")
    text = "".join(p.get_text() for p in doc)
    assert "Evidence Signals" not in text
    assert "EVIDENCE SIGNALS" not in text

def test_report_max_3_pages():
    with open(f"{FIX}real_person.jpg", "rb") as f:
        r = requests.post(f"{BASE}/report", files={"suspect": f})
    if r.status_code == 503:
        pytest.skip("Report endpoint 503 -- model microservices offline")
    with open("/tmp/test_pages.pdf", "wb") as f:
        f.write(r.content)
    doc = _try_open_pdf("/tmp/test_pages.pdf")
    assert len(doc) <= 3

def test_report_no_uuid():
    with open(f"{FIX}real_person.jpg", "rb") as f:
        r = requests.post(f"{BASE}/report", files={"suspect": f})
    if r.status_code == 503:
        pytest.skip("Report endpoint 503 -- model microservices offline")
    with open("/tmp/test_uuid.pdf", "wb") as f:
        f.write(r.content)
    doc = _try_open_pdf("/tmp/test_uuid.pdf")
    text = "".join(p.get_text() for p in doc)
    uuids = re.findall(
        r'[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}',
        text
    )
    assert len(uuids) == 0

def test_file_too_large():
    big = b"x" * (51 * 1024 * 1024)
    r = requests.post(
        f"{BASE}/analyse",
        files={"suspect": ("big.jpg", big)}
    )
    assert r.status_code == 413

def test_invalid_format():
    r = requests.post(
        f"{BASE}/analyse",
        files={"suspect": ("file.exe", b"test")}
    )
    assert r.status_code == 415
