# TruthLens — Intelligent Decision Engine (Task 3)

## 1. Purpose

The **TruthLens Decision Engine** synthesises the results of two independent analysis pipelines:

| Pipeline | Source | Question Answered |
|---|---|---|
| **Task 1 — Authenticity Detection** | NPR AI + Ensemble | *"Does this media appear AI-generated?"* |
| **Task 2 — Face Identity Verification** | MTCNN + FaceNet | *"Does the suspected face match the reference?"* |

The Decision Engine consumes these outputs and applies a **transparent, priority-ordered rule set** to produce a single contextual assessment.

> **Core Principle:** AI-Generated ≠ Deepfake. Face Match ≠ Deepfake. Both signals must be evaluated together.

---

## 2. Architecture

```
Task 1 Results                        Task 2 Results
(reference_analysis)                  (face_verification)
(suspected_analysis)
        │                                    │
        └──────────────┬─────────────────────┘
                       ↓
              DECISION ENGINE
              api/services/decision_engine/
              ├── analyzer.py     ← orchestrator
              ├── rules.py        ← pure deterministic rules
              ├── schemas.py      ← Pydantic models
              └── __init__.py     ← package exports
                       ↓
              AssessmentResult
              (category, risk_level, confidence,
               explanation, signals, disclaimer)
```

**The Decision Engine:**
- Does NOT run any AI detection model.
- Does NOT perform face recognition.
- Is a pure Python rule engine with deterministic logic.

---

## 3. Inputs

The engine accepts the exact response structures from Task 1 and Task 2:

```json
{
  "reference_analysis": {
    "status": "completed",
    "prediction": "LIKELY_REAL | LIKELY_AI_GENERATED | INCONCLUSIVE",
    "ai_probability": 0.04,
    "real_probability": 0.96,
    "confidence": "HIGH"
  },
  "suspected_analysis": {
    "status": "completed",
    "prediction": "LIKELY_AI_GENERATED",
    "ai_probability": 0.94,
    "real_probability": 0.06,
    "confidence": "HIGH"
  },
  "face_verification": {
    "status": "completed",
    "result": "LIKELY_SAME_PERSON | LIKELY_DIFFERENT_PERSON | UNABLE_TO_VERIFY",
    "best_match_score": 0.887,
    "match": true
  }
}
```

---

## 4. Assessment Categories

| Category | Human Label | Description |
|---|---|---|
| `LIKELY_AUTHENTIC` | ✅ Likely Authentic | Both media appear real, faces match |
| `POTENTIAL_DEEPFAKE` | ⚠️ Potential Deepfake | Real reference + AI suspected + same face |
| `BOTH_MEDIA_APPEAR_SYNTHETIC` | ℹ️ Both Media Appear Synthetic | Both AI-generated; face match is irrelevant |
| `AI_GENERATED_MEDIA_DIFFERENT_PERSON` | 🔍 AI-Generated — Different Person | Suspected is AI, but face doesn't match reference |
| `SYNTHETIC_REFERENCE_AUTHENTIC_SUSPECTED` | ℹ️ Synthetic Reference | AI reference + real suspected |
| `AUTHENTIC_MEDIA_DIFFERENT_PERSON` | 👥 Authentic — Different Person | Both real, faces differ |
| `INCONCLUSIVE` | ❓ Inconclusive | Insufficient or contradictory signals |
| `UNABLE_TO_VERIFY` | 🚫 Unable to Verify | Analysis pipeline failed |

---

## 5. Decision Matrix

| Reference | Suspected | Face Verification | Category | Risk |
|---|---|---|---|---|
| `LIKELY_REAL` | `LIKELY_REAL` | `LIKELY_SAME_PERSON` | `LIKELY_AUTHENTIC` | LOW |
| `LIKELY_REAL` | `LIKELY_AI_GENERATED` | `LIKELY_SAME_PERSON` | `POTENTIAL_DEEPFAKE` | HIGH |
| `LIKELY_AI_GENERATED` | `LIKELY_AI_GENERATED` | `LIKELY_SAME_PERSON` | `BOTH_MEDIA_APPEAR_SYNTHETIC` | MEDIUM |
| `LIKELY_AI_GENERATED` | `LIKELY_AI_GENERATED` | `LIKELY_DIFFERENT_PERSON` | `BOTH_MEDIA_APPEAR_SYNTHETIC` | MEDIUM |
| `LIKELY_REAL` | `LIKELY_AI_GENERATED` | `LIKELY_DIFFERENT_PERSON` | `AI_GENERATED_MEDIA_DIFFERENT_PERSON` | LOW |
| `LIKELY_AI_GENERATED` | `LIKELY_REAL` | `LIKELY_SAME_PERSON` | `SYNTHETIC_REFERENCE_AUTHENTIC_SUSPECTED` | LOW |
| `LIKELY_AI_GENERATED` | `LIKELY_REAL` | `LIKELY_DIFFERENT_PERSON` | `SYNTHETIC_REFERENCE_AUTHENTIC_SUSPECTED` | LOW |
| `LIKELY_REAL` | `LIKELY_REAL` | `LIKELY_DIFFERENT_PERSON` | `AUTHENTIC_MEDIA_DIFFERENT_PERSON` | LOW |
| `INCONCLUSIVE` | *any* | *any* | `INCONCLUSIVE` | UNKNOWN |
| *any* | `INCONCLUSIVE` | *any* | `INCONCLUSIVE` | UNKNOWN |
| *any* | *any* | `UNABLE_TO_VERIFY` | `INCONCLUSIVE` | UNKNOWN |
| *analysis failed* | *any* | *any* | `UNABLE_TO_VERIFY` | UNKNOWN |

---

## 6. Rule Priority (Highest First)

