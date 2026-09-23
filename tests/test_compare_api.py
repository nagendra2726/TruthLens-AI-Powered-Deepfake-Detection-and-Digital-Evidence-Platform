import pytest
from fastapi.testclient import TestClient
import sys
import os
import json
from unittest.mock import patch

# Add project root and api directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "api")))

from api import main
from api.main import app, build_authenticity_result

client = TestClient(app)


@pytest.fixture(autouse=True)
def setup_model_config():
    """Ensure ALL_MODEL_CONFIGS is loaded for testing endpoints."""
    config_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "config", "deepsafe_config.json"))
    if os.path.exists(config_path):
        with open(config_path, "r") as f:
            config_data = json.load(f)
            main.ALL_MODEL_CONFIGS = config_data
            main.SUPPORTED_MEDIA_TYPES = list(config_data.get("media_types", {}).keys())
    else:
        main.ALL_MODEL_CONFIGS = {
            "media_types": {
                "image": {
                    "model_endpoints": {"npr_deepfakedetection": "http://npr:5001/predict"},
                    "health_endpoints": {"npr_deepfakedetection": "http://npr:5001/health"},
                }
            },
            "default_threshold": 0.5,
            "default_ensemble_method": "voting",
        }
        main.SUPPORTED_MEDIA_TYPES = ["image"]


# ---------------------------------------------------------------------------
# Unit Tests for build_authenticity_result
# ---------------------------------------------------------------------------

def test_build_authenticity_result_likely_real():
    """Test standard real prediction calculation (P(fake) = 0.04)."""
    res = build_authenticity_result(
        ensemble_prob_fake=0.04,
        model_query_results={"npr_deepfakedetection": {"probability": 0.04, "prediction": 0}},
        threshold=0.5,
    )
    assert res["prediction"] == "LIKELY_REAL"
    assert res["ai_probability"] == 0.04
    assert res["real_probability"] == 0.96
    assert res["confidence"] == "VERY_HIGH"  # distance = 0.46 >= 0.35


def test_build_authenticity_result_likely_ai():
    """Test standard AI-generated prediction calculation (P(fake) = 0.94)."""
    res = build_authenticity_result(
        ensemble_prob_fake=0.94,
        model_query_results={"npr_deepfakedetection": {"probability": 0.94, "prediction": 1}},
        threshold=0.5,
    )
    assert res["prediction"] == "LIKELY_AI_GENERATED"
    assert res["ai_probability"] == 0.94
    assert res["real_probability"] == 0.06
    assert res["confidence"] == "VERY_HIGH"  # distance = 0.44 >= 0.35


def test_build_authenticity_result_inconclusive():
    """Test inconclusive scenario when model is uncertain (e.g., P(fake) = 0.52)."""
    res = build_authenticity_result(
        ensemble_prob_fake=0.52,
        model_query_results={"npr_deepfakedetection": {"probability": 0.52, "prediction": 1}},
        threshold=0.5,
    )
    assert res["prediction"] == "INCONCLUSIVE"
    assert res["confidence"] == "LOW"  # distance = 0.02 < 0.10


def test_build_authenticity_result_confidence_brackets():
    """Test medium and high confidence brackets."""
    # Distance = 0.25 (0.5 + 0.25 = 0.75) -> HIGH
    res_high = build_authenticity_result(0.75, {}, 0.5)
    assert res_high["prediction"] == "LIKELY_AI_GENERATED"
    assert res_high["confidence"] == "HIGH"

    # Distance = 0.15 (0.5 - 0.15 = 0.35) -> MEDIUM
    res_med = build_authenticity_result(0.35, {}, 0.5)
    assert res_med["prediction"] == "LIKELY_REAL"
    assert res_med["confidence"] == "MEDIUM"


# ---------------------------------------------------------------------------
# Integration Tests for /analyze/compare Endpoint
# ---------------------------------------------------------------------------

@pytest.fixture
def sample_image_bytes():
    image_path = os.path.join(os.path.dirname(__file__), "sample_image.jpg")
    if os.path.exists(image_path):
        with open(image_path, "rb") as f:
            return f.read()
    from PIL import Image
    import io
    buf = io.BytesIO()
    img = Image.new("RGB", (64, 64), color="blue")
    img.save(buf, format="JPEG")
    return buf.getvalue()


