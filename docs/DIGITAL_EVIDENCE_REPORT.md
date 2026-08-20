# TruthLens — Digital Evidence & Forensic Report Generation (Task 4)

## 1. Purpose

The **TruthLens Digital Evidence and Forensic Report Generation System** creates an auditable case record and downloadable forensic PDF report following multi-source authenticity analysis (Task 1), face identity verification (Task 2), and intelligent contextual assessment (Task 3).

The platform serves as an **AI-assisted forensic screening tool** designed for academic review, project demonstrations, and structured digital evidence preservation.

> **Forensic Notice:** The generated report records the AI-assisted analysis performed by TruthLens. It does not independently establish the authenticity of the media or prove criminal activity.

---

## 2. Architecture & Workflow

```
[ Upload Reference & Suspected Media ]
                 │
                 ▼
[ Task 1: Authenticity Detection (NPR + Ensemble) ]
                 │
                 ▼
[ Task 2: Face Identity Verification (MTCNN + FaceNet) ]
                 │
                 ▼
[ Task 3: Intelligent Decision Engine (TruthLens Rules) ]
                 │
                 ▼
[ Task 4: Evidence Case Creation & SHA-256 Hashing ]
                 │
      ┌──────────┴──────────┐
      ▼                     ▼
[ SQLite Evidence Store ]  [ JSON API Response ]
      │                     (case_id, report_available: true)
      ▼
[ On-Demand PDF Report Generator ]
      │
      ▼
[ Secure PDF Download Endpoint ]
  GET /reports/{case_id}/download
```

**Key Architectural Rules:**
1. **Single Source of Truth:** The PDF report is constructed strictly from the stored case record.
2. **No Redundant Computation:** AI models and face embeddings are **never re-run** during report generation.
3. **No Raw Embedding Exposure:** Biometric feature vectors are processed in memory and never stored or exported.

---

## 3. Case ID System

Every analyzed comparison is assigned a unique, sequential Case ID following the format:

$$\text{TL-YYYY-NNNNNN}$$

- **`TL`**: TruthLens platform prefix
- **`YYYY`**: Four-digit calendar year (e.g., `2026`)
- **`NNNNNN`**: 6-digit zero-padded sequence number (e.g., `000001`)

### Security & Sanitization
Case IDs are validated against the strict regex `^TL-\d{4}-\d{6}$` before any database lookup or file operation, preventing directory traversal (`../`) or injection attacks.

---

## 4. Evidence Hashing & Integrity

To ensure cryptographic integrity of the uploaded evidence without memory exhaustion, files are processed using chunked SHA-256 streaming (64 KB buffers):

$$\text{Uploaded Bytes} \xrightarrow{\text{SHA-256 (64KB chunks)}} \text{64-character hex digest}$$

```
Reference SHA-256: 9f86d081884c7d659a2feaa0c55ad015a3bf4f1b2b0b822cd15d6c15b0f00a08
Suspected SHA-256: 5e884898da28047151d0e56f8dc6292773603d0d6aabbdd62a11ef721d1542d8
```

### Integrity Statement
> The SHA-256 hash uniquely represents the analyzed file contents at the time of processing. Recomputing the hash of the original file at a later date confirms whether the file contents have remained unaltered. SHA-256 provides integrity verification, not proof of authenticity.

---

## 5. Case Record & Storage (`evidence_cases`)

Case records are persisted in the existing SQLite database using SQLAlchemy without altering the legacy `analysis_history` table.

### Schema: `evidence_cases`

