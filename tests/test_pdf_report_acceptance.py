import io
import pytest
from pypdf import PdfReader

from api.services.report.case_store import build_case
from api.services.report.pdf_builder import build_pdf


def _extract_pdf_text_all(pdf_bytes: bytes) -> str:
    reader = PdfReader(io.BytesIO(pdf_bytes))
    full_text = []
    for page in reader.pages:
        full_text.append(page.extract_text() or "")
    return "\n".join(full_text)


def _get_page_count(pdf_bytes: bytes) -> int:
    reader = PdfReader(io.BytesIO(pdf_bytes))
    return len(reader.pages)


def _make_test_case(case_id: str, face_match: bool, signal_agreement: str):
    ref_analysis = {
        "prediction": "LIKELY_REAL",
        "ai_probability": 0.04,
        "real_probability": 0.96,
        "confidence": "HIGH",
        "status": "completed",
        "evidence_fusion": {
            "ai_model_score": 0.04,
            "forensic_score": 0.85 if signal_agreement == "DISAGREE" else 0.05,
            "fused_score": 0.45 if signal_agreement == "DISAGREE" else 0.04,
            "signal_agreement": signal_agreement,
        },
        "pixel_forensics": {
            "score": 0.85 if signal_agreement == "DISAGREE" else 0.05,
            "signal_quality": "HIGH",
            "noise": {"residual_variance": 0.0012},
            "texture": {"lbp_entropy": 7.42},
            "color": {"chrominance_richness": 0.35},
            "edges": {"edge_density": 0.12},
            "frequency": {"high_low_ratio": 0.08},
            "metadata": {"camera_make": "Apple", "software": "iOS 17.2"},
        },
    }

    sus_analysis = {
        "prediction": "LIKELY_AI_GENERATED",
        "ai_probability": 0.96,
        "real_probability": 0.04,
        "confidence": "HIGH",
        "status": "completed",
        "evidence_fusion": {
            "ai_model_score": 0.96,
            "forensic_score": 0.92,
            "fused_score": 0.95,
            "signal_agreement": "AGREE",
        },
        "pixel_forensics": {
            "score": 0.92,
            "signal_quality": "HIGH",
            "noise": {"residual_variance": 0.0048},
            "texture": {"lbp_entropy": 5.11},
            "color": {"chrominance_richness": 0.12},
            "edges": {"edge_density": 0.28},
            "frequency": {"high_low_ratio": 0.22},
            "metadata": {"camera_make": None, "software": "Midjourney v6"},
        },
    }

    face_verif = {
        "status": "completed",
        "reference_face_detected": True,
        "suspected_face_detected": True,
        "reference_faces_count": 1,
        "suspected_faces_count": 1,
        "best_match_score": 0.887 if face_match else 0.210,
        "best_match_face_index": 1,
        "match": face_match,
        "result": "LIKELY_SAME_PERSON" if face_match else "LIKELY_DIFFERENT_PERSON",
        "threshold_used": 0.65,
    }

    assessment = {
        "category": "POTENTIAL_DEEPFAKE" if face_match else "AUTHENTIC_MEDIA_DIFFERENT_PERSON",
        "risk_level": "HIGH" if face_match else "LOW",
        "confidence": "HIGH",
        "explanation": "Standard evaluation case for PDF generation test.",
        "disclaimer": "This assessment is an AI-assisted forensic screening result.",
    }

    model_info = {
        "ai_detection_models": "npr_deepfakedetection",
        "ensemble_method": "voting",
        "threshold": "0.5",
        "face_threshold": "0.65",
        "decision_engine": "TruthLens Rule-Based Engine v1.0",
    }

    return build_case(
        case_id=case_id,
        request_id="uuid-test-9999-8888",
        created_at="2026-08-27T08:00:00Z",
        completed_at="2026-08-27T08:00:03Z",
        processing_seconds=3.14,
        reference_filename="ref.jpg",
        reference_content_type="image/jpeg",
        reference_size_bytes=102400,
        reference_width=800,
        reference_height=600,
        reference_sha256="a" * 64,
        reference_preview_b64=None,
        suspected_filename="sus.png",
        suspected_content_type="image/png",
        suspected_size_bytes=204800,
        suspected_width=800,
        suspected_height=600,
        suspected_sha256="b" * 64,
        suspected_preview_b64=None,
        reference_analysis=ref_analysis,
        suspected_analysis=sus_analysis,
        face_verification=face_verif,
        assessment=assessment,
        model_info=model_info,
    )


def test_tl_000399_same_person():
    case = _make_test_case("TL-000399", face_match=True, signal_agreement="AGREE")
    pdf_bytes = build_pdf(case)
    page_count = _get_page_count(pdf_bytes)
    text = _extract_pdf_text_all(pdf_bytes)

    assert page_count <= 3, f"TL-000399 must be max 3 pages, got {page_count}"
    assert "uuid-test-9999-8888" not in text
    assert "Processing Duration" not in text
    assert "Status: completed" not in text
    assert "EVIDENCE SIGNALS" not in text
    assert "Best Match Face Index" not in text
    assert "Authentic Score" not in text
    assert "TECHNICAL APPENDIX — FORENSIC SIGNAL DETAIL" in text


def test_tl_000400_different_person():
    case = _make_test_case("TL-000400", face_match=False, signal_agreement="AGREE")
    pdf_bytes = build_pdf(case)
    page_count = _get_page_count(pdf_bytes)
    text = _extract_pdf_text_all(pdf_bytes)

    assert page_count <= 3, f"TL-000400 must be max 3 pages, got {page_count}"
    assert "uuid-test-9999-8888" not in text
    assert "Processing Duration" not in text
    assert "Status: completed" not in text
    assert "EVIDENCE SIGNALS" not in text
    assert "Best Match Face Index" not in text


def test_tl_000401_disagree_case():
    case = _make_test_case("TL-000401", face_match=True, signal_agreement="DISAGREE")
    pdf_bytes = build_pdf(case)
    page_count = _get_page_count(pdf_bytes)
    text = _extract_pdf_text_all(pdf_bytes)

    assert page_count <= 3, f"TL-000401 must be max 3 pages, got {page_count}"
    assert "Note: AI model and forensic signal agreement is inconsistent" in text
    assert "DISAGREE — The AI detection ensemble scored this media as" in text
    assert "85%" in text or "4%" in text
    assert "EVIDENCE SIGNALS" not in text
