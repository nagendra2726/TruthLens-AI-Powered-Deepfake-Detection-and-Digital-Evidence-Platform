"""
TruthLens — Color Forensic Analysis
Extracts RGB and HSV statistical metrics to evaluate color distribution and saturation characteristics.
"""
from __future__ import annotations

import numpy as np
from PIL import Image
from .schemas import ColorSignals


def extract_color_signals(rgb_image: Image.Image) -> ColorSignals:
    """Computes color channel variance, HSV saturation statistics, and chrominance richness."""
    rgb_arr = np.array(rgb_image.convert("RGB"), dtype=np.float32)

    # 1. RGB channel standard deviations
    r_chan, g_chan, b_chan = rgb_arr[:, :, 0], rgb_arr[:, :, 1], rgb_arr[:, :, 2]
    rgb_std = float((np.std(r_chan) + np.std(g_chan) + np.std(b_chan)) / 3.0)

    # 2. HSV saturation statistics
    hsv_image = rgb_image.convert("HSV")
    hsv_arr = np.array(hsv_image, dtype=np.float32)
    # Saturation channel is normalized to [0, 1]
    sat_chan = hsv_arr[:, :, 1] / 255.0
    sat_mean = float(np.mean(sat_chan))
    sat_std = float(np.std(sat_chan))

    # 3. Chrominance richness (opposing channel variance)
    rg_var = float(np.var(r_chan - g_chan))
    rb_var = float(np.var(r_chan - b_chan))
    chroma_richness = float((rg_var + rb_var) / 2.0)

    return ColorSignals(
        rgb_channel_std=round(rgb_std, 4),
        hsv_saturation_mean=round(sat_mean, 4),
        hsv_saturation_std=round(sat_std, 4),
        chrominance_richness=round(chroma_richness, 4),
    )
