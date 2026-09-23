import os
import io
import pytest
import numpy as np

from deepsafe_sdk.audio import AudioModel
from models.audio.aasist_audio_detection.detector import AASISTAudioDetector
from api.services.report.case_store import build_case
from api.services.report.pdf_builder import build_pdf
from pypdf import PdfReader


def test_audio_model_decode_and_pad():
    detector = AASISTAudioDetector()

    # Generate synthetic 16kHz sine wave audio bytes (WAV format)
    import wave
    sr = 16000
    t = np.linspace(0, 1.0, sr, endpoint=False)
    sig = (0.5 * np.sin(2 * np.pi * 440 * t) * 32767).astype(np.int16)

    buf = io.BytesIO()
    with wave.open(buf, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(sr)
        w.writeframes(sig.tobytes())

    b64_str = buf.getvalue()
    import base64
    b64_data = base64.b64encode(b64_str).decode("utf-8")

    waveform, decoded_sr = detector.decode_audio(b64_data)
    assert decoded_sr == 16000
    assert len(waveform) == 16000

    padded = detector.pad_or_truncate(waveform, target_len=64600)
    assert len(padded) == 64600


def test_audio_report_section_5a():
    case = build_case(
        case_id="TL-2026-AUDIO01",
        request_id="req-audio-123",
        created_at="2026-08-27T10:00:00Z",
        completed_at="2026-08-27T10:00:02Z",
        processing_seconds=1.5,
        reference_filename="voice_ref.wav",
        reference_content_type="audio/wav",
        reference_size_bytes=320000,
        reference_width=None,
        reference_height=None,
        reference_sha256="c" * 64,
        reference_preview_b64=None,
        suspected_filename="synthetic_speech.mp3",
        suspected_content_type="audio/mpeg",
        suspected_size_bytes=160000,
        suspected_width=None,
        suspected_height=None,
        suspected_sha256="d" * 64,
        suspected_preview_b64=None,
        reference_analysis={"prediction": "LIKELY_REAL", "ai_probability": 0.05, "confidence": "HIGH"},
        suspected_analysis={"prediction": "LIKELY_AI_GENERATED", "ai_probability": 0.88, "confidence": "HIGH"},
        face_verification={},
        assessment={"category": "POTENTIAL_DEEPFAKE", "risk_level": "HIGH", "confidence": "HIGH", "explanation": "Audio deepfake analysis test."},
        model_info={"ai_detection_models": "aasist_audio_detection", "ensemble_method": "voting"},
    )

    pdf_bytes = build_pdf(case)
    assert isinstance(pdf_bytes, bytes)

    reader = PdfReader(io.BytesIO(pdf_bytes))
    full_text = "\n".join(p.extract_text() for p in reader.pages)

    assert "5A. AUDIO ANALYSIS" in full_text
    assert "AASIST Audio Detector" in full_text
    assert len(reader.pages) <= 3
