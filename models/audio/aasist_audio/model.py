from deepsafe_sdk import AudioModel, PredictionResult
import torch
import torchaudio
import numpy as np


class AASISTAudioDetector(AudioModel):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.model = None
        self.extractor = None
        self.use_hf = False

    def load(self):
        self.load_model()

    def load_model(self):
        try:
            from transformers import (
                AutoFeatureExtractor,
                AutoModelForAudioClassification
            )
            model_name = "mo-thecreator/deepfake-audio-detection"
            self.extractor = AutoFeatureExtractor.from_pretrained(model_name)
            self.model = AutoModelForAudioClassification.from_pretrained(model_name)
            self.model.eval()
            self.use_hf = True
            print("HuggingFace AASIST model loaded")
        except Exception as e:
            print(f"HF failed: {e}. Using fallback.")
            self.model = None
            self.use_hf = False

    def _fallback_score(self, waveform, sr):
        import librosa
        audio = waveform.numpy().flatten()
        mfcc = librosa.feature.mfcc(y=audio, sr=sr, n_mfcc=40)
        spec = librosa.feature.spectral_centroid(y=audio, sr=sr)
        zcr = librosa.feature.zero_crossing_rate(y=audio)
        features = np.concatenate([
            mfcc.mean(axis=1),
            mfcc.std(axis=1),
            spec.mean(axis=1),
            zcr.mean(axis=1)
        ])
        spectral_var = float(np.var(features))
        return min(max(spectral_var / 1000.0, 0.0), 1.0)

    def predict(self, file_path: str) -> PredictionResult:
        try:
            waveform, sample_rate = torchaudio.load(file_path)
            if waveform.shape[0] > 1:
                waveform = waveform.mean(dim=0, keepdim=True)
            if sample_rate != 16000:
                resampler = torchaudio.transforms.Resample(
                    orig_freq=sample_rate,
                    new_freq=16000
                )
                waveform = resampler(waveform)
                sample_rate = 16000

            if self.use_hf and self.model is not None:
                inputs = self.extractor(
                    waveform.squeeze().numpy(),
                    sampling_rate=16000,
                    return_tensors="pt"
                )
                with torch.no_grad():
                    logits = self.model(**inputs).logits
                    probs = torch.softmax(logits, dim=-1)
                    fake_prob = float(probs[0][1])
            else:
                fake_prob = self._fallback_score(waveform, sample_rate)

            distance = abs(fake_prob - 0.5)
            if distance > 0.4:
                confidence = "VERY_HIGH"
            elif distance > 0.25:
                confidence = "HIGH"
            elif distance > 0.1:
                confidence = "MEDIUM"
            else:
                confidence = "LOW"

            return PredictionResult(
                is_fake=fake_prob > 0.5,
                fake_probability=fake_prob,
                authentic_probability=1.0 - fake_prob,
                confidence=confidence,
                model_name="aasist_audio",
                media_type="audio",
                prediction=(
                    "Likely Synthetic"
                    if fake_prob > 0.5
                    else "Likely Real"
                )
            )
        except Exception as e:
            return PredictionResult(
                is_fake=False,
                fake_probability=0.0,
                authentic_probability=1.0,
                confidence="LOW",
                model_name="aasist_audio",
                media_type="audio",
                prediction="Unable to process",
                error=str(e)
            )
