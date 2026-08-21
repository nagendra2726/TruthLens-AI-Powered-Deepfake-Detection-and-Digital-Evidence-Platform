"""
TruthLens — Edge & Gradient Forensic Analysis
Analyzes spatial derivative magnitudes, edge density, and gradient orientation statistics.
"""
from __future__ import annotations

import numpy as np
from PIL import Image
from .schemas import EdgeSignals


def extract_edge_signals(rgb_image: Image.Image) -> EdgeSignals:
    """Computes edge density, gradient magnitude mean, variance, and orientation entropy."""
    gray = rgb_image.convert("L")
    img_arr = np.array(gray, dtype=np.float32)
    h, w = img_arr.shape

    if h < 3 or w < 3:
        return EdgeSignals(
            edge_density=0.0,
            gradient_mean=0.0,
            gradient_variance=0.0,
            orientation_entropy=0.0,
        )

    # 1. Sobel kernels for spatial gradients
    # Gx kernel: [[-1, 0, 1], [-2, 0, 2], [-1, 0, 1]]
    # Gy kernel: [[-1, -2, -1], [0, 0, 0], [1, 2, 1]]
    gx = (
        img_arr[:-2, 2:] + 2 * img_arr[1:-1, 2:] + img_arr[2:, 2:]
        - (img_arr[:-2, :-2] + 2 * img_arr[1:-1, :-2] + img_arr[2:, :-2])
    )
    gy = (
        img_arr[2:, :-2] + 2 * img_arr[2:, 1:-1] + img_arr[2:, 2:]
        - (img_arr[:-2, :-2] + 2 * img_arr[:-2, 1:-1] + img_arr[:-2, 2:])
    )

    magnitude = np.sqrt(gx**2 + gy**2)
    grad_mean = float(np.mean(magnitude))
    grad_var = float(np.var(magnitude))

    # 2. Edge density: fraction of pixels with significant edge magnitude
    # Adaptive threshold = mean + std
    edge_threshold = grad_mean + 0.75 * np.std(magnitude)
    edge_pixels = (magnitude > edge_threshold).astype(np.float32)
    edge_density = float(np.mean(edge_pixels))

    # 3. Orientation entropy
    angles = np.arctan2(gy, gx) + np.pi  # Range [0, 2*pi]
    # Filter strong edge pixels only to compute orientation distribution
    strong_angles = angles[magnitude > edge_threshold]
    if len(strong_angles) > 10:
        hist, _ = np.histogram(strong_angles, bins=16, range=(0, 2 * np.pi), density=True)
        hist = hist[hist > 0]
        orient_entropy = -float(np.sum(hist * np.log2(hist)))
    else:
        orient_entropy = 0.0

    return EdgeSignals(
        edge_density=round(edge_density, 4),
        gradient_mean=round(grad_mean, 4),
        gradient_variance=round(grad_var, 4),
        orientation_entropy=round(orient_entropy, 4),
    )
