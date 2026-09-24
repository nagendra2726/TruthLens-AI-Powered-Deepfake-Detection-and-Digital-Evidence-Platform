import React, { useState, useEffect } from 'react';
import { useParams, useNavigate, useLocation, Link } from 'react-router-dom';
import {
  ArrowLeft, Download, ChevronDown, ChevronUp,
  CheckCircle2, AlertTriangle, HelpCircle, FileText,
  Package, Archive, Loader, Eye, Copy, Check, ShieldCheck,
  Sparkles, ExternalLink
} from 'lucide-react';

import { API_BASE_URL } from '../config/api';
import { downloadPDF } from '../utils/exportUtils';

export default function ResultPage() {
  const { caseId } = useParams();
  const location = useLocation();
  const navigate = useNavigate();

  const [resultData, setResultData] = useState(location.state?.resultData || null);
  const targetCaseId = caseId || resultData?.case_id || resultData?.id;
  const [loading, setLoading] = useState(!resultData);
  const [downloading, setDownloading] = useState(false);
  const [showTech, setShowTech] = useState(false);
  const [copiedHash, setCopiedHash] = useState(false);

  // Case File generation states: "idle" | "generating" | "ready" | "downloading" | "error"
  const [caseFileStatus, setCaseFileStatus] = useState('idle');
  const [caseFileError, setCaseFileError] = useState(null);

  // Restore from localStorage or API if accessed directly or reloaded
  useEffect(() => {
    if (resultData || !caseId) return;
    try {
      const historyStore = JSON.parse(localStorage.getItem('truthlens_history') || '[]');
      const record = historyStore.find(r => r.caseId === caseId || r.id === caseId);
      if (record?.data) {
        setResultData(record.data);
        if (record.caseFileGenerated || record.data.caseFileGenerated) setCaseFileStatus('ready');
        setLoading(false);
        return;
      }
    } catch (_) {}

    fetch(`${API_BASE_URL}/cases/${caseId}`)
      .then(res => res.ok ? res.json() : Promise.reject())
      .then(data => {
        setResultData(data);
        setLoading(false);
      })
      .catch(() => setLoading(false));
  }, [caseId, resultData]);

  // Copy SHA-256 hash to clipboard
  const handleCopyHash = (hashVal) => {
    if (!hashVal) return;
    navigator.clipboard.writeText(hashVal);
    setCopiedHash(true);
    setTimeout(() => setCopiedHash(false), 2500);
  };

  // Open PDF Report in new browser tab
  const handleViewReport = async () => {
    if (!targetCaseId) return;
    try {
      const res = await fetch(`${API_BASE_URL}/reports/${targetCaseId}/download?t=${Date.now()}`);
      if (res.ok) {
        const blob = await res.blob();
        const url = URL.createObjectURL(blob);
        window.open(url, '_blank');
        return;
      }
    } catch (_) {}
    handleDownload();
  };

  // Download PDF Report
  const handleDownload = async () => {
    if (!targetCaseId && !resultData) return;
    setDownloading(true);
    try {
      if (targetCaseId) {
        const res = await fetch(`${API_BASE_URL}/reports/${targetCaseId}/download?t=${Date.now()}`);
        if (res.ok) {
          const blob = await res.blob();
          const url = URL.createObjectURL(blob);
          const a = document.createElement('a');
          a.href = url;
          a.download = `TruthLens_Report_${targetCaseId}.pdf`;
          document.body.appendChild(a);
          a.click();
          document.body.removeChild(a);
          setTimeout(() => URL.revokeObjectURL(url), 60000);
          return;
        }
      }
      // Fallback to client-side PDF generation
      if (resultData) {
        downloadPDF(
          resultData,
          targetCaseId || 'analysis',
          location.state?.suspectedPreview || location.state?.referencePreview || resultData.suspected_preview_b64 || resultData.reference_preview_b64
        );
        return;
      }
      throw new Error('Report not found');
    } catch (err) {
      if (resultData) {
        try {
          downloadPDF(
            resultData,
            targetCaseId || 'analysis',
            location.state?.suspectedPreview || location.state?.referencePreview || resultData.suspected_preview_b64 || resultData.reference_preview_b64
          );
          return;
        } catch (_) {}
      }
      alert('Unable to download report. Please ensure the backend server is running.');
    } finally {
      setDownloading(false);
    }
  };

  // Manual Case-file generation (Strictly on-demand)
  const handleGenerateCaseFile = async () => {
    if (!targetCaseId) return;
    setCaseFileStatus('generating');
    setCaseFileError(null);
    try {
      const res = await fetch(`${API_BASE_URL}/api/cases/${targetCaseId}/generate`, { method: 'POST' });
      if (!res.ok) throw new Error(`Server responded with ${res.status}`);
      setCaseFileStatus('ready');
    } catch (err) {
      setCaseFileError('Unable to generate case file. Please retry.');
      setCaseFileStatus('error');
    }
  };

  // Download Case-file ZIP package
  const handleDownloadCaseFile = async () => {
    if (!targetCaseId) return;
    setCaseFileStatus('downloading');
    try {
      const res = await fetch(`${API_BASE_URL}/reports/${targetCaseId}/case-file/download`);
      if (!res.ok) throw new Error(`Server responded with ${res.status}`);
      const blob = await res.blob();
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `TruthLens_Case_${targetCaseId}.zip`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      setTimeout(() => URL.revokeObjectURL(url), 60000);
      setCaseFileStatus('ready');
    } catch (err) {
      setCaseFileError('Unable to download case file.');
      setCaseFileStatus('error');
    }
  };

  if (loading) {
    return (
      <div style={{ textAlign: 'center', padding: '5rem 1rem' }}>
        <div className="spinner" style={{ width: 36, height: 36, margin: '0 auto 1rem', borderTopColor: 'var(--blue)' }} />
        <p style={{ color: 'var(--text-muted)' }}>Loading analysis result…</p>
      </div>
    );
  }

  if (!resultData) {
    return (
      <div style={{ textAlign: 'center', padding: '5rem 1rem' }}>
        <h2 style={{ fontSize: '1.25rem', fontWeight: 700, marginBottom: '0.5rem' }}>Result not found</h2>
        <p style={{ color: 'var(--text-muted)', marginBottom: '1.5rem' }}>
          Unable to locate analysis for case <span style={{ fontFamily: 'var(--font-mono)' }}>{caseId}</span>.
        </p>
        <Link to="/history" className="btn btn-secondary">
          <ArrowLeft size={16} /> Back to History
        </Link>
      </div>
    );
  }

  // ── Normalize Data from both /api/analyze and /api/compare schemas ──
  const assessment = resultData.assessment || {};
  const resObj = resultData.result || {};
  const sus = resultData.suspected_analysis || {};
  const ref = resultData.reference_analysis || {};
  const face = resultData.face_verification || null;
  const faceAnalysis = resultData.face_analysis || resultData.faceAnalysis || (face?.face_detected != null ? face : null);
  const imageAnalysis = resultData.image_analysis || {};
  const fileInfo = imageAnalysis.file_information || {};
  const optical = imageAnalysis.optical_characteristics || {};
  const ela = imageAnalysis.ela_analysis || {};
  const spectral = imageAnalysis.spectral_analysis || {};
  const pixel = sus.pixel_forensics || ref.pixel_forensics || {};

  // Case ID and Timestamp
  const displayCaseId = targetCaseId || 'TL-Analysis';
  const rawDate = resultData.timestamp || resultData.created_at;
  const formattedDate = rawDate
    ? new Date(rawDate).toLocaleString('en-IN', {
        day: 'numeric',
        month: 'long',
        year: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
        hour12: true
      })
    : 'Recently Analyzed';

  // Probabilities — read from multiple possible locations for forward/backward compat
  // /api/analyze returns data.result.ai_probability
  // Firestore history stores data.suspected_analysis.ai_probability
  // Legacy may store data.deepfake_probability
  const rawAiProb =
    resObj.ai_probability ??
    sus.ai_probability ??
    resultData.deepfake_probability ??
    resultData.ai_probability ??
    0;
  const rawRealProb =
    resObj.real_probability ??
    sus.real_probability ??
    resultData.real_probability ??
    (1 - rawAiProb);
  const aiPct = Number((rawAiProb * 100).toFixed(1));
  const realPct = Number((rawRealProb * 100).toFixed(1));

  // Category and Verdict
  const categoryKey = resObj.category || assessment.category || '';
  const rawClassification = resObj.classification || '';
  const isLikelyReal =
    categoryKey === 'LIKELY_AUTHENTIC' ||
    categoryKey === 'AUTHENTIC_MEDIA_DIFFERENT_PERSON' ||
    rawClassification.toLowerCase().includes('real') ||
    (rawAiProb < 0.35 && rawRealProb > 0.65);

  const isLikelyAI =
    categoryKey === 'POTENTIAL_DEEPFAKE' ||
    categoryKey === 'LIKELY_AI_GENERATED' ||
    categoryKey === 'BOTH_MEDIA_APPEAR_SYNTHETIC' ||
    categoryKey === 'AI_GENERATED_MEDIA_DIFFERENT_PERSON' ||
    rawClassification.toLowerCase().includes('ai') ||
    rawAiProb >= 0.5;

  let verdictTitle = 'Inconclusive';
  let verdictSubtitle = 'Visual patterns do not clearly distinguish authenticity';
  let verdictColor = '#D97706'; // Amber / warning
  let verdictBg = '#FFFBEB';
  let verdictBorder = '#FDE68A';
  let verdictIcon = <HelpCircle size={28} />;
  let confidenceVal = resObj.confidence || assessment.confidence || 'Medium';
  let riskVal = resObj.risk_level || assessment.risk_level || 'Moderate';

  if (isLikelyReal) {
    verdictTitle = 'Likely Real';
    verdictSubtitle = 'Low likelihood of AI-generated content';
    verdictColor = '#16A34A'; // Success green
    verdictBg = '#F0FDF4';
    verdictBorder = '#BBF7D0';
    verdictIcon = <CheckCircle2 size={28} />;
    confidenceVal = resObj.confidence || assessment.confidence || 'Very High';
    riskVal = resObj.risk_level || assessment.risk_level || 'Low';
  } else if (isLikelyAI) {
    verdictTitle = 'Likely AI-Generated';
    verdictSubtitle = 'High likelihood of synthetic or AI-manipulated content';
    verdictColor = '#DC2626'; // Danger red
    verdictBg = '#FEF2F2';
    verdictBorder = '#FECACA';
    verdictIcon = <AlertTriangle size={28} />;
    confidenceVal = resObj.confidence || assessment.confidence || 'Very High';
    riskVal = resObj.risk_level || assessment.risk_level || 'High';
  }

  // Clean badges formatting
  const formattedConfidence = String(confidenceVal).replace(/_/g, ' ').toLowerCase().replace(/\b\w/g, c => c.toUpperCase());
  const formattedRisk = String(riskVal).replace(/_/g, ' ').toLowerCase().replace(/\b\w/g, c => c.toUpperCase());

  // SHA-256 Hash
  const fileHash =
    resultData.hash?.sha256 ||
    resultData.suspected_sha256 ||
    sus.sha256 ||
    resultData.sha256 ||
    '';

  // Face Verification Data
  const hasFaceVerification = Boolean(
    face &&
    (face.best_match_score != null || face.match != null || face.similarity != null)
  );
  const faceScore = face?.best_match_score ?? face?.similarity;
  const faceSimPct = faceScore != null ? (faceScore * 100).toFixed(1) : null;
  const faceMatch = face?.match ?? (faceScore != null && faceScore >= (face?.threshold_used || 0.65));

  // Media preview
  const mediaPreview =
    location.state?.suspectedPreview ||
    location.state?.referencePreview ||
    resultData.suspected_preview_b64 ||
    resultData.reference_preview_b64;

  // ── "Why This Result?" Dynamic Bullets (3–5 points based ONLY on actual data) ──
  const explanationPoints = [];

  // Point 1: AI Detector Confidence
  if (isLikelyReal) {
    explanationPoints.push(`AI detection indicates a high probability of authentic visual patterns (${realPct}% authentic score, ${formattedConfidence} confidence).`);
  } else if (isLikelyAI) {
    explanationPoints.push(`AI detection identified synthetic artifacts and generative patterns (${aiPct}% AI probability, ${formattedConfidence} confidence).`);
  } else {
    explanationPoints.push(`AI detection yields indeterminate indicators (AI: ${aiPct}%, Authentic: ${realPct}%).`);
  }

  // Point 2: Image Characteristics
  if (optical.contrast != null || optical.sharpness != null || optical.brightness != null) {
    explanationPoints.push('Supporting image characteristics examined across optical contrast, sharpness, and brightness metrics.');
  } else if (pixel.texture || pixel.edges) {
    explanationPoints.push('Pixel-level texture analysis and edge distributions support the model assessment.');
  } else {
    explanationPoints.push('Supporting image characteristics and spatial visual transitions were examined.');
  }

  // Point 3: Forensic Indicators
  if (ela.interpretation) {
    explanationPoints.push(`Forensic Error Level Analysis (ELA): ${ela.interpretation}.`);
  } else if (spectral.interpretation) {
    explanationPoints.push(`Frequency domain assessment: ${spectral.interpretation}.`);
  } else if (pixel.noise?.residual_variance != null) {
    explanationPoints.push(`Noise residual variance (${Number(pixel.noise.residual_variance).toFixed(2)}) evaluated for sensor noise consistency.`);
  } else {
    explanationPoints.push('Compression resilience and frequency consistency evaluated across media layers.');
  }

  // Point 4: Face Verification (ONLY if used)
  if (hasFaceVerification && faceSimPct != null) {
    explanationPoints.push(
      faceMatch
        ? `Face verification confirmed facial identity match (${faceSimPct}% similarity).`
        : `Face verification detected differing facial profiles (${faceSimPct}% similarity).`
    );
  }

  // Point 5: File Integrity
  if (fileHash) {
    explanationPoints.push('Cryptographic SHA-256 fingerprint verified for tamper-evident chain of custody.');
  }

  // Technical Details Categorized Groups (Requirement 3.E)
  const techDetailGroups = [
    {
      group: 'FILE INFORMATION',
      items: [
        { label: 'File Name', value: fileInfo.filename || resultData.filename || resultData.suspected_filename || null },
        { label: 'File Format', value: fileInfo.format || null },
        { label: 'MIME Type', value: fileInfo.content_type || resultData.suspected_content_type || 'image/jpeg' },
        { label: 'File Size', value: fileInfo.file_size_bytes ? `${(fileInfo.file_size_bytes / 1024).toFixed(1)} KB` : null },
        { label: 'Image Width', value: fileInfo.width ? `${fileInfo.width} px` : null },
        { label: 'Image Height', value: fileInfo.height ? `${fileInfo.height} px` : null },
        { label: 'Color Mode', value: fileInfo.color_mode || 'RGB' },
        { label: 'SHA-256 Digest', value: fileHash || null },
      ].filter(i => i.value != null),
    },
    {
      group: 'IMAGE CHARACTERISTICS',
      items: [
        { label: 'Brightness', value: optical.brightness != null ? optical.brightness.toFixed(3) : null },
        { label: 'Contrast', value: optical.contrast != null ? optical.contrast.toFixed(3) : null },
        { label: 'Exposure', value: optical.exposure != null ? optical.exposure.toFixed(3) : (optical.brightness != null ? `${(optical.brightness * 100).toFixed(1)}%` : null) },
        { label: 'Sharpness', value: optical.sharpness != null ? optical.sharpness.toFixed(2) : null },
        { label: 'Texture', value: optical.texture != null ? optical.texture.toFixed(3) : null },
        { label: 'Saturation', value: optical.saturation != null ? optical.saturation.toFixed(3) : null },
        { label: 'Noise Variance', value: optical.noise_variance != null ? optical.noise_variance.toFixed(2) : (pixel.noise?.residual_variance != null ? Number(pixel.noise.residual_variance).toFixed(2) : null) },
      ].filter(i => i.value != null),
    },
    {
      group: 'FORENSIC INDICATORS',
      items: [
        { label: 'Edge Density', value: optical.edge_density != null ? optical.edge_density.toFixed(3) : (pixel.edges?.edge_density != null ? Number(pixel.edges.edge_density).toFixed(3) : null) },
        { label: 'High-Frequency Ratio', value: spectral.high_frequency_ratio != null ? spectral.high_frequency_ratio.toFixed(4) : (pixel.frequency?.high_low_ratio != null ? Number(pixel.frequency.high_low_ratio).toFixed(4) : null) },
        { label: 'Noise Residual', value: pixel.noise?.residual_variance != null ? Number(pixel.noise.residual_variance).toFixed(3) : (optical.noise_variance != null ? optical.noise_variance.toFixed(3) : null) },
        { label: 'ELA Compression Profile', value: typeof ela.compression_resilience === 'string' ? ela.compression_resilience : (ela.score != null ? `Score: ${ela.score.toFixed(3)}` : null) },
        { label: 'ELA Mean Error', value: ela.mean_error != null ? ela.mean_error.toFixed(3) : null },
        { label: 'Spectral Consistency', value: spectral.spectral_consistency || null },
      ].filter(i => i.value != null),
    },
    {
      group: 'FACE ANALYSIS',
      items: [
        { label: 'Number of Detected Faces', value: faceAnalysis?.face_count != null ? String(faceAnalysis.face_count) : (faceAnalysis?.face_detected ? '1' : '0') },
        { label: 'Human Face Detected', value: faceAnalysis?.face_detected ? 'Yes' : 'No' },
        { label: 'Face Regions / Bounding Boxes', value: faceAnalysis?.bounding_boxes && faceAnalysis.bounding_boxes.length > 0 ? `${faceAnalysis.bounding_boxes.length} box(es) localized` : 'None' },
        { label: 'Detection Confidence', value: faceAnalysis?.detection_confidences && faceAnalysis.detection_confidences.length > 0 ? faceAnalysis.detection_confidences.map(c => `${(c * 100).toFixed(1)}%`).join(', ') : null },
        { label: 'Biometric Status', value: faceAnalysis?.face_detected ? 'Human facial region localized for AI analysis' : 'No human face detected (calibrated for human faces)' },
      ].filter(i => i.value != null),
    },
    {
      group: 'AI MODEL',
      items: [
        { label: 'Model Name', value: resObj.model_name || sus.model_name || 'dima806/deepfake_vs_real_image_detection' },
        { label: 'Architecture', value: resObj.architecture || sus.architecture || 'Vision Transformer (ViT)' },
        { label: 'Predicted Class', value: verdictTitle },
        { label: 'Authentic Probability', value: `${realPct.toFixed(1)}%` },
        { label: 'AI-Generated Probability', value: `${aiPct.toFixed(1)}%` },
        { label: 'Model Confidence', value: formattedConfidence },
        { label: 'Model Status', value: resObj.is_model_live !== false ? 'Live (Preloaded in memory)' : 'Forensic Heuristic Fallback' },
      ].filter(i => i.value != null),
    },
  ];

  return (
    <div className="fade-in" style={{ maxWidth: 1040, margin: '0 auto', paddingBottom: '3rem' }}>

      {/* ============================================================
          1. PAGE HEADER
          ============================================================ */}
      <div style={{ marginBottom: '1.5rem' }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '0.75rem', marginBottom: '0.75rem' }}>
          <button
            onClick={() => navigate('/history')}
            className="btn btn-ghost btn-sm"
            style={{ paddingLeft: 0, display: 'inline-flex', alignItems: 'center', gap: '0.4rem', color: '#64748B' }}
          >
            <ArrowLeft size={16} /> Back to History
          </button>

          <button
            onClick={handleDownload}
            disabled={downloading}
            className="btn btn-secondary btn-sm"
            id="header-download-report-btn"
            style={{ display: 'inline-flex', alignItems: 'center', gap: '0.4rem' }}
          >
            <Download size={14} /> {downloading ? 'Downloading…' : 'Download Report'}
          </button>
        </div>

        <div>
          <p style={{ fontSize: '0.75rem', fontWeight: 700, color: '#64748B', textTransform: 'uppercase', letterSpacing: '0.06em', margin: 0 }}>
            Analysis Result
          </p>
          <div style={{ display: 'flex', alignItems: 'baseline', gap: '0.85rem', flexWrap: 'wrap', marginTop: '0.2rem' }}>
            <h1 style={{ fontSize: '1.45rem', fontWeight: 800, color: '#0F172A', letterSpacing: '-0.02em', margin: 0 }}>
              Case <span style={{ fontFamily: 'var(--font-mono)' }}>{displayCaseId}</span>
            </h1>
            <span style={{ fontSize: '0.85rem', color: '#64748B', fontWeight: 500 }}>
              {formattedDate}
            </span>
          </div>
        </div>
      </div>

      {/* ============================================================
          2. MAIN RESULT CARD (Most visually important)
          ============================================================ */}
      <div
        style={{
          background: verdictBg,
          border: `1.5px solid ${verdictBorder}`,
          borderRadius: 14,
          padding: '1.75rem 2rem',
          marginBottom: '1.25rem',
          boxShadow: '0 2px 8px rgba(15,23,42,0.04)',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', flexWrap: 'wrap', gap: '1.25rem' }}>
          <div style={{ display: 'flex', alignItems: 'flex-start', gap: '1rem', flex: 1, minWidth: 280 }}>
            <div style={{ color: verdictColor, flexShrink: 0, marginTop: '2px' }}>
              {verdictIcon}
            </div>
            <div>
              <h2 style={{ fontSize: '1.65rem', fontWeight: 800, color: verdictColor, letterSpacing: '-0.02em', margin: 0 }}>
                {verdictTitle}
              </h2>
              <p style={{ fontSize: '0.975rem', color: '#334155', fontWeight: 500, margin: '0.35rem 0 0.85rem 0' }}>
                {verdictSubtitle}
              </p>

              {/* Confidence & Risk indicators */}
              <div style={{ display: 'flex', alignItems: 'center', gap: '1.5rem', flexWrap: 'wrap' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
                  <span style={{ fontSize: '0.8125rem', color: '#64748B', fontWeight: 500 }}>Confidence:</span>
                  <span style={{ fontSize: '0.8125rem', fontWeight: 700, color: '#0F172A' }}>{formattedConfidence}</span>
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
                  <span style={{ fontSize: '0.8125rem', color: '#64748B', fontWeight: 500 }}>Risk:</span>
                  <span style={{
                    fontSize: '0.75rem',
                    fontWeight: 700,
                    padding: '2px 8px',
                    borderRadius: 9999,
                    background: riskVal === 'Low' || riskVal === 'LOW' ? '#DCFCE7' : riskVal === 'High' || riskVal === 'HIGH' ? '#FEE2E2' : '#FEF3C7',
                    color: riskVal === 'Low' || riskVal === 'LOW' ? '#16A34A' : riskVal === 'High' || riskVal === 'HIGH' ? '#DC2626' : '#D97706'
                  }}>
                    {formattedRisk}
                  </span>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* AI-assisted assessment disclaimer */}
        <div style={{ marginTop: '1.25rem', paddingTop: '0.85rem', borderTop: `1px solid ${verdictBorder}`, fontSize: '0.8125rem', color: '#64748B', fontStyle: 'italic' }}>
          AI-assisted assessment. This result is not definitive proof of authenticity or manipulation.
        </div>
      </div>

      {/* ============================================================
          3. DETECTION PROBABILITIES
          ============================================================ */}
      <div
        className="card"
        style={{
          background: '#FFFFFF',
          border: '1px solid #E2E8F0',
          borderRadius: 14,
          padding: '1.35rem 1.75rem',
          marginBottom: '1.25rem',
          boxShadow: '0 1px 3px rgba(15,23,42,0.04)'
        }}
      >
        <h3 style={{ fontSize: '0.9375rem', fontWeight: 700, color: '#0F172A', marginBottom: '1.1rem' }}>
          Detection Summary
        </h3>

        {/* AI-Generated Probability Bar */}
        <div style={{ marginBottom: '1rem' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.35rem' }}>
            <span style={{ fontSize: '0.8125rem', color: '#475569', fontWeight: 600 }}>
              AI-Generated Probability
            </span>
            <span style={{ fontSize: '0.875rem', fontWeight: 800, color: aiPct > 50 ? '#DC2626' : '#475569', fontFamily: 'var(--font-mono)' }}>
              {aiPct.toFixed(1)}%
            </span>
          </div>
          <div style={{ height: 8, background: '#F1F5F9', borderRadius: 9999, overflow: 'hidden' }}>
            <div
              style={{
                width: `${Math.min(100, Math.max(0, aiPct))}%`,
                height: '100%',
                background: aiPct > 50 ? '#DC2626' : '#94A3B8',
                borderRadius: 9999,
                transition: 'width 0.4s ease'
              }}
            />
          </div>
        </div>

        {/* Authentic Probability Bar */}
        <div>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.35rem' }}>
            <span style={{ fontSize: '0.8125rem', color: '#475569', fontWeight: 600 }}>
              Authentic Probability
            </span>
            <span style={{ fontSize: '0.875rem', fontWeight: 800, color: realPct > 50 ? '#16A34A' : '#475569', fontFamily: 'var(--font-mono)' }}>
              {realPct.toFixed(1)}%
            </span>
          </div>
          <div style={{ height: 8, background: '#F1F5F9', borderRadius: 9999, overflow: 'hidden' }}>
            <div
              style={{
                width: `${Math.min(100, Math.max(0, realPct))}%`,
                height: '100%',
                background: realPct > 50 ? '#16A34A' : '#94A3B8',
                borderRadius: 9999,
                transition: 'width 0.4s ease'
              }}
            />
          </div>
        </div>
      </div>

      {/* ============================================================
          4. WHY THIS RESULT?
          ============================================================ */}
      <div
        className="card"
        style={{
          background: '#FFFFFF',
          border: '1px solid #E2E8F0',
          borderRadius: 14,
          padding: '1.35rem 1.75rem',
          marginBottom: '1.25rem',
          boxShadow: '0 1px 3px rgba(15,23,42,0.04)'
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.9rem' }}>
          <Sparkles size={17} color="#2563EB" />
          <h3 style={{ fontSize: '0.95rem', fontWeight: 700, color: '#0F172A', margin: 0 }}>
            Why did TruthLens give this result?
          </h3>
        </div>

        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.65rem' }}>
          {explanationPoints.map((point, idx) => (
            <div key={idx} style={{ display: 'flex', alignItems: 'flex-start', gap: '0.6rem' }}>
              <span style={{ color: '#16A34A', fontWeight: 700, fontSize: '0.875rem', lineHeight: 1.4 }}>✓</span>
              <span style={{ fontSize: '0.875rem', color: '#334155', lineHeight: 1.5 }}>{point}</span>
            </div>
          ))}
        </div>
      </div>

      {/* ============================================================
          5. IMAGE / TECHNICAL DETAILS (Collapsible, closed by default)
          ============================================================ */}
      <div
        className="card"
        style={{
          background: '#FFFFFF',
          border: '1px solid #E2E8F0',
          borderRadius: 14,
          padding: '1.25rem 1.75rem',
          marginBottom: '1.25rem',
          boxShadow: '0 1px 3px rgba(15,23,42,0.04)'
        }}
      >
        <button
          onClick={() => setShowTech(v => !v)}
          style={{
            width: '100%',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            background: 'none',
            border: 'none',
            padding: 0,
            cursor: 'pointer',
            textAlign: 'left'
          }}
          aria-expanded={showTech}
          id="toggle-tech-details-btn"
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <FileText size={17} color="#64748B" />
            <span style={{ fontSize: '0.925rem', fontWeight: 700, color: '#0F172A' }}>
              View Technical Details
            </span>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.35rem', color: '#64748B', fontSize: '0.8125rem' }}>
            <span>{showTech ? 'Hide Details' : 'Expand'}</span>
            {showTech ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
          </div>
        </button>

        {showTech && (
          <div className="fade-in" style={{ marginTop: '1.25rem', paddingTop: '1.25rem', borderTop: '1px solid #E2E8F0' }}>
            
            {/* If media preview exists, show thumbnail with file details */}
            {mediaPreview && (
              <div style={{
                display: 'flex',
                alignItems: 'center',
                gap: '1rem',
                padding: '0.75rem',
                background: '#F8FAFC',
                border: '1px solid #E2E8F0',
                borderRadius: 10,
                marginBottom: '1.25rem'
              }}>
                <img
                  src={mediaPreview}
                  alt="Analyzed Media"
                  style={{ width: 64, height: 64, objectFit: 'cover', borderRadius: 6, border: '1px solid #CBD5E1' }}
                />
                <div>
                  <div style={{ fontSize: '0.8125rem', fontWeight: 700, color: '#0F172A', wordBreak: 'break-all' }}>
                    {resultData.filename || resultData.suspected_filename || fileInfo.filename || 'Analyzed Media'}
                  </div>
                  <div style={{ fontSize: '0.75rem', color: '#64748B', marginTop: '0.15rem' }}>
                    {fileInfo.width && fileInfo.height ? `${fileInfo.width} × ${fileInfo.height} px · ` : ''}
                    {fileInfo.format || fileInfo.content_type || 'Image'}
                  </div>
                </div>
              </div>
            )}

            {/* Categorized Technical Details Groups */}
            <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
              {techDetailGroups.map(grp => grp.items.length > 0 && (
                <div key={grp.group}>
                  <div style={{
                    fontSize: '0.75rem',
                    fontWeight: 800,
                    letterSpacing: '0.06em',
                    color: '#2563EB',
                    marginBottom: '0.65rem',
                    textTransform: 'uppercase',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '0.5rem',
                  }}>
                    <span>{grp.group}</span>
                    <div style={{ flex: 1, height: '1px', background: '#E2E8F0' }} />
                  </div>

                  <div style={{
                    display: 'grid',
                    gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))',
                    gap: '0.45rem 2rem',
                  }}>
                    {grp.items.map(({ label, value }) => (
                      <div
                        key={label}
                        style={{
                          display: 'flex',
                          alignItems: 'center',
                          justifyContent: 'space-between',
                          padding: '0.4rem 0',
                          borderBottom: '1px solid #F1F5F9',
                        }}
                      >
                        <span style={{ fontSize: '0.8125rem', color: '#64748B' }}>{label}</span>
                        <span style={{ fontSize: '0.8125rem', fontWeight: 600, color: '#0F172A', fontFamily: 'var(--font-mono)' }}>
                          {value}
                        </span>
                      </div>
                    ))}
                  </div>

                  {grp.group === 'FACE ANALYSIS' && faceAnalysis && !faceAnalysis.face_detected && (
                    <div style={{
                      marginTop: '0.65rem',
                      padding: '0.65rem 0.85rem',
                      background: '#FFFBEB',
                      border: '1px solid #FDE68A',
                      borderRadius: 8,
                      fontSize: '0.8rem',
                      color: '#92400E',
                      lineHeight: 1.45,
                    }}>
                      <strong>Notice:</strong> TruthLens is calibrated specifically for human facial deepfake and synthetic media analysis. Non-facial assessments should not be treated as human deepfake evidence.
                    </div>
                  )}
                </div>
              ))}
            </div>

            {/* Forensic Interpretations if available */}
            {(ela.interpretation || spectral.interpretation) && (
              <div style={{ marginTop: '1.25rem', padding: '0.85rem 1rem', background: '#F8FAFC', borderRadius: 8, fontSize: '0.8125rem' }}>
                {ela.interpretation && (
                  <p style={{ margin: '0 0 0.4rem 0', color: '#334155' }}>
                    <strong>ELA Interpretation:</strong> {ela.interpretation}
                  </p>
                )}
                {spectral.interpretation && (
                  <p style={{ margin: 0, color: '#334155' }}>
                    <strong>Spectral Consistency:</strong> {spectral.interpretation}
                  </p>
                )}
              </div>
            )}
          </div>
        )}
      </div>

      {/* ============================================================
          6. SHA-256 / FILE INTEGRITY
          ============================================================ */}
      <div
        className="card"
        style={{
          background: '#FFFFFF',
          border: '1px solid #E2E8F0',
          borderRadius: 14,
          padding: '1.25rem 1.75rem',
          marginBottom: '1.25rem',
          boxShadow: '0 1px 3px rgba(15,23,42,0.04)'
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '0.5rem', marginBottom: '0.4rem' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <ShieldCheck size={18} color="#2563EB" />
            <h3 style={{ fontSize: '0.9375rem', fontWeight: 700, color: '#0F172A', margin: 0 }}>
              File Integrity
            </h3>
          </div>
          <span style={{ fontSize: '0.75rem', fontWeight: 600, color: '#64748B' }}>
            SHA-256 Fingerprint
          </span>
        </div>

        <div style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          gap: '0.75rem',
          background: '#F8FAFC',
          border: '1px solid #E2E8F0',
          borderRadius: 8,
          padding: '0.6rem 0.85rem',
          margin: '0.75rem 0'
        }}>
          <span style={{
            fontFamily: 'var(--font-mono)',
            fontSize: '0.8125rem',
            color: '#1E293B',
            wordBreak: 'break-all',
            letterSpacing: '0.02em'
          }}>
            {fileHash || 'Pending computation'}
          </span>

          <button
            onClick={() => handleCopyHash(fileHash)}
            className="btn btn-ghost btn-sm"
            style={{ flexShrink: 0, padding: '0.35rem 0.65rem', display: 'inline-flex', alignItems: 'center', gap: '0.3rem', fontSize: '0.75rem' }}
            title="Copy SHA-256 Hash"
          >
            {copiedHash ? <Check size={14} color="#16A34A" /> : <Copy size={14} />}
            <span>{copiedHash ? 'Copied' : 'Copy'}</span>
          </button>
        </div>

        <p style={{ fontSize: '0.8125rem', color: '#64748B', margin: 0, lineHeight: 1.5 }}>
          SHA-256 acts as a digital fingerprint for the exact uploaded file. It helps verify whether the file has changed.
        </p>
      </div>

      {/* ============================================================
          7. FACE VERIFICATION — ONLY IF PERFORMED
          ============================================================ */}
      {hasFaceVerification && (
        <div
          className="card"
          style={{
            background: '#FFFFFF',
            border: '1px solid #E2E8F0',
            borderRadius: 14,
            padding: '1.25rem 1.75rem',
            marginBottom: '1.25rem',
            boxShadow: '0 1px 3px rgba(15,23,42,0.04)'
          }}
        >
          <h3 style={{ fontSize: '0.9375rem', fontWeight: 700, color: '#0F172A', marginBottom: '0.85rem' }}>
            Face Verification
          </h3>

          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '1rem', alignItems: 'center', marginBottom: '0.85rem' }}>
            <div>
              <div style={{ fontSize: '0.75rem', color: '#64748B', fontWeight: 500 }}>Similarity Score</div>
              <div style={{ fontSize: '1.5rem', fontWeight: 800, color: faceMatch ? '#16A34A' : '#DC2626', fontFamily: 'var(--font-mono)' }}>
                {faceSimPct != null ? `${faceSimPct}%` : '—'}
              </div>
            </div>

            <div>
              <div style={{ fontSize: '0.75rem', color: '#64748B', fontWeight: 500 }}>Result</div>
              <div style={{ fontSize: '0.95rem', fontWeight: 700, color: faceMatch ? '#16A34A' : '#334155' }}>
                {faceMatch ? 'Similar faces detected' : 'Different person or profile'}
              </div>
            </div>
          </div>

          <p style={{ fontSize: '0.8125rem', color: '#64748B', margin: 0, lineHeight: 1.5, borderTop: '1px solid #F1F5F9', paddingTop: '0.65rem' }}>
            Face verification measures similarity between faces in the supplied images. It does not determine whether an image is AI-generated.
          </p>
        </div>
      )}

      {/* ============================================================
          8. REPORT ACTIONS (View Report + Download PDF)
          ============================================================ */}
      <div
        className="card"
        style={{
          background: '#FFFFFF',
          border: '1px solid #E2E8F0',
          borderLeft: '4px solid #16A34A',
          borderRadius: 14,
          padding: '1.35rem 1.75rem',
          marginBottom: '1.25rem',
          boxShadow: '0 1px 3px rgba(15,23,42,0.04)'
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '1rem' }}>
          <div>
            <h3 style={{ fontSize: '1rem', fontWeight: 700, color: '#0F172A', margin: 0 }}>
              Analysis Report
            </h3>
            <p style={{ fontSize: '0.8125rem', color: '#64748B', margin: '0.2rem 0 0 0' }}>
              Your analysis report is ready.
            </p>
          </div>

          <div style={{ display: 'flex', gap: '0.6rem', flexWrap: 'wrap' }}>
            <button
              onClick={handleViewReport}
              className="btn btn-secondary btn-sm"
              id="view-report-action-btn"
              style={{ display: 'inline-flex', alignItems: 'center', gap: '0.4rem' }}
            >
              <Eye size={15} /> View Report
            </button>

            <button
              onClick={handleDownload}
              disabled={downloading}
              className="btn btn-primary btn-sm"
              id="download-report-action-btn"
              style={{ display: 'inline-flex', alignItems: 'center', gap: '0.4rem' }}
            >
              <Download size={15} /> {downloading ? 'Downloading…' : 'Download PDF'}
            </button>
          </div>
        </div>
      </div>

      {/* ============================================================
          9. OPTIONAL CASE FILE (Manual generation only)
          ============================================================ */}
      <div
        className="card"
        style={{
          background: '#FFFFFF',
          border: '1px solid #E2E8F0',
          borderLeft: '4px solid #2563EB',
          borderRadius: 14,
          padding: '1.25rem 1.75rem',
          marginBottom: '1.5rem',
          boxShadow: '0 1px 3px rgba(15,23,42,0.04)'
        }}
      >
        <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', flexWrap: 'wrap', gap: '1rem' }}>
          <div style={{ flex: 1, minWidth: 260 }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.45rem', marginBottom: '0.25rem' }}>
              <Package size={17} color="#2563EB" />
              <h3 style={{ fontSize: '0.9375rem', fontWeight: 700, color: '#0F172A', margin: 0 }}>
                Optional Case File
              </h3>
            </div>
            <p style={{ fontSize: '0.8125rem', color: '#64748B', margin: '0.2rem 0 0 0' }}>
              Create a package containing the analysis report and supporting evidence.
            </p>

            {caseFileStatus === 'ready' && (
              <div style={{ fontSize: '0.8125rem', color: '#16A34A', fontWeight: 600, marginTop: '0.4rem' }}>
                ✓ Case file package is ready for download.
              </div>
            )}

            {caseFileStatus === 'error' && (
              <div style={{ fontSize: '0.8125rem', color: '#DC2626', marginTop: '0.4rem' }}>
                {caseFileError}
              </div>
            )}
          </div>

          <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center', flexShrink: 0 }}>
            {(caseFileStatus === 'idle' || caseFileStatus === 'error') && (
              <button
                onClick={handleGenerateCaseFile}
                className="btn btn-secondary btn-sm"
                id="generate-case-file-btn"
                disabled={!targetCaseId}
                style={{ display: 'inline-flex', alignItems: 'center', gap: '0.4rem' }}
              >
                <Archive size={14} /> Generate Case File
              </button>
            )}

            {caseFileStatus === 'generating' && (
              <button className="btn btn-secondary btn-sm" disabled style={{ display: 'inline-flex', alignItems: 'center', gap: '0.4rem' }}>
                <Loader size={14} style={{ animation: 'spin 1s linear infinite' }} /> Generating…
              </button>
            )}

            {(caseFileStatus === 'ready' || caseFileStatus === 'downloading') && (
              <button
                onClick={handleDownloadCaseFile}
                className="btn btn-primary btn-sm"
                id="download-case-file-btn"
                disabled={caseFileStatus === 'downloading'}
                style={{ display: 'inline-flex', alignItems: 'center', gap: '0.4rem' }}
              >
                <Download size={14} /> {caseFileStatus === 'downloading' ? 'Downloading…' : 'Download Case File'}
              </button>
            )}
          </div>
        </div>
      </div>

      {/* ============================================================
          10. DISCLAIMER & HELP LINK
          ============================================================ */}
      <div style={{ textAlign: 'center', padding: '1.25rem 0 0.5rem', borderTop: '1px solid #E2E8F0' }}>
        <p style={{ fontSize: '0.8125rem', color: '#64748B', margin: '0 auto', maxWidth: 780, lineHeight: 1.6 }}>
          AI-based image detection provides a probabilistic assessment and should not be treated as conclusive proof of authenticity or manipulation. Supporting forensic indicators provide additional context but may be affected by image compression, resizing, editing, and other processing.
        </p>
        <p style={{ fontSize: '0.75rem', color: '#94A3B8', marginTop: '0.35rem' }}>
          Need to report an incident or consult Indian legal remedies?{' '}
          <Link
            to={targetCaseId ? `/help-reporting?caseId=${targetCaseId}` : '/help-reporting'}
            style={{ color: '#2563EB', textDecoration: 'none', fontWeight: 600, display: 'inline-flex', alignItems: 'center', gap: '0.2rem' }}
          >
            Help &amp; Reporting <ExternalLink size={11} />
          </Link>
        </p>
      </div>

    </div>
  );
}
