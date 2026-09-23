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

## Deploying on Render

TruthLens is configured for deployment on Render with a two-service architecture:

```
┌─────────────────────────────────┐       ┌─────────────────────────────────┐
│       Render Static Site        │       │       Render Web Service        │
│    (React Frontend — CRA)       │ ───▶  │      (FastAPI Python API)       │
│                                 │       │                                 │
│  • Build: npm run build         │       │  • Runtime: Python              │
│  • Publish dir: build           │       │  • Build: pip install -r ...    │
│  • SPA Rewrites: _redirects     │       │  • Start: uvicorn api.main:app  │
│  • Env: REACT_APP_API_URL       │       │  • Health check: /api/health    │
└─────────────────────────────────┘       └─────────────────────────────────┘
```

You can deploy via the provided [`render.yaml`](./render.yaml) Blueprint or manually through the Render Dashboard:

### 1. Backend: Render Web Service

- **Name:** `truthlens-api`
- **Environment:** `Python`
- **Region:** `Oregon` (or closest region)
- **Branch:** `main`
- **Root Directory:** (leave blank — project root)
- **Build Command:** `pip install -r api/requirements.txt`
- **Start Command:** `uvicorn api.main:app --host 0.0.0.0 --port $PORT`
- **Health Check Path:** `/api/health`
- **Environment Variables:**
  - `PORT`: `10000` (Render sets `$PORT` automatically)
  - `SECRET_KEY`: `<generate-a-secure-random-string>`
  - `FRONTEND_URL`: `https://truthlens-frontend.onrender.com` (your frontend static site URL)
  - `USE_TF`: `0`
  - `USE_TORCH`: `1`

### 2. Frontend: Render Static Site

- **Name:** `truthlens-frontend`
- **Branch:** `main`
- **Root Directory:** `frontend`
- **Build Command:** `npm install && npm run build`
- **Publish Directory:** `build`
- **SPA Rewrites:** Pre-configured in `frontend/public/_redirects` (`/*  /index.html  200`)
- **Environment Variables:**
  - `REACT_APP_API_URL`: `https://truthlens-api.onrender.com` (your backend URL)

### 3. Firebase Authorized Domains

After Render generates your frontend domain:
1. Open the [Firebase Console](https://console.firebase.google.com/) → Your Project (`truthlens-6aa27`).
2. Navigate to **Authentication** → **Settings** → **Authorized Domains**.
3. Add your Render frontend domain (e.g., `truthlens-frontend.onrender.com`).

---

## Key Limitations

- **Ephemeral Storage on Render Free Tier:** Render Web Services use an ephemeral filesystem. SQLite database records and temporary uploads are cleared when the container restarts or spins down. For permanent case retention, configure a persistent disk or set `DATABASE_URL` to an external PostgreSQL instance.
- **Render Free Tier Spin-Down:** Free instances spin down after 15 minutes of inactivity. The initial request after spin-down may take ~30–50 seconds while the container initializes and pre-warms the Vision Transformer model.
- **Novel AI Generators:** Unseen generative architectures not represented in the training distribution may yield lower confidence.
- **Face Verification:** Requires clear, unoccluded reference images.
- **Forensic Scope:** TruthLens is an investigative screening tool; expert verification is recommended for legal proceedings.

---

## Roadmap

- Expanded generator fingerprinting (Midjourney v6, DALL-E 3, Flux, Sora)
- C2PA content provenance verification
- Video temporal coherence analysis (optical flow)
- Scaled production deployment (PostgreSQL + Redis queue)
