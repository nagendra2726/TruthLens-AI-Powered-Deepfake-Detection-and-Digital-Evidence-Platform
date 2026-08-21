"""
TruthLens — Texture Forensic Analysis
Extracts Local Binary Pattern (LBP) entropy and spatial texture gradient variance.
"""
from __future__ import annotations

import numpy as np
from PIL import Image
from .schemas import TextureSignals


def compute_lbp_entropy(gray_arr: np.ndarray) -> float:
    """
    Computes Shannon entropy of the 8-neighbor Local Binary Pattern (LBP) histogram.
    Natural photographs have a diverse, rich LBP distribution (higher entropy),
    while synthetic/smoothed AI textures often exhibit lower texture entropy.
    """
    h, w = gray_arr.shape
    if h < 3 or w < 3:
        return 0.0

    # Extract 8-neighborhood using slices
    center = gray_arr[1:-1, 1:-1]
    lbp_code = np.zeros(center.shape, dtype=np.uint8)

    neighbors = [
        gray_arr[:-2, :-2],  # top-left
        gray_arr[:-2, 1:-1],  # top
        gray_arr[:-2, 2:],   # top-right
        gray_arr[1:-1, 2:],  # right
        gray_arr[2:, 2:],    # bottom-right
        gray_arr[2:, 1:-1],  # bottom
        gray_arr[2:, :-2],   # bottom-left
        gray_arr[1:-1, :-2], # left
    ]

    for bit_idx, neighbor in enumerate(neighbors):
        lbp_code |= ((neighbor >= center).astype(np.uint8) << bit_idx)

    # Compute histogram and Shannon entropy
    hist, _ = np.histogram(lbp_code.ravel(), bins=256, range=(0, 256), density=True)
    hist = hist[hist > 0]
    entropy = -float(np.sum(hist * np.log2(hist)))
    return entropy


def extract_texture_signals(rgb_image: Image.Image) -> TextureSignals:
    """Extracts micro-texture statistics and spatial gradient texture metrics."""
    gray = rgb_image.convert("L")
    gray_arr = np.array(gray, dtype=np.float32)

    # 1. LBP entropy
    lbp_entropy = compute_lbp_entropy(gray_arr)

    # 2. Local spatial variance (4x4 tiled variance)
    h, w = gray_arr.shape
    step = 8
    local_vars = []
    for y in range(0, h - step, step):
        for x in range(0, w - step, step):
            tile = gray_arr[y : y + step, x : x + step]
            local_vars.append(float(np.var(tile)))

    local_var_mean = float(np.mean(local_vars)) if local_vars else float(np.var(gray_arr))

    # 3. Spatial gradient texture variance
    dx = np.diff(gray_arr, axis=1)
    dy = np.diff(gray_arr, axis=0)
    grad_tex_var = float((np.var(dx) + np.var(dy)) / 2.0)

    return TextureSignals(
        lbp_entropy=round(lbp_entropy, 4),
        local_variance=round(local_var_mean, 4),
        gradient_texture_variance=round(grad_tex_var, 4),
    )
