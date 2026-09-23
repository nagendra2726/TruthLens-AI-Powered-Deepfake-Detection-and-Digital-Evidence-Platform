import io
import pytest
from pypdf import PdfReader

from scripts.train_generator_classifier import train_or_create_classifier
from models.image.universalfakedetect.detector import get_generator_type
from api.services.report.case_store import build_case
from api.services.report.pdf_builder import build_pdf


def test_generator_classifier_training_and_inference():
    train_or_create_classifier()

    # Test inference helper
    gen_type, gen_conf = get_generator_type([0.5] * 768)
    assert gen_type in ["GAN", "Diffusion"]
    assert 0.0 <= gen_conf <= 100.0


def test_pdf_generator_type_row():
    # Case with fake media -> Generator Type row included
    fake_case = build_case(
        case_id="TL-2026-GEN01",
        request_id="req-gen-1",
        created_at="2026-08-27T10:00:00Z",
        completed_at="2026-08-27T10:00:02Z",
        processing_seconds=1.5,
        reference_filename="ref.jpg",
        reference_content_type="image/jpeg",
        reference_size_bytes=100000,
        reference_width=800,
        reference_height=600,
        reference_sha256="a" * 64,
        reference_preview_b64=None,
        suspected_filename="sus.jpg",
        suspected_content_type="image/jpeg",
        suspected_size_bytes=100000,
        suspected_width=800,
        suspected_height=600,
        suspected_sha256="b" * 64,
        suspected_preview_b64=None,
        reference_analysis={"prediction": "LIKELY_REAL", "ai_probability": 0.04, "confidence": "HIGH"},
        suspected_analysis={"prediction": "LIKELY_AI_GENERATED", "ai_probability": 0.95, "confidence": "HIGH", "generator_type": "Diffusion", "generator_confidence": 88.5},
        face_verification={},
        assessment={"category": "POTENTIAL_DEEPFAKE", "risk_level": "HIGH", "confidence": "HIGH", "explanation": "Generator test."},
        model_info={"ai_detection_models": "universalfakedetect", "ensemble_method": "voting"},
    )

    pdf_bytes = build_pdf(fake_case)
    reader = PdfReader(io.BytesIO(pdf_bytes))
    full_text = "\n".join(p.extract_text() for p in reader.pages)

    assert "Generator Type" in full_text
    assert "Diffusion" in full_text
    assert len(reader.pages) <= 3
