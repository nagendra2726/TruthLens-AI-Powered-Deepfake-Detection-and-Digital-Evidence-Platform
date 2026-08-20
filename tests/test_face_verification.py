import pytest
from PIL import Image
import os
import sys
import torch
import torch.nn.functional as F
from unittest.mock import patch
from fastapi.testclient import TestClient

# Add api directory to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "api")))

from services.face_verification import (
    FaceDetector,
    FaceEmbedder,
    FaceVerifier,
    FaceVerificationResult,
    get_face_verifier,
    DEFAULT_VERIFICATION_THRESHOLD,
)
import main
from main import app

client = TestClient(app)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def face_verifier_instance():
    return get_face_verifier()


@pytest.fixture
def real_face_image():
    path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "frontend", "public", "demo_images", "real_sample.jpg"))
    if os.path.exists(path):
        return Image.open(path).convert("RGB")
    # Fallback synthetically created test face
    return Image.new("RGB", (160, 160), color=(180, 150, 130))


@pytest.fixture
def different_face_image():
    path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "frontend", "public", "demo_images", "fake_sample_gan.jpg"))
    if os.path.exists(path):
        return Image.open(path).convert("RGB")
    return Image.new("RGB", (160, 160), color=(100, 120, 140))


@pytest.fixture
def non_face_image():
    return Image.new("RGB", (120, 120), color="blue")


# ---------------------------------------------------------------------------
# Unit Tests for Face Detection & Embedding
# ---------------------------------------------------------------------------

def test_face_detector_detects_real_face(real_face_image):
    detector = FaceDetector()
    tensors, count = detector.detect_and_crop(real_face_image)
    assert count >= 1
    assert tensors is not None
    assert tensors.shape[1:] == torch.Size([3, 160, 160])


def test_face_detector_no_face(non_face_image):
    detector = FaceDetector()
    tensors, count = detector.detect_and_crop(non_face_image)
    assert count == 0
    assert tensors is None


def test_face_embedder_normalised_output():
    embedder = FaceEmbedder()
    dummy_faces = torch.randn(2, 3, 160, 160)
    embeddings = embedder.extract_embeddings(dummy_faces)
    assert embeddings.shape == (2, 512)
    # Check L2 norm is ~1.0
    norms = torch.norm(embeddings, p=2, dim=1)
    for n in norms:
        assert abs(n.item() - 1.0) < 1e-4


# ---------------------------------------------------------------------------
# Unit Tests for FaceVerifier
# ---------------------------------------------------------------------------

def test_verifier_same_person(face_verifier_instance, real_face_image):
    """TEST 1: Same person comparison (identity match)."""
    res = face_verifier_instance.verify_faces(real_face_image, real_face_image)
    assert isinstance(res, FaceVerificationResult)
    assert res.status == "completed"
    assert res.reference_face_detected is True
    assert res.suspected_face_detected is True
    assert res.match is True
    assert res.result == "LIKELY_SAME_PERSON"
    assert res.best_match_score is not None
    assert res.best_match_score >= 0.90


def test_verifier_different_person(face_verifier_instance, real_face_image, different_face_image):
    """TEST 2: Different person comparison (identity mismatch)."""
    res = face_verifier_instance.verify_faces(real_face_image, different_face_image)
    assert res.status == "completed"
    assert res.reference_face_detected is True
    assert res.suspected_face_detected is True
    assert res.match is False
    assert res.result == "LIKELY_DIFFERENT_PERSON"
    assert res.best_match_score is not None
    assert res.best_match_score < 0.65


def test_verifier_no_face_in_suspected(face_verifier_instance, real_face_image, non_face_image):
    """TEST 3: No face in suspected media."""
    res = face_verifier_instance.verify_faces(real_face_image, non_face_image)
    assert res.status == "unable_to_verify"
    assert res.reference_face_detected is True
    assert res.suspected_face_detected is False
    assert res.match is None
    assert res.result == "UNABLE_TO_VERIFY"
    assert "No usable face detected in suspected media" in res.message


def test_verifier_no_face_in_reference(face_verifier_instance, non_face_image, real_face_image):
    """TEST 4: No face in reference media."""
    res = face_verifier_instance.verify_faces(non_face_image, real_face_image)
    assert res.status == "unable_to_verify"
    assert res.reference_face_detected is False
    assert res.suspected_face_detected is True
    assert res.match is None
    assert res.result == "UNABLE_TO_VERIFY"
    assert "No usable face detected in reference media" in res.message


def test_verifier_multi_face_matching(face_verifier_instance):
    """TEST 5: Suspected image with multiple faces picks the best matching face."""
    # Create a composite side-by-side image containing both different and same person
    real_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "frontend", "public", "demo_images", "real_sample.jpg"))
    fake_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "frontend", "public", "demo_images", "fake_sample_gan.jpg"))
    if os.path.exists(real_path) and os.path.exists(fake_path):
        img_real = Image.open(real_path).convert("RGB")
        img_fake = Image.open(fake_path).convert("RGB")

        # Composite side by side (2 faces in suspected)
        combo = Image.new("RGB", (img_fake.width + img_real.width, max(img_fake.height, img_real.height)))
        combo.paste(img_fake, (0, 0))
        combo.paste(img_real, (img_fake.width, 0))

        res = face_verifier_instance.verify_faces(img_real, combo)
        assert res.status == "completed"
        assert res.suspected_faces_count >= 2
        # The best match among the 2 faces should match img_real
        assert res.match is True
        assert res.result == "LIKELY_SAME_PERSON"


# ---------------------------------------------------------------------------
# Integration Tests for /analyze/compare with Face Verification
# ---------------------------------------------------------------------------

def test_compare_endpoint_includes_face_verification():
    """Verify POST /analyze/compare includes structured face_verification block."""
    real_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "frontend", "public", "demo_images", "real_sample.jpg"))
    if not os.path.exists(real_path):
        pytest.skip("Demo real image not found")

    with open(real_path, "rb") as f:
        real_bytes = f.read()

    with patch("main.query_model_api") as mock_query:
        mock_query.return_value = {
            "model": "npr_deepfakedetection",
            "probability": 0.05,
            "prediction": 0,
            "class": "real",
            "inference_time": 0.05,
        }

        response = client.post(
            "/analyze/compare",
            files={
                "reference_media": ("real.jpg", real_bytes, "image/jpeg"),
                "suspected_media": ("real_clone.jpg", real_bytes, "image/jpeg"),
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert "face_verification" in data
        fv = data["face_verification"]
        assert fv["status"] == "completed"
        assert fv["reference_face_detected"] is True
        assert fv["suspected_face_detected"] is True
        assert fv["match"] is True
        assert fv["result"] == "LIKELY_SAME_PERSON"
        assert fv["best_match_score"] >= 0.90
