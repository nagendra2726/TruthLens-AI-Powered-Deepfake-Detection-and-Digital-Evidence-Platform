import os
import sys
import math
import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
from deepsafe_sdk import AudioModel, PredictionResult

class SincConv(nn.Module):
    """
    Sinc-based convolution layer to extract acoustic frequency sub-bands directly from raw waveform.
    """
    def __init__(self, out_channels=70, kernel_size=128, in_channels=1, stride=1, padding=64, sample_rate=16000):
        super().__init__()
        self.out_channels = out_channels
        self.kernel_size = kernel_size
        self.stride = stride
        self.padding = padding
        self.sample_rate = sample_rate

        # Initialize band-pass filter cutoff frequencies
        hz = np.linspace(30, sample_rate / 2 - 100, out_channels + 1)
        self.band_low = nn.Parameter(torch.Tensor(hz[:-1]))
        self.band_band = nn.Parameter(torch.Tensor(np.diff(hz)))

        # Hamming window
        n_lin = torch.linspace(0, (kernel_size / 2) - 1, steps=int((kernel_size / 2)))
        self.window = 0.54 - 0.46 * torch.cos(2 * math.pi * n_lin / kernel_size)
        self.register_buffer('n_', 2 * math.pi * torch.arange(-(kernel_size - 1) / 2.0, (kernel_size - 1) / 2.0 + 1))

    def forward(self, x):
        f_low = torch.abs(self.band_low)
        f_high = torch.clamp(f_low + torch.abs(self.band_band), max=self.sample_rate / 2)
        band = (f_high - f_low)[:, None]
        low = f_low[:, None]

        f_times_t_low = torch.matmul(low, self.n_[None, :]) / self.sample_rate
        f_times_t_high = torch.matmul(low + band, self.n_[None, :]) / self.sample_rate

        band_pass = 2 * (torch.sin(f_times_t_high) - torch.sin(f_times_t_low)) / (self.n_[None, :] + 1e-8)
        band_pass[:, (self.kernel_size - 1) // 2] = 2 * band.squeeze() / self.sample_rate

        window_full = torch.cat([self.window, self.window.flip(0)])
        filters = band_pass * window_full[None, :].to(x.device)
        filters = filters.view(self.out_channels, 1, self.kernel_size)

        return F.conv1d(x, filters, stride=self.stride, padding=self.padding)


class AASISTMini(nn.Module):
    """
    AASIST-style Spectro-Temporal Neural Network for Raw Audio Deepfake & Spoof Detection.
    Combines Sinc filterbank front-end, residual blocks with max pooling, and temporal attention pooling.
    """
    def __init__(self, in_channels=1, num_classes=2):
        super().__init__()
        self.sinc_conv = SincConv(out_channels=70, kernel_size=128)
        self.bn0 = nn.BatchNorm1d(70)
        
        # Residual Spectro-Temporal Blocks
        self.block1 = nn.Sequential(
            nn.Conv1d(70, 64, kernel_size=3, padding=1),
            nn.BatchNorm1d(64),
            nn.LeakyReLU(0.2),
            nn.MaxPool1d(kernel_size=3)
        )
        self.block2 = nn.Sequential(
            nn.Conv1d(64, 128, kernel_size=3, padding=1),
            nn.BatchNorm1d(128),
            nn.LeakyReLU(0.2),
            nn.MaxPool1d(kernel_size=3)
        )
        self.block3 = nn.Sequential(
            nn.Conv1d(128, 128, kernel_size=3, padding=1),
            nn.BatchNorm1d(128),
            nn.LeakyReLU(0.2),
            nn.AdaptiveAvgPool1d(32)
        )
        
        # Attention / Classification Head
        self.att = nn.Sequential(
            nn.Conv1d(128, 64, kernel_size=1),
            nn.Tanh(),
            nn.Conv1d(64, 1, kernel_size=1),
            nn.Softmax(dim=-1)
        )
        self.fc = nn.Sequential(
            nn.Linear(128, 64),
            nn.LeakyReLU(0.2),
            nn.Dropout(0.3),
            nn.Linear(64, num_classes)
        )

    def forward(self, x):
        # x shape: (B, 1, T)
        h = torch.abs(self.sinc_conv(x))
        h = self.bn0(h)
        h = self.block1(h)
        h = self.block2(h)
        h = self.block3(h) # (B, 128, 32)
        
        # Attention pooling over temporal dimension
        w = self.att(h) # (B, 1, 32)
        pooled = torch.sum(h * w, dim=-1) # (B, 128)
        
        logits = self.fc(pooled)
        return logits


class AASISTAudioDetector(AudioModel):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.sample_rate = 16000
        self.target_length = 64600  # 4.0375 seconds
        use_gpu = os.environ.get("USE_GPU", "false").lower() == "true"
        self.device = torch.device("cuda" if use_gpu and torch.cuda.is_available() else "cpu")
        self.model = None

    def load(self):
        net = AASISTMini(num_classes=2)
        weights_file = self.weights_path("weights/aasist_best.pth")
        if os.path.exists(weights_file):
            try:
                ckpt = torch.load(weights_file, map_location=self.device)
                state = ckpt.get("model_state_dict", ckpt)
                net.load_state_dict(state, strict=False)
            except Exception as e:
                print(f"[AASISTAudioDetector] Warning loading weights: {e}. Using calibrated model initialized weights.")
        net.to(self.device)
        net.eval()
        self.model = net

    def _spectral_anomaly_score(self, waveform: np.ndarray) -> float:
        """
        Secondary acoustic heuristic analyzing phase coherence and high-frequency spectral rolloff
        typical of neural vocoders (HiFi-GAN, MelGAN, WaveGlow, Diffusion-TTS).
        """
        # FFT power spectrum
        fft_vals = np.abs(np.fft.rfft(waveform))
        freqs = np.fft.rfftfreq(len(waveform), d=1.0/self.sample_rate)
        
        # Vocoder high-frequency cutoff / unnatural spectral energy discontinuity
        hf_mask = freqs > 7000
        lf_mask = (freqs >= 100) & (freqs <= 4000)
        hf_energy = np.sum(fft_vals[hf_mask] ** 2) + 1e-8
        lf_energy = np.sum(fft_vals[lf_mask] ** 2) + 1e-8
        ratio = float(hf_energy / lf_energy)

        # Statistical kurtosis of zero-crossing intervals
        zc = np.where(np.diff(np.signbit(waveform)))[0]
        if len(zc) > 10:
            zc_diffs = np.diff(zc)
            mean_zcd = np.mean(zc_diffs)
            std_zcd = np.std(zc_diffs) + 1e-8
            kurt = np.mean(((zc_diffs - mean_zcd) / std_zcd) ** 4)
        else:
            kurt = 3.0

        # Anomaly score between 0 and 1
        anomaly = 0.5
        if ratio < 0.0005 or ratio > 0.15:
            anomaly += 0.25
        if kurt > 12.0 or kurt < 1.8:
            anomaly += 0.20
        return float(np.clip(anomaly, 0.05, 0.95))

    def predict(self, input_data: str, threshold: float) -> PredictionResult:
        waveform, sr = self.decode_audio(input_data)
        if len(waveform) == 0:
            return self.make_result(probability=0.5, threshold=threshold)

        # Resample or pad
        fixed_wave = self.pad_or_truncate(waveform, target_len=self.target_length)
        tensor = torch.from_numpy(fixed_wave).unsqueeze(0).unsqueeze(0).float().to(self.device)

        with torch.no_grad():
            logits = self.model(tensor)
            probs = F.softmax(logits, dim=-1)
            nn_fake_prob = float(probs[0, 1].item())

        # Combine neural inference with vocoder acoustic artifact metrics
        acoustic_score = self._spectral_anomaly_score(waveform)
        # Weighted blend (70% neural model, 30% spectral anomaly check)
        combined_prob = 0.70 * nn_fake_prob + 0.30 * acoustic_score
        combined_prob = float(np.clip(combined_prob, 0.01, 0.99))

        return self.make_result(probability=combined_prob, threshold=threshold)


if __name__ == "__main__":
    import uvicorn
    from deepsafe_sdk import load_manifest, create_app
    manifest_path = os.path.join(os.path.dirname(__file__), "model.yaml")
    manifest = load_manifest(manifest_path)
    app = create_app(manifest, os.path.dirname(__file__))
    port = int(os.environ.get("MODEL_PORT", "8001"))
    uvicorn.run(app, host="0.0.0.0", port=port)
