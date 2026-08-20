# TruthLens — Multi-Source Authenticity Verification (Task 1)

## 1. Core Problem

Traditional deepfake detection systems analyze only the suspected media file. This introduces a major logical fallacy:

> If both the reference media and suspected media are AI-generated, an isolated analysis of the suspected media might label it as an AI creation, but fails to account for whether the reference itself was genuine. The user or investigator may mistakenly believe a genuine reference was swapped or impersonated when in reality both files are purely synthetic or generated from different sources.

Therefore, **TruthLens** independently analyzes:
1. **Reference media**
2. **Suspected media**

and returns separate, uncoupled authenticity determinations for each. The system **never assumes** that the reference media is genuine simply because the user provided it as a reference.

---

## 2. Existing DeepSafe Workflow

In DeepSafe v1.3:
```
Suspected Media (single file)
      ↓
POST /detect (or POST /predict)
      ↓
Model Ensemble Inference (NPR, UniversalFakeDetect, Cross-Efficient-ViT)
      ↓
Decision Fusion (Voting / Average / Stacking)
      ↓
Single Result: { is_likely_deepfake: true/false, deepfake_probability: 0.xx }
```

---

## 3. New TruthLens Workflow

In TruthLens (Task 1):
```
Reference Media                 Suspected Media
      ↓                               ↓
AI Authenticity Detection       AI Authenticity Detection
(Same Preprocessing & Models)   (Same Preprocessing & Models)
      ↓                               ↓
Reference Authenticity Result   Suspected Authenticity Result
      │                               │
      └───────────────┬───────────────┘
                      ↓
          Combined Compare Response
                      ↓
       Frontend UI (Side-by-Side Cards)
```

> **Important Statement:**
> **"TruthLens independently evaluates the authenticity of the reference and suspected media. An AI-generated classification alone does not establish that the media is a deepfake."**

Contextual assessment, face verification, and deepfake decision engines are scheduled for subsequent tasks (Task 2 & Task 3).

---

## 4. Reference Media Analysis

The first uploaded file is treated strictly as **"Reference Media"** (never presumed to be "Authentic Original").
- Standard prediction classes:
  - `LIKELY_REAL`
  - `LIKELY_AI_GENERATED`
  - `INCONCLUSIVE`
- Confidence levels:
  - `LOW`, `MEDIUM`, `HIGH`, `VERY_HIGH`

---

## 5. Suspected Media Analysis

The second uploaded file is treated as **"Suspected Media"** and undergoes the exact same independent pipeline with identical prediction classes and confidence intervals.

---

## 6. Model Reuse & Performance

- Microservice models (`npr_deepfakedetection`, `universalfakedetect`, `cross_efficient_vit`) remain long-lived services in Docker containers.
- The API gateway queries the already-instantiated microservices in sequence without reloading weights.
- Memory and GPU resources are preserved without duplicating neural network instances.

---

## 7. API Changes

### New Endpoint: `POST /analyze/compare`
- **Path**: `/analyze/compare`
- **Method**: `POST`
- **Content-Type**: `multipart/form-data`
- **Parameters**:
  - `reference_media` (UploadFile, required)
  - `suspected_media` (UploadFile, required)
  - `threshold` (float, optional, default: 0.5)
  - `ensemble_method` (string, optional: `voting` | `average` | `stacking`)

### Sample Response:
```json
{
  "success": true,
  "request_id": "8f0a7b42-1e9c-48d6-953b-092dc0bb5891",
  "processing_time_seconds": 0.45,
  "threshold_used": 0.5,
  "ensemble_method_used": "voting",
  "reference_analysis": {
    "status": "completed",
    "filename": "ref.jpg",
    "prediction": "LIKELY_REAL",
    "ai_probability": 0.04,
    "real_probability": 0.96,
    "confidence": "VERY_HIGH",
    "model_results": { ... }
  },
  "suspected_analysis": {
    "status": "completed",
    "filename": "sus.jpg",
    "prediction": "LIKELY_AI_GENERATED",
    "ai_probability": 0.94,
    "real_probability": 0.06,
    "confidence": "VERY_HIGH",
    "model_results": { ... }
  }
}
```

### Backward Compatibility
- Existing `/detect` and `/predict` endpoints remain 100% untouched and operational.

---

## 8. Frontend Changes

- Added Mode Tab Switcher:
  - **🔍 Single Analysis**: Preserves original DeepSafe single-file upload & chart flow.
  - **⚖️ Compare Media**: Dedicated TruthLens multi-source verification interface with dual drag-and-drop upload zones.
- Side-by-side authenticity cards presenting:
  - Prediction badge (`LIKELY REAL`, `LIKELY AI-GENERATED`, `INCONCLUSIVE`)
  - AI vs. Real probability gauge bars
  - Confidence rating badge
  - Donut chart distribution
  - Expandable breakdown of individual model scores
- Disclaimer banner informing users that independent synthetic detection does not constitute a final deepfake verdict.

---

## 9. Test Scenarios Implemented

All test cases are codified in `tests/test_compare_api.py`:

| Test ID | Scenario | Expected Reference | Expected Suspected | Result |
|---|---|---|---|---|
| **TEST 1** | Real + Real | `LIKELY_REAL` | `LIKELY_REAL` | Passed |
| **TEST 2** | Real + AI | `LIKELY_REAL` | `LIKELY_AI_GENERATED` | Passed |
| **TEST 3** | AI + AI | `LIKELY_AI_GENERATED` | `LIKELY_AI_GENERATED` | Passed |
| **TEST 4** | AI + Real | `LIKELY_AI_GENERATED` | `LIKELY_REAL` | Passed |
| **TEST 5** | Real + Real (Different identities) | `LIKELY_REAL` | `LIKELY_REAL` | Passed |
| **TEST 6** | One file corrupt / invalid | `FAILED` status with error detail | `COMPLETED` | Passed |
| **TEST 7** | Backward Compatibility | `/detect` endpoint functions normally | - | Passed |

---

## 10. Limitations

1. **Standalone Authenticity vs. Deepfake Verdict**: An AI-generated classification on both items simply indicates synthetic origin; determining whether the suspected media is a face-swap or impersonation of the reference requires biometric identity matching (Task 2) and decision synthesis (Task 3).
2. **Model Generalization**: Base deepfake detectors (NPR, UniversalFakeDetect) are sensitive to compression, re-encoding, and novel generative architectures (e.g. latest diffusion models).
3. **CPU In-Memory Limits**: High-resolution video comparison requires sufficient container memory allocation when processing frame batches.
