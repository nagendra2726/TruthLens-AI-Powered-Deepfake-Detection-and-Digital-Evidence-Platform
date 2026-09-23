import base64
import io
import time
import wave
import numpy as np
import pytest
from unittest.mock import patch, MagicMock

import sys
import os

_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_API_DIR = os.path.join(_PROJECT_ROOT, "api")
_SDK_DIR = os.path.join(_PROJECT_ROOT, "sdk")
for p in [_PROJECT_ROOT, _API_DIR, _SDK_DIR]:
    if p not in sys.path:
        sys.path.insert(0, p)

from deepsafe_sdk import AudioModel, PredictionResult
from circuit_breaker import CircuitBreaker, CircuitState, CircuitBreakerRegistry
from models.audio.aasist_audio_detection.detector import AASISTAudioDetector
from models.video.cross_efficient_vit.detector import CrossEfficientViTDetector
from services.report import sha256_of_bytes
from api.main import calculate_ensemble_verdict_api


def _generate_synthetic_wav_bytes(duration_sec: float = 1.0, sample_rate: int = 16000) -> bytes:
    """Helper to generate valid PCM WAV audio in-memory."""
    buf = io.BytesIO()
    t = np.linspace(0, duration_sec, int(sample_rate * duration_sec), endpoint=False)
    # 440 Hz tone + harmonics
    signal = 0.5 * np.sin(2 * np.pi * 440 * t)
    pcm16 = (signal * 32767).astype(np.int16)
    with wave.open(buf, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(sample_rate)
        w.writeframes(pcm16.tobytes())
    return buf.getvalue()


class TestAudioDetectorAndSDK:
    def test_audio_sdk_decode_and_padding(self):
        detector = AASISTAudioDetector()
        wav_bytes = _generate_synthetic_wav_bytes(duration_sec=2.0, sample_rate=16000)
        b64_audio = base64.b64encode(wav_bytes).decode("utf-8")

        waveform, sr = detector.decode_audio(b64_audio)
        assert sr == 16000
        assert len(waveform) == 32000
        assert -1.0 <= waveform.min() and waveform.max() <= 1.0

        padded = detector.pad_or_truncate(waveform, target_len=64600)
        assert len(padded) == 64600

    def test_aasist_audio_detector_prediction(self):
        detector = AASISTAudioDetector()
        detector.load()

        wav_bytes = _generate_synthetic_wav_bytes(duration_sec=1.5, sample_rate=16000)
        b64_audio = base64.b64encode(wav_bytes).decode("utf-8")

        result = detector.predict(b64_audio, threshold=0.5)
        assert isinstance(result, PredictionResult)
        assert 0.0 <= result.probability <= 1.0
        assert result.prediction in [0, 1]
        assert result.class_name in ["real", "fake"]



class TestCircuitBreakerResilience:
    def test_circuit_breaker_transitions(self):
        cb = CircuitBreaker("test_model", failure_threshold=2, recovery_timeout=0.2, per_call_timeout=1.0)
        assert cb.state == CircuitState.CLOSED
        assert cb.can_execute() is True

        # 1st failure
        cb.record_failure(Exception("Timeout"))
        assert cb.state == CircuitState.CLOSED
        assert cb.can_execute() is True

        # 2nd failure -> Reaches threshold (2) -> OPEN
        cb.record_failure(Exception("Service Unavailable"))
        assert cb.state == CircuitState.OPEN
        assert cb.can_execute() is False

        # Wait for recovery timeout
        time.sleep(0.25)
        assert cb.can_execute() is True
        assert cb.state == CircuitState.HALF_OPEN

        # Success resets to CLOSED
        cb.record_success()
        assert cb.state == CircuitState.CLOSED
        assert cb.consecutive_failures == 0


class TestTemporalVideoAggregation:
    def test_multi_frame_burst_anomaly_pooling(self):
        detector = CrossEfficientViTDetector()

        # Case 1: All clean frames
        clean_scores = [0.10, 0.12, 0.09, 0.11, 0.08, 0.13, 0.10]
        agg_clean = detector._aggregate_temporal_scores(clean_scores)
        assert agg_clean < 0.30

        # Case 2: Deepfake localized burst in subset of frames (e.g. 3 of 10 frames)
        burst_scores = [0.15, 0.12, 0.95, 0.92, 0.88, 0.10, 0.14, 0.11, 0.13, 0.10]
        agg_burst = detector._aggregate_temporal_scores(burst_scores)
        # Genuine temporal aggregation flags burst manipulation instead of getting washed out by flat mean
        assert agg_burst > 0.50


class TestEnsembleDisagreementAndHashing:
    def test_detector_disagreement_surfacing(self):
        # Base models heavily disagree (NPR says 0.95 fake, UniversalFakeDetect says 0.10 real)
        mock_results = {
            "npr_deepfakedetection": {"probability": 0.95, "prediction": 1, "class": "Fake"},
            "universalfakedetect": {"probability": 0.10, "prediction": 0, "class": "Real"},
        }
        (
            verdict,
            confidence,
            fake_votes,
            real_votes,
            prob_fake,
            method_used,
            needs_human_review,
            disagreement_score,
            review_reasons,
        ) = calculate_ensemble_verdict_api(
            results=mock_results,
            threshold=0.5,
            method="average",
            media_type="image",
            request_id="test-req-123",
        )

        assert needs_human_review is True
        assert disagreement_score > 0.30
        assert len(review_reasons) > 0
        assert any("High detector disagreement" in r or "Split decision" in r for r in review_reasons)

    def test_ingestion_sha256_hashing(self):
        sample_bytes = b"DeepSafe Raw Forensic Ingest Bytes 2026"
        computed_hash = sha256_of_bytes(sample_bytes)
        assert len(computed_hash) == 64
        # Hash matches deterministic sha256
        import hashlib
        assert computed_hash == hashlib.sha256(sample_bytes).hexdigest()