| Column | Type | Description |
|---|---|---|
| `id` | `INTEGER PRIMARY KEY` | Auto-increment internal identifier |
| `case_id` | `VARCHAR(32) UNIQUE` | Public identifier (e.g. `TL-2026-000001`) |
| `request_id` | `VARCHAR(64) UNIQUE` | Correlation UUID for API telemetry |
| `created_at` | `VARCHAR(32)` | Analysis start timestamp (UTC ISO-8601) |
| `completed_at` | `VARCHAR(32)` | Analysis completion timestamp (UTC ISO-8601) |
| `processing_seconds` | `FLOAT` | Total pipeline execution time |
| `reference_filename` | `VARCHAR(512)` | Name of reference file (sanitized) |
| `reference_content_type` | `VARCHAR(64)` | MIME type (e.g. `image/jpeg`) |
| `reference_size_bytes` | `INTEGER` | Byte size |
| `reference_width` / `height` | `INTEGER` | Image dimensions in pixels |
| `reference_sha256` | `VARCHAR(64)` | SHA-256 hash of reference file |
| `reference_preview_b64` | `TEXT` | Compressed thumbnail preview (base64) |
| `suspected_filename` | `VARCHAR(512)` | Name of suspected file (sanitized) |
| `suspected_content_type` | `VARCHAR(64)` | MIME type (e.g. `image/png`) |
| `suspected_size_bytes` | `INTEGER` | Byte size |
| `suspected_width` / `height` | `INTEGER` | Image dimensions in pixels |
| `suspected_sha256` | `VARCHAR(64)` | SHA-256 hash of suspected file |
| `suspected_preview_b64` | `TEXT` | Compressed thumbnail preview (base64) |
| `reference_analysis_json` | `TEXT` | Task 1 reference authenticity output |
| `suspected_analysis_json` | `TEXT` | Task 1 suspected authenticity output |
| `face_verification_json` | `TEXT` | Task 2 face identity output |
| `assessment_json` | `TEXT` | Task 3 decision engine output |
| `model_info_json` | `TEXT` | AI models, architectures, and thresholds |
| `report_version` | `VARCHAR(8)` | Report template schema version (`1.0`) |
| `report_generated_at` | `VARCHAR(32)` | Timestamp when PDF was compiled |

---

## 6. Forensic PDF Structure

The report is compiled into a multi-page A4 document styled for academic and professional digital forensics review:

1. **Header & Case Information**: Case ID, Request ID, start/completion UTC timestamps, execution duration, and report version.
2. **Executive Assessment (Task 3)**: Prominent verdict badge (`POTENTIAL DEEPFAKE`, `LIKELY AUTHENTIC`, etc.), risk level (`HIGH` / `MEDIUM` / `LOW`), confidence rating, and the dynamic context explanation.
3. **Reference Media**: Thumbnail, filename, MIME type, dimensions, file size, SHA-256 hash, and AI authenticity score.
4. **Suspected Media**: Thumbnail, filename, MIME type, dimensions, file size, SHA-256 hash, and AI authenticity score.
5. **AI Authenticity Analysis (Task 1)**: Side-by-side comparative table of model predictions, AI scores, real scores, and ensemble verdicts.
6. **Face Identity Verification (Task 2)**: Face detection statuses, face count tallies, cosine similarity percentage, and threshold evaluation.
7. **Evidence Signals Matrix**: Unified summary of all analytical signals driving the final assessment.
8. **Model & Processing Metadata**: Underlying CNN/ViT architectures, face embedding models (InceptionResnetV1), similarity metrics, and ensemble parameters.
9. **Evidence Integrity**: SHA-256 verification instructions and checksums.
10. **Limitations & Legal Disclaimer**: Forensic screening boundaries, false-positive/negative disclosures, biometric privacy notices, and non-statutory status.

---

## 7. API Endpoints

### 1. Analysis & Case Creation
- **Endpoint:** `POST /analyze/compare`
- **Output:** Returns analysis results along with `case_id` and `report_available: true`.

### 2. Forensic Report Download
- **Endpoint:** `GET /reports/{case_id}/download`
- **Response Headers:**
  - `Content-Type: application/pdf`
  - `Content-Disposition: attachment; filename="TruthLens_Report_{case_id}.pdf"`
- **Status Codes:**
  - `200 OK`: PDF stream returned.
  - `400 Bad Request`: Malformed or invalid Case ID.
  - `404 Not Found`: Case ID does not exist in the database.
  - `500 Internal Server Error`: PDF compilation failure.

---

## 8. Security & Privacy

1. **Path Traversal Defense:** Case IDs are strictly validated with regex before database queries or file access.
2. **Path Sanitization:** File system paths (e.g. `/Users/...`) are stripped from all reports and API outputs.
3. **Embedding Protection:** 512-dimensional facial embeddings are discarded after cosine distance computation and never written to disk or the PDF.
4. **Non-Public Storage:** Reports are generated dynamically in memory upon user request rather than exposed via static web directories.
5. **Git Hygiene:** Local database files (`*.db`) and generated artifacts are excluded via `.gitignore`.

---

## 9. Limitations & Ethical Notice

1. **Forensic Screening Tool:** TruthLens is an investigative aid, not a definitive legal adjudication system.
2. **Probabilistic Outputs:** AI scores represent model confidence estimates and should not be interpreted as statistically calibrated probabilities of authenticity.
3. **Biometric Privacy:** Biometric comparison data must be handled in compliance with applicable data protection regulations.
