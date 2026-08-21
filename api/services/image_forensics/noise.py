"""
TruthLens — Noise & Residual Forensic Analysis
Extracts noise residual features using spatial filtering to evaluate sensor noise consistency.
"""
from __future__ import annotations

import numpy as np
from PIL import Image, ImageFilter
from .schemas import NoiseSignals


def extract_noise_signals(rgb_image: Image.Image) -> NoiseSignals:
    """
    Computes noise residual statistics by subtracting a smoothed filter from the original image.
    Natural camera images exhibit standard Poisson/Gaussian sensor noise across all patches,
    whereas AI-generated images often lack sensor noise or have spatial noise discrepancies.
    """
    gray = rgb_image.convert("L")
    img_arr = np.array(gray, dtype=np.float32)

    # 1. Spatial smoothing filter (3x3 box blur)
    smoothed_img = gray.filter(ImageFilter.BoxBlur(1))
    smoothed_arr = np.array(smoothed_img, dtype=np.float32)

    # 2. Noise residual: Original - Denoised
    residual = img_arr - smoothed_arr

    mean_res = float(np.mean(residual))
    res_var = float(np.var(residual))
    mean_abs_res = float(np.mean(np.abs(residual)))

    # 3. Spatial consistency across 4x4 image patches
    h, w = img_arr.shape
    patch_h, patch_w = max(4, h // 4), max(4, w // 4)
    patch_vars = []

    for i in range(4):
        for j in range(4):
            patch = residual[i * patch_h : (i + 1) * patch_h, j * patch_w : (j + 1) * patch_w]
            if patch.size > 0:
                patch_vars.append(float(np.var(patch)))

    if len(patch_vars) > 1 and np.mean(patch_vars) > 0:
        # Coefficient of variation of patch noise (0.0 to 1.0)
        cv = float(np.std(patch_vars) / (np.mean(patch_vars) + 1e-6))
        spatial_consistency = float(np.clip(1.0 - min(1.0, cv), 0.0, 1.0))
    else:
        spatial_consistency = 0.5

    return NoiseSignals(
        mean_residual=round(mean_res, 6),
        residual_variance=round(res_var, 6),
        mean_absolute_residual=round(mean_abs_res, 6),
        spatial_consistency=round(spatial_consistency, 4),
    )
