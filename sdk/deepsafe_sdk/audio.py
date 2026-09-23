import base64
import io
import logging
import wave
from typing import Tuple

import numpy as np

from deepsafe_sdk.base import DeepSafeModel

logger = logging.getLogger(__name__)


class AudioModel(DeepSafeModel):
    sample_rate: int = 16000
    target_length: int = 64600  # ~4 seconds at 16kHz for AASIST/RawNet

    def decode_audio(self, base64_data: str) -> Tuple[np.ndarray, int]:
        """
        Decodes base64-encoded audio bytes into a normalized 1D float32 numpy array [-1.0, 1.0].
        Supports raw WAV, as well as general formats via soundfile/scipy fallback.
        """
        try:
            audio_bytes = base64.b64decode(base64_data)
        except Exception as e:
            raise ValueError(f"Failed to decode base64 audio data: {e}") from e

        # First attempt: standard wave module (for uncompressed PCM WAV)
        try:
            buf = io.BytesIO(audio_bytes)
            with wave.open(buf, "rb") as w:
                sr = w.getframerate()
                n_frames = w.getnframes()
                raw = w.readframes(n_frames)
                sample_width = w.getsampwidth()
                n_channels = w.getnchannels()

            if sample_width == 2:
                dtype = np.int16
            elif sample_width == 4:
                dtype = np.int32
            else:
                dtype = np.uint8

            waveform = np.frombuffer(raw, dtype=dtype).astype(np.float32)
            max_val = float(np.iinfo(dtype).max) if dtype != np.uint8 else 255.0
            if dtype == np.uint8:
                waveform = (waveform - 128.0) / 128.0
            else:
                waveform = waveform / max_val

            if n_channels > 1:
                waveform = waveform.reshape(-1, n_channels).mean(axis=1)

            return waveform, sr
        except Exception:
            pass

        # Second attempt: soundfile / scipy fallback
        try:
            # pyrefly: ignore [missing-import]
            import soundfile as sf
            buf = io.BytesIO(audio_bytes)
            waveform, sr = sf.read(buf, dtype="float32")
            if waveform.ndim > 1:
                waveform = np.mean(waveform, axis=1)
            return waveform, sr
        except ImportError:
            pass
        except Exception as sf_err:
            logger.debug(f"Soundfile decode failed: {sf_err}")

        # Third attempt: scipy.io.wavfile
        try:
            from scipy.io import wavfile
            buf = io.BytesIO(audio_bytes)
            sr, waveform = wavfile.read(buf)
            waveform = waveform.astype(np.float32)
            if np.issubdtype(waveform.dtype, np.integer):
                waveform = waveform / 32768.0
            if waveform.ndim > 1:
                waveform = np.mean(waveform, axis=1)
            return waveform, sr
        except Exception as sc_err:
            logger.debug(f"Scipy wavfile decode failed: {sc_err}")

        raise ValueError("Unsupported audio format or corrupted stream. Please provide WAV/MP3/FLAC.")

    def pad_or_truncate(self, waveform: np.ndarray, target_len: int = 0) -> np.ndarray:
        """Pads or truncates waveform to fixed sample length."""
        if target_len <= 0:
            target_len = self.target_length
        if len(waveform) >= target_len:
            return waveform[:target_len]
        # Repeat or zero-pad
        repeats = int(np.ceil(target_len / len(waveform)))
        return np.tile(waveform, repeats)[:target_len]

