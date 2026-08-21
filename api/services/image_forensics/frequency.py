"""
TruthLens — Frequency-Domain Forensic Analysis
Extracts 2D Fast Fourier Transform (FFT) spectral energy distribution and high/low frequency ratios.
"""
from __future__ import annotations

import numpy as np
from PIL import Image
from .schemas import FrequencySignals


def extract_frequency_signals(rgb_image: Image.Image) -> FrequencySignals:
    """
    Computes 2D FFT magnitude spectrum to evaluate spectral power distribution.
    Generative models (diffusion models, GANs) frequently display frequency domain artifacts
    or high-frequency attenuation compared to optical camera sensors.
    """
    gray = rgb_image.convert("L")
    img_arr = np.array(gray, dtype=np.float32)
    h, w = img_arr.shape

    if h < 8 or w < 8:
        return FrequencySignals(
            low_freq_energy=0.0,
            high_freq_energy=0.0,
            high_low_ratio=0.0,
            spectral_entropy=0.0,
        )

    # 1. 2D FFT and centered shift
    fft2d = np.fft.fft2(img_arr)
    fft_shifted = np.fft.fftshift(fft2d)
    power_spectrum = np.abs(fft_shifted) ** 2

    # 2. Radial frequency grid
    cy, cx = h // 2, w // 2
    y_indices, x_indices = np.ogrid[:h, :w]
    radii = np.sqrt((y_indices - cy) ** 2 + (x_indices - cx) ** 2)
    max_radius = min(cy, cx)

    if max_radius <= 0:
        return FrequencySignals(
            low_freq_energy=0.0,
            high_freq_energy=0.0,
            high_low_ratio=0.0,
            spectral_entropy=0.0,
        )

    # Radial masks
    low_freq_mask = radii <= (0.25 * max_radius)
    high_freq_mask = radii >= (0.60 * max_radius)

    low_energy = float(np.sum(power_spectrum[low_freq_mask]))
    high_energy = float(np.sum(power_spectrum[high_freq_mask]))
    total_energy = float(np.sum(power_spectrum)) + 1e-10

    high_low_ratio = float(high_energy / (low_energy + 1e-6))

    # 3. Spectral entropy
    normalized_power = power_spectrum / total_energy
    valid_power = normalized_power[normalized_power > 0]
    spectral_entropy = -float(np.sum(valid_power * np.log2(valid_power)))

    return FrequencySignals(
        low_freq_energy=round(low_energy / total_energy, 4),
        high_freq_energy=round(high_energy / total_energy, 4),
        high_low_ratio=round(high_low_ratio, 6),
        spectral_entropy=round(spectral_entropy, 4),
    )