1. Missing/failed analysis → `UNABLE_TO_VERIFY`
2. Either prediction `INCONCLUSIVE` → `INCONCLUSIVE`
3. Face verification `UNABLE_TO_VERIFY` → `INCONCLUSIVE`
4. Both media `LIKELY_AI_GENERATED` → `BOTH_MEDIA_APPEAR_SYNTHETIC` (regardless of face result)
5. Reference `LIKELY_REAL` + Suspected `LIKELY_AI_GENERATED` + Same face → `POTENTIAL_DEEPFAKE`
6. Reference `LIKELY_REAL` + Suspected `LIKELY_AI_GENERATED` + Different face → `AI_GENERATED_MEDIA_DIFFERENT_PERSON`
7. Reference `LIKELY_AI_GENERATED` + Suspected `LIKELY_REAL` → `SYNTHETIC_REFERENCE_AUTHENTIC_SUSPECTED`
8. Both `LIKELY_REAL` + Same face → `LIKELY_AUTHENTIC`
9. Both `LIKELY_REAL` + Different face → `AUTHENTIC_MEDIA_DIFFERENT_PERSON`
10. Anything else → `INCONCLUSIVE`

> Rule 4 ensures AI+AI+Same never becomes `POTENTIAL_DEEPFAKE`. This is the most critical rule.

---

## 7. Risk Levels

| Risk Level | Assigned To | Meaning |
|---|---|---|
| `HIGH` | `POTENTIAL_DEEPFAKE` | Strong signals consistent with identity manipulation |
| `MEDIUM` | `BOTH_MEDIA_APPEAR_SYNTHETIC` | Context unclear; both media synthetic |
| `LOW` | `LIKELY_AUTHENTIC`, `AUTHENTIC_MEDIA_DIFFERENT_PERSON`, `AI_GENERATED_MEDIA_DIFFERENT_PERSON`, `SYNTHETIC_REFERENCE_AUTHENTIC_SUSPECTED` | Low evidence of deepfake targeting |
| `UNKNOWN` | `INCONCLUSIVE`, `UNABLE_TO_VERIFY` | Insufficient signals to assess risk |

---

## 8. Confidence Derivation

Overall confidence is derived from all three independent signal streams:

| Condition | Confidence |
|---|---|
| Either prediction is `INCONCLUSIVE` | `LOW` |
| Face verification is `UNABLE_TO_VERIFY` | `MEDIUM` |
| All three signals strong & consistent | `HIGH` |
| At least one signal strong | `MEDIUM` |
| No strong signal | `LOW` |

A "strong" signal means:
- Authenticity: `ai_probability > 0.80` or `ai_probability < 0.20`
- Face similarity: `score > 0.80` or `score < 0.40`

> Confidence is never inherited from individual model confidence ratings. It is derived holistically.

---

## 9. Explanations

Every assessment includes a dynamically generated human-readable explanation incorporating actual probability values and face similarity scores. Explanations are never hardcoded — they are generated from actual signal values in `rules.py::build_explanation()`.

---

## 10. Edge Cases

| Case | Handling |
|---|---|
| `reference_analysis = None` | Treated as `INCONCLUSIVE` prediction → `UNABLE_TO_VERIFY` |
| `suspected_analysis = None` | Treated as `INCONCLUSIVE` prediction → `UNABLE_TO_VERIFY` |
| `face_verification = None` | Treated as `UNABLE_TO_VERIFY` → `INCONCLUSIVE` |
| Analysis `status = "failed"` | Prediction forced to `INCONCLUSIVE` |
| Missing probability fields | Handled gracefully; confidence degrades |
| Multiple faces in suspected | Best-match face index used; multi-face note in explanation |
| Exception in Decision Engine | Caught in `main.py`; returns safe `UNABLE_TO_VERIFY` fallback |

---

## 11. API Response

### `POST /analyze/compare` — Full Response Schema

```json
{
  "success": true,
  "request_id": "...",
  "processing_time_seconds": 2.49,
  "reference_analysis": { "..." },
  "suspected_analysis": { "..." },
  "face_verification": { "..." },
  "assessment": {
    "category": "POTENTIAL_DEEPFAKE",
    "risk_level": "HIGH",
    "confidence": "HIGH",
    "explanation": "The reference media appears authentic (AI probability: 4.0%), while the suspected media appears AI-generated (AI probability: 94.0%). The detected face is highly similar to the reference (similarity: 88.7%). This combination is consistent with a potential deepfake, but the result is not definitive proof.",
    "signals": {
      "reference_authenticity": "LIKELY_REAL",
      "suspected_authenticity": "LIKELY_AI_GENERATED",
      "face_verification": "LIKELY_SAME_PERSON",
      "reference_ai_probability": 0.04,
      "suspected_ai_probability": 0.94,
      "face_similarity_score": 0.887,
      "face_match": true
    },
    "disclaimer": "This assessment is an AI-assisted forensic screening result and should not be treated as definitive proof of manipulation, identity, or criminal activity."
  }
}
```

---

## 12. Limitations

1. **Not Legal Proof**: TruthLens provides forensic screening. Results are probabilistic and should not be used as standalone legal evidence.
2. **AI Detection Accuracy**: Authenticity detection depends on the underlying NPR model. Novel deepfake techniques not present in training data may evade detection.
3. **Face Verification Constraints**: MTCNN may fail on severely occluded, low-resolution, or extreme-angle faces, leading to `UNABLE_TO_VERIFY`.
4. **No Temporal Analysis**: The Decision Engine does not consider temporal consistency across video frames.
5. **Context-Free**: The Decision Engine does not consider document metadata, provenance chains, EXIF data, or upload source.

---

## 13. Disclaimer

> This assessment is an AI-assisted forensic screening result and should not be treated as definitive proof of manipulation, identity, or criminal activity.
