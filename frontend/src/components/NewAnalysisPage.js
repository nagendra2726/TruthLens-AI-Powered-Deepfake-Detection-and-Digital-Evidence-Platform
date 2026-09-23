import React, { useState, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { UploadCloud, X, Image, Video, Volume2, ArrowRight, AlertCircle } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { db } from '../config/firebase';
import { doc, setDoc, serverTimestamp } from 'firebase/firestore';

import { API_BASE_URL } from '../config/api';

// ── Scanning Overlay ─────────────────────────────────────
const ScanOverlay = ({ steps, currentStep }) => (
  <div className="scan-overlay">
    <div style={{ maxWidth: 420, width: '100%', padding: '2rem 1.5rem', textAlign: 'center' }}>
      <div style={{
        width: 56, height: 56, borderRadius: '50%',
        background: 'var(--bg-soft-blue)', color: 'var(--blue)',
        display: 'flex', alignItems: 'center', justifyContent: 'center',
        margin: '0 auto 1.5rem',
      }}>
        <div className="spinner" style={{ width: 28, height: 28, borderTopColor: 'var(--blue)' }} />
      </div>
      <h2 style={{ fontSize: '1.25rem', fontWeight: 700, color: 'var(--text)', marginBottom: '0.35rem' }}>
        Analyzing your media
      </h2>
      <p style={{ fontSize: '0.875rem', color: 'var(--text-muted)', marginBottom: '1.75rem' }}>
        This may take a few seconds. Please wait.
      </p>
      <div style={{ textAlign: 'left', background: 'var(--bg-white)', border: '1px solid var(--border)', borderRadius: 'var(--r-lg)', padding: '1.25rem' }}>
        {steps.map((step, idx) => {
          const state = idx < currentStep ? 'done' : idx === currentStep ? 'active' : 'pending';
          return (
            <div key={idx} className={`scan-step ${state}`}>
              {state === 'done' ? (
                <svg width="16" height="16" viewBox="0 0 16 16" fill="none" style={{ flexShrink: 0 }}>
                  <circle cx="8" cy="8" r="8" fill="#16A34A" />
                  <path d="M4.5 8l2.5 2.5 4.5-4.5" stroke="#fff" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
                </svg>
              ) : (
                <span className={`scan-dot ${state}`} />
              )}
              <span>{step}</span>
            </div>
          );
        })}
      </div>
    </div>
  </div>
);

// ── Upload Card ──────────────────────────────────────────
const UploadCard = ({ label, description, file, preview, onChange, onRemove, accept, icon }) => {
  const [drag, setDrag] = useState(false);
  const inputRef = useRef();

  const handleDrop = (e) => {
    e.preventDefault(); setDrag(false);
    const f = e.dataTransfer.files[0];
    if (f) onChange(f);
  };

  const handleChange = (e) => {
    if (e.target.files[0]) onChange(e.target.files[0]);
    e.target.value = '';
  };

  if (file) {
    const isVideo = file.type.startsWith('video/') || /\.(mp4|avi|mov|mkv)$/i.test(file.name);
    const isAudio = file.type.startsWith('audio/') || /\.(wav|mp3|flac|ogg|m4a|aac)$/i.test(file.name);
    const sizeKB = (file.size / 1024).toFixed(0);
    return (
      <div className="upload-zone has-file">
        {preview && (
          <div style={{ marginBottom: '0.875rem', borderRadius: 'var(--r-md)', overflow: 'hidden', minHeight: 100, maxHeight: 140, background: '#f8fafc', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', padding: isAudio ? '1rem' : 0 }}>
            {isAudio ? (
              <div style={{ width: '100%', display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '0.5rem' }}>
                <Volume2 size={28} style={{ color: 'var(--blue)' }} />
                <audio controls src={preview} style={{ width: '100%', maxWidth: 280, height: 36 }} />
              </div>
            ) : isVideo ? (
              <video src={preview} style={{ height: '100%', width: '100%', objectFit: 'contain' }} muted />
            ) : (
              <img src={preview} alt="preview" style={{ height: '100%', width: '100%', objectFit: 'contain' }} />
            )}
          </div>
        )}
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: '0.75rem' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', flex: 1, minWidth: 0 }}>
            {isAudio ? (
              <Volume2 size={16} style={{ color: 'var(--blue)', flexShrink: 0 }} />
            ) : isVideo ? (
              <Video size={16} style={{ color: 'var(--success)', flexShrink: 0 }} />
            ) : (
              <Image size={16} style={{ color: 'var(--success)', flexShrink: 0 }} />
            )}
            <span style={{ fontSize: '0.8125rem', fontWeight: 500, color: 'var(--text)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{file.name}</span>
            <span style={{ fontSize: '0.75rem', color: 'var(--text-faint)', flexShrink: 0 }}>{sizeKB} KB</span>
          </div>
          <button onClick={onRemove} className="btn btn-ghost btn-sm" style={{ padding: '0.25rem', color: 'var(--text-muted)' }} aria-label="Remove file">
            <X size={16} />
          </button>
        </div>
      </div>
    );
  }

  return (
    <div
      className={`upload-zone${drag ? ' drag-over' : ''}`}
      onDragOver={e => { e.preventDefault(); setDrag(true); }}
      onDragLeave={() => setDrag(false)}
      onDrop={handleDrop}
      onClick={() => inputRef.current?.click()}
      role="button" tabIndex={0}
      onKeyDown={e => e.key === 'Enter' && inputRef.current?.click()}
      aria-label={`Upload ${label}`}
    >
      <input ref={inputRef} type="file" accept={accept} onChange={handleChange} style={{ display: 'none' }} />
      <div style={{ color: drag ? 'var(--blue)' : 'var(--text-faint)', marginBottom: '0.75rem' }}>
        {icon || <UploadCloud size={32} />}
      </div>
      <p style={{ fontSize: '0.9375rem', fontWeight: 600, color: 'var(--text-2)', marginBottom: '0.25rem' }}>
        {label}
      </p>
      <p style={{ fontSize: '0.8125rem', color: 'var(--text-muted)', marginBottom: '0.75rem' }}>
        {description}
      </p>
      <span style={{ display: 'inline-block', fontSize: '0.8125rem', fontWeight: 600, color: 'var(--blue)', background: 'var(--bg-soft-blue)', padding: '0.3rem 0.85rem', borderRadius: 'var(--r-full)', cursor: 'pointer' }}>
        Choose file
      </span>
    </div>
  );
};

// ── Main Component ───────────────────────────────────────
const NewAnalysisPage = ({ onAnalysisComplete }) => {
  const { user } = useAuth();
  const [mode, setMode] = useState('single');
  const [singleFile, setSingleFile] = useState(null);
  const [singlePreview, setSinglePreview] = useState(null);
  const [refFile, setRefFile] = useState(null);
  const [refPreview, setRefPreview] = useState(null);
  const [susFile, setSusFile] = useState(null);
  const [susPreview, setSusPreview] = useState(null);
  const [analyzing, setAnalyzing] = useState(false);
  const [scanStep, setScanStep] = useState(0);
  const [error, setError] = useState('');
  const navigate = useNavigate();

  const SINGLE_STEPS = [
    'Preparing image…',
    'Analyzing image…',
    'Calculating supporting characteristics…',
    'Preparing assessment…',
  ];
  const COMPARE_STEPS = [
    'Uploading media…',
    'Analyzing reference media…',
    'Analyzing suspected media…',
    'Comparing faces…',
    'Evaluating evidence…',
    'Preparing your result…',
  ];

  const setFile = (setter, previewSetter) => (f) => {
    setter(f);
    previewSetter(f ? URL.createObjectURL(f) : null);
    setError('');
  };

  const saveToFirestore = async (caseId, payload) => {
    if (!user?.uid) return;
    try {
      await setDoc(doc(db, 'users', user.uid, 'analyses', caseId), { ...payload, userId: user.uid, createdAt: serverTimestamp() });
    } catch (e) { /* non-blocking */ }
  };

  const simulateScan = (steps) => {
    let i = 0;
    setScanStep(0);
    const interval = setInterval(() => {
      i++;
      if (i < steps.length) setScanStep(i);
      else clearInterval(interval);
    }, 800);
    return interval;
  };

  // Single Analysis
  const handleSingle = async () => {
    if (!singleFile || analyzing) return;
    if (singleFile.size === 0) {
      setError('The selected file is empty. Please choose a valid image file.');
      return;
    }
    if (singleFile.size > 50 * 1024 * 1024) {
      setError('File size exceeds the 50MB limit. Please upload a smaller image.');
      return;
    }
    setAnalyzing(true); setError('');
    const timer = simulateScan(SINGLE_STEPS);
    const isAudio = singleFile.type.startsWith('audio/') || /\.(wav|mp3|flac|ogg|m4a|aac)$/i.test(singleFile.name);
    const isVideo = singleFile.type.startsWith('video/') || /\.(mp4|avi|mov|mkv)$/i.test(singleFile.name);
    const mediaType = isAudio ? 'audio' : isVideo ? 'video' : 'image';
    const form = new FormData();
    form.append('image', singleFile);
    form.append('file', singleFile);
    form.append('media_type', mediaType);
    try {
      let res = await fetch(`${API_BASE_URL}/api/analyze`, { method: 'POST', body: form });
      if (!res.ok && res.status === 404) {
        res = await fetch(`${API_BASE_URL}/detect`, { method: 'POST', body: form });
      }
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail?.message || data.detail || 'Analysis failed. Please try again.');
      clearInterval(timer);
      const caseId = data.case_id || `TL-${Date.now()}`;
      const verdict = data.result?.category || data.assessment?.category || (data.is_likely_deepfake ? 'POTENTIAL_DEEPFAKE' : 'LIKELY_AUTHENTIC');
      const risk = data.result?.risk_level || data.assessment?.risk_level || (data.is_likely_deepfake ? 'HIGH' : 'LOW');
      const conf = data.result?.confidence || data.assessment?.confidence || 'HIGH';
      const aiScore = data.result?.ai_probability ?? data.deepfake_probability ?? 0.5;
      const realScore = data.result?.real_probability ?? (1.0 - aiScore);
      const classification = data.result?.classification || (aiScore >= 0.55 ? 'Likely AI-Generated' : aiScore <= 0.45 ? 'Likely Real' : 'Inconclusive');

      const resultData = {
        case_id: caseId,
        timestamp: data.timestamp || new Date().toISOString(),
        mode: 'single',
        filename: singleFile.name,
        classification,
        // 'result' key mirrors what /api/analyze returns directly — ResultPage reads resObj = resultData.result
        result: {
          classification,
          category: verdict,
          risk_level: risk,
          ai_probability: aiScore,
          real_probability: realScore,
          confidence: conf,
          confidence_score: data.result?.confidence_score ?? null,
          model_name: data.result?.model_name || 'dima806/deepfake_vs_real_image_detection',
          architecture: data.result?.architecture || 'Vision Transformer (ViT)',
        },
        assessment: {
          category: verdict,
          risk_level: risk,
          confidence: conf,
          explanation: data.assessment?.explanation || `AI detection signals indicate a ${aiScore >= 0.55 ? 'high' : 'low'} likelihood of AI generation or synthetic modification.`,
          disclaimer: 'AI-assisted screening. Results may contain errors and should not be treated as definitive proof.'
        },
        suspected_analysis: {
          prediction: classification,
          ai_probability: aiScore,
          real_probability: realScore,
          confidence: conf,
          model_name: data.result?.model_name || 'dima806/deepfake_vs_real_image_detection',
          architecture: data.result?.architecture || 'Vision Transformer (ViT)',
        },
        image_analysis: data.image_analysis || null,
        sha256: data.hash?.sha256 || null,
        hash: data.hash || null,
        face_verification: data.face_verification || null,
      };

      await saveToFirestore(caseId, {
        caseId,
        mode: 'single',
        mediaType,
        referenceFileName: singleFile.name,
        suspectedFileName: 'N/A',
        verdict,
        classification,
        riskLevel: risk,
        confidence: conf,
        caseFileGenerated: false,
        suspectedAIScore: aiScore,
        sha256: data.hash?.sha256 || null,
        timestamp: new Date().toISOString(),
        data: resultData
      });
      try {
        const ex = JSON.parse(localStorage.getItem('truthlens_history') || '[]');
        localStorage.setItem('truthlens_history', JSON.stringify([{
          id: caseId,
          caseId,
          timestamp: new Date().toISOString(),
          mode: 'single',
          filenames: [singleFile.name],
          caseFileGenerated: false,
          verdict,
          classification,
          riskLevel: risk,
          confidence: conf,
          data: resultData
        }, ...ex].slice(0, 100)));
      } catch (_) {}
      onAnalysisComplete?.();
      navigate(`/history/${caseId}`, { state: { resultData } });
    } catch (err) {
      clearInterval(timer);
      setError(err.message || 'Analysis could not be completed. Please try again.');
      setAnalyzing(false);
    }
  };

  // Compare Analysis
  const handleCompare = async () => {
    if (!refFile || !susFile) return;
    setAnalyzing(true); setError('');
    const timer = simulateScan(COMPARE_STEPS);
    const form = new FormData();
    form.append('reference_media', refFile);
    form.append('suspected_media', susFile);
    try {
      const res = await fetch(`${API_BASE_URL}/analyze/compare`, { method: 'POST', body: form });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail?.message || data.detail || 'Analysis failed. Please try again.');
      clearInterval(timer);
      const caseId = data.case_id || `TL-${Date.now()}`;
      const verdict = data.assessment?.category || 'POTENTIAL_DEEPFAKE';
      const risk = data.assessment?.risk_level || 'HIGH';
      const conf = data.reference_analysis?.confidence || 'HIGH';
      await saveToFirestore(caseId, { caseId, mode: 'compare', mediaType: 'image_compare', referenceFileName: refFile.name, suspectedFileName: susFile.name, verdict, riskLevel: risk, confidence: conf, referenceAIScore: data.reference_analysis?.ai_probability || 0, suspectedAIScore: data.suspected_analysis?.ai_probability || 0, faceSimilarity: data.face_verification?.similarity_score || 0, caseFileGenerated: false, faceVerificationResult: data.face_verification?.verification_result || 'UNKNOWN', timestamp: new Date().toISOString(), data });
      try { const ex = JSON.parse(localStorage.getItem('truthlens_history') || '[]'); localStorage.setItem('truthlens_history', JSON.stringify([{ id: caseId, caseId, timestamp: new Date().toISOString(), mode: 'compare', filenames: [refFile.name, susFile.name], caseFileGenerated: false, verdict, riskLevel: risk, confidence: conf, data }, ...ex].slice(0, 100))); } catch (_) {}
      onAnalysisComplete?.();
      navigate(`/history/${caseId}`, { state: { resultData: data, referencePreview: refPreview, suspectedPreview: susPreview } });
    } catch (err) {
      clearInterval(timer);
      setError(err.message || 'Analysis could not be completed. Please try again.');
      setAnalyzing(false);
    }
  };

  const canSingle = Boolean(singleFile && !analyzing);
  const canCompare = Boolean(refFile && susFile && !analyzing);

  return (
    <>
      {analyzing && <ScanOverlay steps={mode === 'single' ? SINGLE_STEPS : COMPARE_STEPS} currentStep={scanStep} />}

      <div className="fade-in" style={{ maxWidth: 780, margin: '0 auto' }}>
        {/* Header */}
        <div style={{ marginBottom: '1.75rem' }}>
          <h1 style={{ fontSize: '1.625rem', fontWeight: 800, color: 'var(--text)', marginBottom: '0.35rem', letterSpacing: '-0.02em' }}>
            Analyze Media
          </h1>
          <p style={{ fontSize: '0.9375rem', color: 'var(--text-muted)' }}>
            Upload media to check for signs of AI generation or manipulation.
          </p>
        </div>

        {/* Mode Switcher */}
        <div style={{ display: 'flex', gap: '0.5rem', background: 'var(--bg-muted)', padding: '0.3rem', borderRadius: 'var(--r-md)', marginBottom: '1.75rem', width: 'fit-content' }}>
          {[
            { id: 'single', label: 'Single Analysis' },
            { id: 'compare', label: 'Compare Media' },
          ].map(m => (
            <button key={m.id} onClick={() => { setMode(m.id); setError(''); }}
              style={{
                padding: '0.5rem 1.1rem', borderRadius: 'var(--r-sm)',
                fontSize: '0.875rem', fontWeight: 600, border: 'none', cursor: 'pointer',
                background: mode === m.id ? 'var(--bg-white)' : 'transparent',
                color: mode === m.id ? 'var(--text)' : 'var(--text-muted)',
                boxShadow: mode === m.id ? 'var(--shadow-sm)' : 'none',
                transition: 'all var(--t-fast)',
              }}
            >
              {m.label}
            </button>
          ))}
        </div>

        {error && (
          <div className="alert alert-error mb-4" role="alert">
            <AlertCircle size={16} style={{ flexShrink: 0, marginTop: 1 }} />
            <span>{error}</span>
          </div>
        )}

        {/* Single Mode */}
        {mode === 'single' && (
          <div className="card card-lg">
            <p style={{ fontSize: '0.875rem', color: 'var(--text-muted)', marginBottom: '1.25rem' }}>
              Upload an image, video, or audio file to analyze for AI-generated or manipulated content.
            </p>
            <UploadCard
              label="Upload media file"
              description="Drag & drop or choose a file — JPG, PNG, WEBP, MP4, WAV, MP3"
              file={singleFile}
              preview={singlePreview}
              onChange={setFile(setSingleFile, setSinglePreview)}
              onRemove={() => { setSingleFile(null); setSinglePreview(null); }}
              accept="image/*,video/*,audio/*"
            />
            <div style={{ marginTop: '1.5rem' }}>
              <button onClick={handleSingle} disabled={!canSingle} className="btn btn-primary btn-lg" id="analyze-single-btn">
                <ArrowRight size={17} /> Analyze Media
              </button>
            </div>
          </div>
        )}

        {/* Compare Mode */}
        {mode === 'compare' && (
          <div className="card card-lg">
            <p style={{ fontSize: '0.875rem', color: 'var(--text-muted)', marginBottom: '1.25rem' }}>
              Upload two images to independently analyze and compare. Both images are examined separately — no assumptions are made about either.
            </p>
            <div className="grid-2">
              <div>
                <p style={{ fontSize: '0.8125rem', fontWeight: 700, color: 'var(--text-2)', marginBottom: '0.65rem' }}>Reference Media</p>
                <UploadCard
                  label="Upload reference image"
                  description="Drag & drop or choose a file"
                  file={refFile}
                  preview={refPreview}
                  onChange={setFile(setRefFile, setRefPreview)}
                  onRemove={() => { setRefFile(null); setRefPreview(null); }}
                  accept="image/*,video/*"
                />
              </div>
              <div>
                <p style={{ fontSize: '0.8125rem', fontWeight: 700, color: 'var(--text-2)', marginBottom: '0.65rem' }}>Suspected Media</p>
                <UploadCard
                  label="Upload suspected image"
                  description="Drag & drop or choose a file"
                  file={susFile}
                  preview={susPreview}
                  onChange={setFile(setSusFile, setSusPreview)}
                  onRemove={() => { setSusFile(null); setSusPreview(null); }}
                  accept="image/*,video/*"
                />
              </div>
            </div>
            <div style={{ marginTop: '1.5rem' }}>
              <button onClick={handleCompare} disabled={!canCompare} className="btn btn-primary btn-lg" id="analyze-compare-btn">
                <ArrowRight size={17} /> Analyze Both
              </button>
            </div>
          </div>
        )}

        {/* Disclaimer */}
        <div className="disclaimer mt-auto" style={{ marginTop: '1.5rem' }}>
          TruthLens provides AI-assisted authenticity analysis. Results may contain errors and should not be considered definitive proof of authenticity or manipulation.
        </div>
      </div>
    </>
  );
};

export default NewAnalysisPage;
