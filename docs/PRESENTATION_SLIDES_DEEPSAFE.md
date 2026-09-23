# DeepSafe / TruthLens — Presentation Deck (10 Slides)

---

## Slide 1 — THE PROBLEM
- **Headline:** Deepfakes are growing faster than human detection.
- **Context:** In 2026, AI-generated synthetic media (GANs, Diffusion, Neural Vocoders) is visually and aurally indistinguishable from authentic media to the human eye.
- **The Threat:** Digital identity impersonation, evidence tampering, financial fraud, and disinformation campaigns.

---

## Slide 2 — EXISTING TOOLS AND THEIR LIMITS
- **Commercial APIs (Sightengine, Hive, Optic):**
  - Return a bare percentage score (e.g. 87% fake).
  - No chain of custody or tamper-evident hashing.
  - No face identity verification against reference media.
  - No formal forensic investigation report or complaint draft.
  - Require uploading sensitive media to third-party cloud servers.

---

## Slide 3 — DEEPSAFE SOLUTION
- **Core Value Proposition:** A complete, self-hosted forensic investigation platform — not just a detector.
- **Three Pillars:** **Detect** · **Verify** · **Report**
- **Privacy Assurance:** Sensitivity guaranteed — data never leaves your infrastructure.

---

## Slide 4 — ARCHITECTURE & WORKFLOW
- **Pipeline:** Media Upload -> API Gateway (:8000) -> Parallel Microservices -> Decision Engine / Meta-Learner -> Tamper-Evident PDF Report
- **Microservices:**
  - NPR Deepfake Detector (:5001)
  - UniversalFakeDetect (:5004)
  - Cross-Efficient ViT Video (:7001)
  - AASIST Audio Detector (:8001)
  - MTCNN + VGGFace2 Face Verifier

---

## Slide 5 — LIVE DEMO & USE CASES
- **Case 1 (Same Person):** Reference & Suspect media match face identity; AI Detection Score < 5% -> LIKELY AUTHENTIC — SAME PERSON
- **Case 2 (AI Image):** Stable Diffusion / Midjourney output -> LIKELY AI-GENERATED (Generator: Diffusion, Confidence: 88.5%)
- **Case 3 (Impersonation):** Authentic media, different individuals -> AUTHENTIC MEDIA — DIFFERENT PERSON
- **Case 4 (Synthetic Voice):** Audio deepfake -> LIKELY SYNTHETIC AUDIO (AASIST Spectro-Temporal Model)

---

## Slide 6 — THE FORENSIC REPORT
- **PDF Report Structure (3 Pages Max):**
  - Section 1: Executive Assessment & Verdict Box (with DISAGREE warnings)
  - Section 2 & 3: Reference & Suspected Media SHA-256 Hashes
  - Section 4: AI Authenticity Analysis & Generator Fingerprint
  - Section 4B: Multi-Signal Pixel Forensics & Signal Agreement Notes
  - Section 5: Face Identity Verification & Cosine Similarity
  - Section 6-8: Model Info, Evidence Integrity & Limitations
  - Section 9: Technical Appendix — Forensic Signal Detail

---

## Slide 7 — HOW IT WORKS (TECHNICAL DETAILS)
- **NPR (Nearest Neighbor Resampling):** Detects upsampling and frequency artifacts left by GAN/Diffusion architectures.
- **UniversalFakeDetect (CLIP ViT-L/14):** Generalizes feature extraction to detect unseen generative models.
- **AASIST Audio:** SincConv front-end + spectro-temporal graph attention for raw waveform voice clone detection.
- **MTCNN + InceptionResNetV1:** Computes 512-d face embeddings and cosine similarity.

---

## Slide 8 — TECH STACK
- **Backend & Gateway:** FastAPI, Python 3.9+, Uvicorn, Pydantic, SQLAlchemy, SQLite
- **AI & ML Frameworks:** PyTorch, Torchvision, Torchaudio, Transformers, scikit-learn, OpenCV
- **Forensics & Signal Processing:** Librosa, SoundFile, SciPy, NumPy, Pillow
- **Report & Web UI:** ReportLab, PyPDF, React, TailwindCSS, Docker, Makefile

---

## Slide 9 — LIMITATIONS & ETHICAL DESIGN
- **Honest Constraints Make Evidence Credible:**
  - Novel, un-encountered generative architectures may yield lower confidence.
  - Face verification requires clear, un-occluded reference media.
  - Audio detection quality depends on compression and sample rate.
  - Designed as an expert screening aid, not automated judicial proof.

---

## Slide 10 — ROADMAP & KEY TAKEAWAY
- **6-Month Roadmap:**
  - Next-gen generator coverage (Flux, Midjourney v6, Sora)
  - Temporal optical flow analysis for video deepfakes
  - C2PA provenance cryptographic verification
- **Key Takeaway:**
  > "Unlike commercial APIs that return only a confidence score, DeepSafe produces a full tamper-evident forensic investigation report — running entirely on-premise so sensitive evidence never leaves the investigator's system."