def test_compare_endpoint_both_real(sample_image_bytes):
    """TEST 1: Reference = Real, Suspected = Real."""
    with patch("api.main.query_model_api") as mock_query:
        mock_query.return_value = {
            "model": "npr_deepfakedetection",
            "probability": 0.05,
            "prediction": 0,
            "class": "real",
            "inference_time": 0.1,
        }

        response = client.post(
            "/analyze/compare",
            files={
                "reference_media": ("ref.jpg", sample_image_bytes, "image/jpeg"),
                "suspected_media": ("sus.jpg", sample_image_bytes, "image/jpeg"),
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["reference_analysis"]["status"] == "completed"
        assert data["suspected_analysis"]["status"] == "completed"
        assert data["reference_analysis"]["prediction"] == "LIKELY_REAL"
        assert data["suspected_analysis"]["prediction"] == "LIKELY_REAL"
        assert "is_likely_deepfake" not in data["reference_analysis"]


def test_compare_endpoint_ref_real_sus_ai(sample_image_bytes):
    """TEST 2: Reference = Real, Suspected = AI-generated."""
    with patch("api.main.query_model_api") as mock_query:
        call_count = 0

        def side_effect(model_name, media_type, encoded_media_content, threshold, req_id):
            nonlocal call_count
            call_count += 1
            is_ref = call_count <= len(main.ALL_MODEL_CONFIGS["media_types"]["image"]["model_endpoints"])
            return {
                "model": model_name,
                "probability": 0.08 if is_ref else 0.92,
                "prediction": 0 if is_ref else 1,
                "class": "real" if is_ref else "fake",
                "inference_time": 0.1,
            }
        mock_query.side_effect = side_effect

        response = client.post(
            "/analyze/compare",
            files={
                "reference_media": ("ref.jpg", sample_image_bytes, "image/jpeg"),
                "suspected_media": ("sus.jpg", sample_image_bytes, "image/jpeg"),
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["reference_analysis"]["prediction"] == "LIKELY_REAL"
        assert data["suspected_analysis"]["prediction"] == "LIKELY_AI_GENERATED"


def test_compare_endpoint_both_ai(sample_image_bytes):
    """TEST 3: Reference = AI-generated, Suspected = AI-generated."""
    with patch("api.main.query_model_api") as mock_query:
        mock_query.return_value = {
            "model": "npr_deepfakedetection",
            "probability": 0.88,
            "prediction": 1,
            "class": "fake",
            "inference_time": 0.1,
        }

        response = client.post(
            "/analyze/compare",
            files={
                "reference_media": ("ref.jpg", sample_image_bytes, "image/jpeg"),
                "suspected_media": ("sus.jpg", sample_image_bytes, "image/jpeg"),
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["reference_analysis"]["prediction"] == "LIKELY_AI_GENERATED"
        assert data["suspected_analysis"]["prediction"] == "LIKELY_AI_GENERATED"


def test_compare_endpoint_ref_ai_sus_real(sample_image_bytes):
    """TEST 4: Reference = AI-generated, Suspected = Real."""
    with patch("api.main.query_model_api") as mock_query:
        call_count = 0

        def side_effect(model_name, media_type, encoded_media_content, threshold, req_id):
            nonlocal call_count
            call_count += 1
            is_ref = call_count <= len(main.ALL_MODEL_CONFIGS["media_types"]["image"]["model_endpoints"])
            return {
                "model": model_name,
                "probability": 0.91 if is_ref else 0.07,
                "prediction": 1 if is_ref else 0,
                "class": "fake" if is_ref else "real",
                "inference_time": 0.1,
            }
        mock_query.side_effect = side_effect

        response = client.post(
            "/analyze/compare",
            files={
                "reference_media": ("ref.jpg", sample_image_bytes, "image/jpeg"),
                "suspected_media": ("sus.jpg", sample_image_bytes, "image/jpeg"),
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["reference_analysis"]["prediction"] == "LIKELY_AI_GENERATED"
        assert data["suspected_analysis"]["prediction"] == "LIKELY_REAL"


def test_compare_endpoint_one_invalid_file(sample_image_bytes):
    """TEST 6: One file is invalid (corrupt image), other is valid."""
    with patch("api.main.query_model_api") as mock_query:
        mock_query.return_value = {
            "model": "npr_deepfakedetection",
            "probability": 0.10,
            "prediction": 0,
            "class": "real",
            "inference_time": 0.1,
        }

        corrupt_bytes = b"not a valid image content"
        response = client.post(
            "/analyze/compare",
            files={
                "reference_media": ("corrupt.jpg", corrupt_bytes, "image/jpeg"),
                "suspected_media": ("valid.jpg", sample_image_bytes, "image/jpeg"),
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["reference_analysis"]["status"] == "failed"
        assert "error" in data["reference_analysis"]
        assert data["suspected_analysis"]["status"] == "completed"
        assert data["suspected_analysis"]["prediction"] == "LIKELY_REAL"


def test_compare_endpoint_missing_file():
    """Test validation when one or both files are missing."""
    response = client.post("/analyze/compare", files={})
    assert response.status_code == 422  # Unprocessable Entity for missing required form fields


def test_backward_compatibility_detect_endpoint(sample_image_bytes):
    """Regression test: verify original /detect endpoint continues to work untouched."""
    with patch("api.main.query_model_api") as mock_query:
        mock_query.return_value = {
            "model": "npr_deepfakedetection",
            "probability": 0.20,
            "prediction": 0,
            "class": "real",
            "inference_time": 0.1,
        }

        response = client.post(
            "/detect",
            files={"file": ("sample.jpg", sample_image_bytes, "image/jpeg")},
        )

        assert response.status_code == 200
        data = response.json()
        assert "is_likely_deepfake" in data
        assert "deepfake_probability" in data
        assert "model_results" in data
