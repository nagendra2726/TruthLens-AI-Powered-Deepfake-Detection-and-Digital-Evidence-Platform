# TruthLens — Face Identity Verification (Task 2)

## 1. Purpose

The objective of **Face Identity Verification** is to determine:

> *"Does the suspected media likely contain the same person as the reference media?"*

### Independence of Analysis
Deepfake detection and face verification address two orthogonal questions:
- **Authenticity Detection (Task 1)**: *"Does this media exhibit artifacts of AI generation/synthesis?"*
- **Face Verification (Task 2)**: *"Does this media share the same facial identity as the reference?"*

These two pipelines operate independently:
- A face can be real yet represent a different person.
- A face can be synthetic/AI-generated yet successfully impersonate the reference person (face swap / diffusion clone).
- Both results are supplied independently to provide comprehensive digital evidence for the decision engine in Task 3.

> **Important Statement:**
> **"Face verification provides a probabilistic similarity assessment and does not constitute definitive proof of identity."**

---

## 2. Architecture Overview

```
REFERENCE MEDIA                         SUSPECTED MEDIA
      │                                       │
      ▼                                       ▼
┌──────────────┐                       ┌──────────────┐
│ FaceDetector │ (MTCNN)               │ FaceDetector │ (MTCNN)
└──────┬───────┘                       └──────┬───────┘
       │ [Aligned Face Crop]                  │ [All N Aligned Face Crops]
       ▼                                      ▼
┌──────────────┐                       ┌──────────────┐
│ FaceEmbedder │ (InceptionResnetV1)   │ FaceEmbedder │ (InceptionResnetV1)
└──────┬───────┘                       └──────┬───────┘
       │ e_ref: 512-D L2-normalized           │ e_sus: (N, 512) L2-normalized
       │                                      │
       └──────────────────┬───────────────────┘
                          │
                          ▼
              ┌───────────────────────┐
              │ FaceVerifier Decision │
              │ Multi-Face Cosine Sim │
              └───────────┬───────────┘
                          │
                          ▼
            FaceVerificationResult:
            - match: true / false / null
            - result: LIKELY_SAME_PERSON / LIKELY_DIFFERENT_PERSON / UNABLE_TO_VERIFY
            - best_match_score: 0.00 – 1.00
            - best_match_face_index: 1..N
```

---

## 3. Face Detection

- **Engine**: Multi-task Cascaded Convolutional Networks (MTCNN via `facenet-pytorch`).
- **Input**: Preprocessed RGB image.
- **Output**: Aligned, normalized 160×160 pixel face crops.
- **Parameters**:
  - `min_face_size`: 32px
  - `thresholds`: `[0.6, 0.7, 0.7]` (P-Net, R-Net, O-Net)
  - `keep_all`: `True` (detects all faces in crowded scenes)

---

## 4. Face Embedding

- **Architecture**: InceptionResnetV1 pretrained on VGGFace2.
- **Embedding Vector**: 512-dimensional continuous feature space.
- **Normalization**: Unit L2-norm ($\|\mathbf{e}\|_2 = 1.0$) for direct angular comparison.

---

## 5. Similarity Metric & Threshold

### Metric: Cosine Similarity
$$\text{Similarity}(\mathbf{u}, \mathbf{v}) = \frac{\mathbf{u} \cdot \mathbf{v}}{\|\mathbf{u}\|_2 \|\mathbf{v}\|_2} = \mathbf{u} \cdot \mathbf{v}$$

For L2-normalized vectors, cosine similarity is equivalent to the dot product.

### Decision Threshold: `0.65`
- **$\ge 0.65$**: `LIKELY_SAME_PERSON` (`match = true`)
- **$< 0.65$**: `LIKELY_DIFFERENT_PERSON` (`match = false`)
- **No usable face detected**: `UNABLE_TO_VERIFY` (`match = null`)

### Calibration Data
Empirical verification on reference dataset portraits:
- **Same Identity (Self-match)**: Cosine similarity $\approx 1.000$
- **Different Identity (Cross-match)**: Cosine similarity $\approx 0.089 – 0.250$
- Clear separation margin $\Delta > 0.40$ from the 0.65 threshold.

---

## 6. Multiple-Face Handling

When the suspected media contains multiple individuals (crowd, group photos):
1. The primary face in the reference media is extracted as $\mathbf{e}_{\text{ref}}$.
2. All $N$ faces in the suspected media are detected and embedded: $\mathbf{e}_1, \mathbf{e}_2, \dots, \mathbf{e}_N$.
3. Cosine similarity is evaluated pairwise: $s_i = \text{sim}(\mathbf{e}_{\text{ref}}, \mathbf{e}_i)$ for $i \in \{1, \dots, N\}$.
4. The system identifies the **best matching score** $s_{\text{best}} = \max_i s_i$ and the matching face index $i_{\text{best}}$.
5. The UI highlights: *"3 faces detected — best match: Face #2 (93.4%)"*.

---

## 7. Error Handling & Edge Cases

| Scenario | System Behavior | Result Status |
|---|---|---|
| **No face in reference** | Returns diagnostic message without failing pipeline | `UNABLE_TO_VERIFY` |
| **No face in suspected** | Returns diagnostic message without failing pipeline | `UNABLE_TO_VERIFY` |
| **Corrupt image** | Caught by PIL verification handler | `FAILED` (with error message) |
| **Low-resolution / blurred face** | MTCNN confidence filtering rejects sub-threshold crops | `UNABLE_TO_VERIFY` |

---

## 8. Privacy & Security

Biometric facial data requires strict handling:
- **No Raw Embeddings in API**: Embeddings are held in ephemeral PyTorch memory and discarded after response generation.
- **No Biometric Storage**: Vector representations are never persisted to disk or SQLite database.
- **Zero Logging**: Raw 512-dimensional vectors are never printed to stdout or logfiles.

---

## 9. API Integration

### Endpoint: `POST /analyze/compare`
Parameters:
- `reference_media` (UploadFile)
- `suspected_media` (UploadFile)
- `threshold` (float, default: 0.5) — Authenticity threshold
- `face_threshold` (float, default: 0.65) — Biometric threshold

### Response Schema:
```json
{
  "success": true,
  "request_id": "3606ebeb-9a1f-454a-9c9b-84358ea038ec",
  "processing_time_seconds": 2.489,
  "reference_analysis": {
    "status": "completed",
    "prediction": "LIKELY_REAL",
    "ai_probability": 0.04,
    "real_probability": 0.96,
    "confidence": "VERY_HIGH"
  },
  "suspected_analysis": {
    "status": "completed",
    "prediction": "LIKELY_AI_GENERATED",
    "ai_probability": 0.94,
    "real_probability": 0.06,
    "confidence": "VERY_HIGH"
  },
  "face_verification": {
    "status": "completed",
    "reference_face_detected": true,
    "suspected_face_detected": true,
    "reference_faces_count": 1,
    "suspected_faces_count": 2,
    "best_match_score": 0.94,
    "best_match_face_index": 1,
    "match": true,
    "result": "LIKELY_SAME_PERSON",
    "threshold_used": 0.65,
    "message": null
  }
}
```

---

## 10. Limitations

1. **Severe Occlusions**: Heavy sunglasses, masks, or extreme profile angles (>60° yaw) may impede MTCNN landmark alignment.
2. **Extreme Lighting**: High underexposure or lens flare can degrade embedding accuracy.
3. **Probabilistic Confidence**: Verification establishes statistical similarity in deep latent space, not legal identification.
