# TruthLens — Task 6: Multi-Signal Pixel-Level Image Forensics & Evidence Fusion

## 1. Executive Summary & Academic Rationale
Standard deepfake detection systems often suffer from over-reliance on single black-box deep learning classifiers, leading to brittle predictions (e.g. abrupt 100% vs 0% outputs) and vulnerability to adversarial perturbation or compression artifacts.

**TruthLens Task 6** introduces an explainable multi-signal forensic layer that pairs AI model ensemble predictions with deterministic pixel-level statistical features and non-deterministic EXIF metadata.

```
                           INPUT IMAGE
                                │
        ┌───────────────────────┼───────────────────────┐
        ↓                       ↓                       ↓
 AI MODEL ENSEMBLE        PIXEL FORENSICS        METADATA ANALYSIS
 (NPR / UFD / Stacking)   (Statistical signals)  (EXIF / Container)
        │                       │                       │
        │             ┌─────────┼─────────┐             │
        │             ↓         ↓         ↓             │
        │           Noise    Texture    Color           │
        │             ↓         ↓         ↓             │
        │           Edges   Frequency                   │
        │                       │                       │
        └───────────────────────┼───────────────────────┘
                                ↓
                         EVIDENCE FUSION
                                ↓
                      FUSED AI-LIKELIHOOD
                                ↓
                    Task 3: Decision Engine
                                ↓
                    Task 4: Forensic Report
                                ↓
                    Task 5: Cybercrime Pack
```

---

## 2. Forensic Signal Components

### 2.1 Noise & Sensor Residual Analysis (`noise.py`)
- **Methodology**: Applies spatial filtering ($3 \times 3$ Box Blur) to compute the residual $R = I_{\text{original}} - I_{\text{denoised}}$.
- **Extracted Signals**:
  - `mean_residual`: Mean residual deviation.
  - `residual_variance`: Variance of noise residual (reflecting physical CMOS sensor photon shot noise).
  - `spatial_consistency`: Patch-wise noise uniformity across a $4 \times 4$ spatial grid.

### 2.2 Micro-Texture Analysis (`texture.py`)
- **Methodology**: Vectorized 8-neighbor Local Binary Pattern (LBP) histogram extraction.
- **Extracted Signals**:
  - `lbp_entropy`: Shannon entropy $H = -\sum p_i \log_2(p_i)$ of micro-texture distributions.
  - `local_variance`: Neighborhood spatial variance across $8 \times 8$ local tiles.
  - `gradient_texture_variance`: Variance of horizontal and vertical spatial derivatives.

### 2.3 Color & Chrominance Distribution (`color.py`)
- **Methodology**: RGB and HSV color space decomposition.
- **Extracted Signals**:
  - `rgb_channel_std`: Average standard deviation across RGB channels.
  - `hsv_saturation_mean` & `hsv_saturation_std`: Color saturation mean and variance.
  - `chrominance_richness`: Cross-channel covariance $(R-G)$ and $(R-B)$ measuring natural organic skin and environmental lighting.

### 2.4 Edge & Structural Gradient Analysis (`edges.py`)
- **Methodology**: Sobel operator convolution ($G_x, G_y$) and Canny edge density.
- **Extracted Signals**:
  - `edge_density`: Proportion of strong structural edge pixels.
  - `gradient_mean` & `gradient_variance`: Energy distribution of boundary gradients.
  - `orientation_entropy`: Directional entropy across edge gradient vectors.

### 2.5 Frequency-Domain Analysis (`frequency.py`)
- **Methodology**: 2D Fast Fourier Transform (FFT) centered power spectrum $\Phi(u, v) = |\mathcal{F}(u, v)|^2$.
- **Extracted Signals**:
  - `low_freq_energy`: Power concentrated in central circular radial band ($r \le 0.25 r_{\max}$).
  - `high_freq_energy`: Power concentrated in outer annular band ($r \ge 0.60 r_{\max}$).
  - `high_low_ratio`: Spectral ratio $\frac{E_{\text{high}}}{E_{\text{low}}}$.
  - `spectral_entropy`: Information entropy of the 2D power spectrum.

### 2.6 Metadata & EXIF Analysis (`metadata.py`) — Supporting Evidence Only
- **Strict Isolation**: EXIF data is **NEVER** used to directly classify an image as real or fake.
- **Extracted Fields**:
  - `camera_make` & `camera_model` (e.g. Apple iPhone 15, Canon EOS).
  - `software` (e.g. Adobe Photoshop, Midjourney Web).
  - `gps_present` (Boolean flag only; raw geographical coordinates are suppressed for privacy).

---

## 3. Evidence Fusion & Signal Agreement (`fusion.py`)

### 3.1 Transparent Weighted Fusion
$$P_{\text{fused}} = w_{\text{ai}} \cdot P_{\text{ai}} + w_{\text{forensic}} \cdot P_{\text{forensic}}$$
- Default weights: $w_{\text{ai}} = 0.70$, $w_{\text{forensic}} = 0.30$.
- Normalized automatically such that $w_{\text{ai}} + w_{\text{forensic}} = 1.0$.

### 3.2 Signal Agreement Rules
| AI Model Prediction | Pixel Forensic Prediction | Signal Agreement | Fused Confidence |
| :--- | :--- | :--- | :--- |
| `LIKELY_AI_GENERATED` | `LIKELY_AI_GENERATED` | **`AGREE`** | **VERY_HIGH / HIGH** |
| `LIKELY_REAL` | `LIKELY_REAL` | **`AGREE`** | **VERY_HIGH / HIGH** |
| `LIKELY_AI_GENERATED` | `LIKELY_REAL` | **`DISAGREE`** | **MEDIUM / LOW** (Flagged for Review) |
| `LIKELY_REAL` | `LIKELY_AI_GENERATED` | **`DISAGREE`** | **MEDIUM / LOW** (Flagged for Review) |
| Any `INCONCLUSIVE` | Any | **`PARTIAL`** | **LOW** |

---

## 4. Integration with Tasks 1–5
1. **Task 1 (Authenticity)**: Single and compare endpoints enrich `AuthenticityResult` with `pixel_forensics` and `evidence_fusion`.
2. **Task 2 (Face Verification)**: Operates concurrently on detected face regions.
3. **Task 3 (Decision Engine)**: Consumes the fused authenticity probability and calibrated confidence.
4. **Task 4 (Forensic PDF Report)**: Section 4B displays the multi-signal forensic breakdown, agreement badge, and supporting EXIF metadata.
5. **Task 5 (Cybercrime Complaint Assistance)**: Packs multi-signal forensic findings into neutral, reviewable complaint drafts and evidence ZIP archives.
