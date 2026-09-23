# TruthLens
## AI-Powered Deepfake Detection & Digital Forensics Platform

TruthLens is a self-hosted deepfake detection platform that goes beyond a simple detection score. It produces a full tamper-evident forensic report, verifies face identity between reference and suspect media, and generates cyber complaint drafts — all running on-premise so sensitive media never leaves the investigator's system.

---

## What Makes It Different

| Feature | TruthLens | Commercial APIs |
|---|:---:|:---:|
| **Vision Transformer AI Detection (dima806 ViT)** | ✅ | ✅ |
| **Forensic PDF Report with SHA-256 Hash** | ✅ | ❌ |
| **Face Identity Verification (MTCNN + VGGFace2)** | ✅ | ❌ |
| **ELA / FFT Spectral Pixel Forensic Analysis** | ✅ | ❌ |
| **Cyber Complaint Draft Generator (India — IT Act / BNS)** | ✅ | ❌ |
| **Evidence Case File Package (.zip)** | ✅ | ❌ |
| **Self-Hosted / On-Premise (Data Privacy)** | ✅ | ❌ |
| **Firebase Authentication & History** | ✅ | ❌ |

---

## Core Workflow

```
Login → Dashboard → Start New Analysis → Upload Image
  → Preprocessing (SHA-256, resize, normalize)
  → AI Detection (dima806/deepfake_vs_real_image_detection ViT)
  → Supporting Forensic Analysis (ELA, FFT, Noise, Edges)
  → Optional Face Verification (MTCNN + VGGFace2)
  → Final Assessment: "Likely Real" / "Likely AI-Generated" / "Inconclusive"
  → PDF Report Generation
  → Optional: Case File Package (.zip) on manual request only
  → History Saved (Firestore + localStorage)
```

---

## Local Setup & Running

### Prerequisites
- Python 3.10–3.13 (tested on 3.13.9 with Anaconda)
- Node.js 18+ and npm
- Git

### 1. Clone & Install Backend

```bash
git clone <repository-url>
cd DeepSafe-main

# Install Python dependencies
pip install -r requirements.txt
pip install torch torchvision transformers facenet-pytorch reportlab pillow python-multipart sqlalchemy fastapi uvicorn

# On macOS Python 3.13+: TensorFlow is not required and must not be imported.
# The backend automatically sets USE_TF=0 and USE_TORCH=1 at startup.
```

### 2. Configure Environment

```bash
# Backend (root directory)
cp .env.example .env
# No changes needed for local development defaults.

# Frontend
cp frontend/.env.example frontend/.env
# Edit frontend/.env and add your Firebase API key.
```

### 3. Start the Backend

```bash
python3 -m uvicorn api.main:app --port 8000 --reload
```

The backend will:
- Pre-warm the `dima806/deepfake_vs_real_image_detection` Vision Transformer on first start (downloads ~330MB model once).
- Initialize SQLite database at `deepsafe_history.db`.
- Serve the API at `http://localhost:8000`.
- Serve API docs at `http://localhost:8000/docs`.

### 4. Start the Frontend

```bash
cd frontend
npm install
npm start   # Development server at http://localhost:3000
# OR serve the production build:
# npm run build && npx serve -s build
```

---

## API Reference (Key Endpoints)

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/health` | Health check — returns model load status |
| `POST` | `/api/analyze` | Single image deepfake detection |
| `POST` | `/api/compare` | Comparative two-image analysis + face verification |
| `POST` | `/api/face-verify` | Standalone face verification (MTCNN + VGGFace2) |
| `GET` | `/api/cases/{case_id}` | Retrieve stored case analysis |
| `POST` | `/api/cases/{case_id}/generate` | **Manual** case file (.zip) generation |
| `GET` | `/reports/{case_id}/download` | Download forensic PDF report |
| `GET` | `/reports/{case_id}/case-file/download` | Download case file (.zip) |

> **Note:** Case file generation is **never** triggered automatically. It only runs when the user explicitly clicks "Generate Case File".

---

## AI Model

**Model:** [`dima806/deepfake_vs_real_image_detection`](https://huggingface.co/dima806/deepfake_vs_real_image_detection)  
**Architecture:** Vision Transformer (ViT-base-patch16-224)  
**Labels:** `{0: "Real", 1: "Fake"}`  
**Framework:** PyTorch via HuggingFace Transformers  
**Input:** 224×224 RGB images  
**Output:** Softmax probabilities → `real_probability`, `ai_probability`

---

## Supporting Forensic Analysis

| Module | Description |
|--------|-------------|
| **Error Level Analysis (ELA)** | Detects JPEG re-compression artifacts characteristic of manipulation |
| **FFT Spectral Analysis** | Identifies high-frequency noise patterns from AI generators |
| **Noise Residual Analysis** | Measures pixel noise variance inconsistencies |
| **Edge Coherence** | Evaluates edge distribution using Sobel/Canny operators |
| **Optical Characteristics** | Saturation, dynamic range, brightness distribution |

---

## Running Tests

```bash
# Unit and module tests only (no backend server required):
pytest tests/test_case_file_module.py tests/test_truthlens_api.py -v

# All tests (integration tests skip gracefully if backend is offline):
pytest -v
```

**Test summary (as of final submission):** 96 passed, 20 skipped — 0 failures.

---

## Technology Stack

- **API Gateway:** FastAPI, Uvicorn, Pydantic, Python 3.10+
- **AI / ML:** PyTorch, Transformers (ViT), facenet-pytorch (MTCNN + VGGFace2), scikit-learn
- **Forensic Algorithms:** ELA, 2D FFT, LBP Texture Entropy, Noise Residual, Sobel/Canny Edges
- **Report Generation:** ReportLab (PDF)
- **Database:** SQLite (SQLAlchemy ORM)
- **Frontend:** React 18, React Router v7, Firebase Auth & Firestore
- **Auth:** Firebase Authentication + JWT (backend)
- **Containerisation (optional):** Docker, Docker Compose

---

## Verdict Language

TruthLens uses precise, non-definitive language in all outputs:

| Result | Meaning |
|--------|---------|
| **Likely Real** | AI probability < 45%; forensic indicators consistent with authentic media |
| **Likely AI-Generated** | AI probability ≥ 55%; forensic indicators suggest synthetic generation |
| **Inconclusive** | AI probability 45–55%; signals are mixed; human review recommended |

> Results are investigative aids. They should not be treated as definitive forensic proof without additional expert verification.

---

## Key Limitations

- Novel AI generators not in training distribution may yield lower confidence.
- Face verification requires clear, unoccluded reference images.
- EXIF metadata may be absent or spoofed in processed media.
- This tool is an investigative screening aid; expert verification is recommended for legal proceedings.

---

## Roadmap

- Expanded generator fingerprinting (Midjourney v6, DALL-E 3, Flux, Sora)
- C2PA content provenance verification
- Video temporal coherence analysis (optical flow)
- Scaled production deployment (PostgreSQL + Redis queue)
