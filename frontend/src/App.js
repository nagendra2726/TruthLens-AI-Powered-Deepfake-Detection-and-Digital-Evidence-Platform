import React, { useState, useEffect, useRef } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate, useLocation } from 'react-router-dom';
import Login from './components/Login';
import Register from './components/Register';
import './App.css';
import {
    Chart as ChartJS,
    CategoryScale,
    LinearScale,
    BarElement,
    Title,
    Tooltip,
    Legend,
    ArcElement,
} from 'chart.js';
import { Bar, Doughnut } from 'react-chartjs-2';

// Register ChartJS components
ChartJS.register(
    CategoryScale,
    LinearScale,
    BarElement,
    Title,
    Tooltip,
    Legend,
    ArcElement
);

const API_BASE_URL = window.location.hostname === 'localhost' && window.location.port === '3000'
  ? 'http://localhost:8000'  // Local dev (npm start)
  : '/api';                   // Docker (Nginx proxy)

// Protected Route Wrapper
const ProtectedRoute = ({ children, isAuthenticated }) => {
    const location = useLocation();
    if (!isAuthenticated) {
        return <Navigate to="/login" state={{ from: location }} replace />;
    }
    return children;
};

// ---------------------------------------------------------------------------
// Utility: map AuthenticityResult prediction to display colours / icons
// ---------------------------------------------------------------------------
function getAuthenticityStyle(prediction) {
    switch (prediction) {
        case 'LIKELY_REAL':
            return { color: 'var(--success)', icon: '✅', label: 'LIKELY REAL' };
        case 'LIKELY_AI_GENERATED':
            return { color: 'var(--danger)', icon: '⚠️', label: 'LIKELY AI-GENERATED' };
        case 'INCONCLUSIVE':
        default:
            return { color: '#f59e0b', icon: '❓', label: 'INCONCLUSIVE' };
    }
}

// ---------------------------------------------------------------------------
// AuthenticityCard – displays one side of the comparison
// ---------------------------------------------------------------------------
function AuthenticityCard({ title, analysis, previewUrl, mediaType }) {
    if (!analysis) return null;

    if (analysis.status === 'failed') {
        return (
            <div className="card" style={{ borderTop: '4px solid var(--danger)', flex: 1 }}>
                <h3 style={{ fontSize: '1rem', fontWeight: '600', marginBottom: '0.75rem', color: 'var(--text-secondary)' }}>
                    {title}
                </h3>
                <div style={{ color: 'var(--danger)', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                    <span>❌</span>
                    <span style={{ fontSize: '0.9rem' }}>Analysis failed</span>
                </div>
                {analysis.error && (
                    <p style={{ marginTop: '0.5rem', fontSize: '0.8rem', color: 'var(--text-secondary)' }}>
                        {typeof analysis.error === 'string' ? analysis.error : JSON.stringify(analysis.error)}
                    </p>
                )}
            </div>
        );
    }

    const style = getAuthenticityStyle(analysis.prediction);
    const aiPct = ((analysis.ai_probability || 0) * 100).toFixed(1);
    const realPct = ((analysis.real_probability || 0) * 100).toFixed(1);

    const doughnutData = {
        labels: ['Real', 'AI-Generated'],
        datasets: [{
            data: [parseFloat(realPct), parseFloat(aiPct)],
            backgroundColor: ['rgba(16, 185, 129, 0.7)', 'rgba(239, 68, 68, 0.7)'],
            borderColor: ['rgba(16, 185, 129, 1)', 'rgba(239, 68, 68, 1)'],
            borderWidth: 2,
        }],
    };

    return (
        <div className="card" style={{ borderTop: `4px solid ${style.color}`, flex: 1, minWidth: 0 }}>
            {/* Card header */}
            <h3 style={{ fontSize: '1rem', fontWeight: '700', marginBottom: '0.5rem', color: 'var(--text-secondary)', letterSpacing: '0.05em', textTransform: 'uppercase' }}>
                {title}
            </h3>
            {analysis.filename && (
                <p style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', marginBottom: '1rem', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                    {analysis.filename}
                </p>
            )}

            {/* Preview */}
            {previewUrl && (
                <div style={{ marginBottom: '1rem', borderRadius: 'var(--radius-md)', overflow: 'hidden', background: '#000', height: '160px', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                    {mediaType === 'video'
                        ? <video src={previewUrl} style={{ height: '100%', width: '100%', objectFit: 'contain' }} />
                        : <img src={previewUrl} alt={title} style={{ height: '100%', width: '100%', objectFit: 'contain' }} />
                    }
                </div>
            )}

            {/* Authenticity verdict */}
            <div style={{ textAlign: 'center', marginBottom: '1.25rem' }}>
                <div style={{ fontSize: '1.8rem', marginBottom: '0.25rem' }}>{style.icon}</div>
                <div style={{ fontSize: '1.25rem', fontWeight: '800', color: style.color }}>{style.label}</div>
            </div>

            {/* Probability bars */}
            <div style={{ marginBottom: '1rem' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.8rem', marginBottom: '0.25rem' }}>
                    <span style={{ color: 'var(--text-secondary)' }}>AI-Generated Probability</span>
                    <span style={{ fontWeight: '600', color: 'var(--danger)' }}>{aiPct}%</span>
                </div>
                <div style={{ background: 'rgba(255,255,255,0.08)', borderRadius: '999px', height: '8px', overflow: 'hidden' }}>
                    <div style={{ width: `${aiPct}%`, height: '100%', background: 'var(--danger)', borderRadius: '999px', transition: 'width 0.6s ease' }} />
                </div>

                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.8rem', marginBottom: '0.25rem', marginTop: '0.75rem' }}>
                    <span style={{ color: 'var(--text-secondary)' }}>Real Probability</span>
                    <span style={{ fontWeight: '600', color: 'var(--success)' }}>{realPct}%</span>
                </div>
                <div style={{ background: 'rgba(255,255,255,0.08)', borderRadius: '999px', height: '8px', overflow: 'hidden' }}>
                    <div style={{ width: `${realPct}%`, height: '100%', background: 'var(--success)', borderRadius: '999px', transition: 'width 0.6s ease' }} />
                </div>
            </div>

            {/* Confidence badge */}
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '1rem' }}>
                <span style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>Confidence:</span>
                <span style={{
                    fontSize: '0.75rem', fontWeight: '700', padding: '0.2rem 0.6rem', borderRadius: '999px',
                    background: analysis.confidence === 'VERY_HIGH' ? 'rgba(16,185,129,0.15)'
                        : analysis.confidence === 'HIGH' ? 'rgba(59,130,246,0.15)'
                        : analysis.confidence === 'MEDIUM' ? 'rgba(245,158,11,0.15)'
                        : 'rgba(255,255,255,0.08)',
                    color: analysis.confidence === 'VERY_HIGH' ? 'var(--success)'
                        : analysis.confidence === 'HIGH' ? '#60a5fa'
                        : analysis.confidence === 'MEDIUM' ? '#f59e0b'
                        : 'var(--text-secondary)',
                    letterSpacing: '0.05em',
                }}>
                    {analysis.confidence || 'N/A'}
                </span>
            </div>

            {/* Donut chart */}
            <div style={{ height: '160px', display: 'flex', justifyContent: 'center' }}>
                <Doughnut data={doughnutData} options={{
                    maintainAspectRatio: false,
                    plugins: { legend: { position: 'bottom', labels: { color: '#94a3b8', font: { size: 11 } } } },
                }} />
            </div>

            {/* Individual model scores */}
            {analysis.model_results && Object.keys(analysis.model_results).length > 0 && (
                <details style={{ marginTop: '1rem' }}>
                    <summary style={{ cursor: 'pointer', fontSize: '0.8rem', color: 'var(--text-secondary)', userSelect: 'none' }}>
                        Individual model scores ▸
                    </summary>
                    <div style={{ marginTop: '0.5rem' }}>
                        {Object.entries(analysis.model_results).map(([modelName, res]) => {
                            if (res && res.error) {
                                return (
                                    <div key={modelName} style={{ fontSize: '0.78rem', color: 'var(--danger)', marginBottom: '0.25rem' }}>
                                        {modelName}: ERROR — {res.error}
                                    </div>
                                );
                            }
                            const prob = res?.probability;
                            return (
                                <div key={modelName} style={{ marginBottom: '0.5rem' }}>
                                    <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.78rem' }}>
                                        <span style={{ color: 'var(--text-secondary)' }}>{modelName}</span>
                                        <span style={{ color: prob >= 0.5 ? 'var(--danger)' : 'var(--success)' }}>
                                            {prob !== undefined ? `${(prob * 100).toFixed(1)}%` : 'N/A'}
                                        </span>
                                    </div>
                                    {prob !== undefined && (
                                        <div style={{ background: 'rgba(255,255,255,0.06)', borderRadius: '999px', height: '5px', overflow: 'hidden', marginTop: '0.2rem' }}>
                                            <div style={{ width: `${(prob * 100).toFixed(1)}%`, height: '100%', background: prob >= 0.5 ? 'var(--danger)' : 'var(--success)', borderRadius: '999px' }} />
                                        </div>
                                    )}
                                </div>
                            );
                        })}
                    </div>
                </details>
            )}
        </div>
    );
}

// ---------------------------------------------------------------------------
// MediaUploadZone – reusable drop-zone for Compare Mode
// ---------------------------------------------------------------------------
function MediaUploadZone({ id, label, sublabel, file, preview, onFileChange, disabled }) {
    const inputRef = useRef(null);
    const [dragActive, setDragActive] = useState(false);

    const handleDrag = (e) => {
        e.preventDefault(); e.stopPropagation();
        if (disabled) return;
        setDragActive(e.type === 'dragenter' || e.type === 'dragover');
    };
    const handleDrop = (e) => {
        e.preventDefault(); e.stopPropagation();
        setDragActive(false);
        if (disabled) return;
        if (e.dataTransfer.files?.[0]) onFileChange(e.dataTransfer.files[0]);
    };

    return (
        <div style={{ flex: 1, minWidth: 0 }}>
            <p style={{ fontSize: '0.85rem', fontWeight: '600', color: 'var(--text-secondary)', marginBottom: '0.5rem', textTransform: 'uppercase', letterSpacing: '0.06em' }}>
                {label}
            </p>
            <div
                onClick={() => !disabled && inputRef.current?.click()}
                onDragEnter={handleDrag} onDragLeave={handleDrag} onDragOver={handleDrag} onDrop={handleDrop}
                style={{
                    border: `2px dashed ${dragActive ? 'var(--accent-primary)' : 'rgba(255,255,255,0.12)'}`,
                    borderRadius: 'var(--radius-md)',
                    padding: '1.5rem',
                    textAlign: 'center',
                    cursor: disabled ? 'not-allowed' : 'pointer',
                    background: dragActive ? 'rgba(59,130,246,0.06)' : 'rgba(30,41,59,0.5)',
                    transition: 'all 0.2s ease',
                    opacity: disabled ? 0.6 : 1,
                    minHeight: '140px',
                    display: 'flex',
                    flexDirection: 'column',
                    alignItems: 'center',
                    justifyContent: 'center',
                }}
            >
                <input
                    ref={inputRef}
                    type="file"
                    id={id}
                    accept="image/jpeg,image/png,image/webp,video/mp4,video/quicktime,video/x-msvideo,video/x-matroska"
                    style={{ display: 'none' }}
                    disabled={disabled}
                    onChange={(e) => e.target.files?.[0] && onFileChange(e.target.files[0])}
                />
                {preview ? (
                    <div style={{ width: '100%' }}>
                        <img
                            src={preview}
                            alt={label}
                            style={{ maxHeight: '100px', maxWidth: '100%', objectFit: 'contain', borderRadius: '6px', marginBottom: '0.5rem' }}
                            onError={(e) => { e.target.style.display = 'none'; }}
                        />
                        <p style={{ fontSize: '0.78rem', color: 'var(--text-secondary)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                            {file?.name}
                        </p>
                        <button
                            type="button"
                            onClick={(e) => { e.stopPropagation(); onFileChange(null); }}
                            style={{ marginTop: '0.4rem', fontSize: '0.75rem', color: 'var(--accent-primary)', background: 'none', border: 'none', cursor: 'pointer', padding: 0 }}
                        >
                            Change file
                        </button>
                    </div>
                ) : (
                    <>
                        <svg width="28" height="28" fill="none" stroke="currentColor" viewBox="0 0 24 24" style={{ color: 'var(--accent-primary)', marginBottom: '0.75rem' }}>
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
                        </svg>
                        <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', margin: 0 }}>Click or drag & drop</p>
                        <p style={{ fontSize: '0.75rem', color: 'rgba(148,163,184,0.6)', margin: '0.25rem 0 0' }}>{sublabel}</p>
                    </>
                )}
            </div>
        </div>
    );
}

// ---------------------------------------------------------------------------
// Dashboard (existing single-file mode + new Compare Mode tab)
// ---------------------------------------------------------------------------
function Dashboard({ onLogout }) {
    // ---- Existing single-file state (unchanged) ----
    const [selectedFile, setSelectedFile] = useState(null);
    const [previewUrl, setPreviewUrl] = useState(null);
    const [mediaType, setMediaType] = useState('image');
    const [isAnalyzing, setIsAnalyzing] = useState(false);
    const [results, setResults] = useState(null);
    const [error, setError] = useState(null);
    const [systemHealth, setSystemHealth] = useState(null);

    // ---- TruthLens Compare Mode state (new) ----
    const [analysisMode, setAnalysisMode] = useState('single'); // 'single' | 'compare'
    const [referenceFile, setReferenceFile] = useState(null);
    const [referencePreview, setReferencePreview] = useState(null);
    const [suspectedFile, setSuspectedFile] = useState(null);
    const [suspectedPreview, setSuspectedPreview] = useState(null);
    const [isComparing, setIsComparing] = useState(false);
    const [compareResults, setCompareResults] = useState(null);
    const [compareError, setCompareError] = useState(null);

    useEffect(() => {
        fetch(`${API_BASE_URL}/health`)
            .then((res) => res.json())
            .then((data) => setSystemHealth(data))
            .catch((err) => console.error('Health check failed:', err));
    }, []);

    // ---- Existing handlers (unchanged) ----
    const handleFileChange = (event) => {
        const file = event.target.files[0];
        if (file) {
            setSelectedFile(file);
            setResults(null);
            setError(null);
            const objectUrl = URL.createObjectURL(file);
            setPreviewUrl(objectUrl);
            if (file.type.startsWith('video/')) {
                setMediaType('video');
            } else {
                setMediaType('image');
            }
        }
    };

    const handleDemoImage = () => {
        fetch('/demo_image.jpg')
            .then((res) => res.blob())
            .then((blob) => {
                const file = new File([blob], 'demo_image.jpg', { type: 'image/jpeg' });
                setSelectedFile(file);
                setPreviewUrl('/demo_image.jpg');
                setMediaType('image');
                setResults(null);
                setError(null);
            })
            .catch(() => setError('Failed to load demo image'));
    };

    const handleDemoVideo = () => {
        fetch('/demo_video.mp4')
            .then((res) => res.blob())
            .then((blob) => {
                const file = new File([blob], 'demo_video.mp4', { type: 'video/mp4' });
                setSelectedFile(file);
                setPreviewUrl('/demo_video.mp4');
                setMediaType('video');
                setResults(null);
                setError(null);
            })
            .catch(() => setError('Failed to load demo video'));
    };

    const handleDemoAudio = () => {
        fetch('/demo_audio.wav')
            .then((res) => res.blob())
            .then((blob) => {
                const file = new File([blob], 'demo_audio.wav', { type: 'audio/wav' });
                setSelectedFile(file);
                setPreviewUrl('/demo_audio.wav');
                setMediaType('audio');
                setResults(null);
                setError(null);
            })
            .catch(() => setError('Failed to load demo audio'));
    };

    const handleAnalyze = async () => {
        if (!selectedFile) return;
        setIsAnalyzing(true);
        setError(null);
        setResults(null);

        const formData = new FormData();
        formData.append('file', selectedFile);
        formData.append('media_type', mediaType);

        try {
            const response = await fetch(`${API_BASE_URL}/detect`, {
                method: 'POST',
                body: formData,
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || 'Analysis failed');
            }

            const data = await response.json();
            setResults(data);
        } catch (err) {
            setError(err.message);
        } finally {
            setIsAnalyzing(false);
        }
    };

    // ---- TruthLens Compare Mode handlers (new) ----
    const handleReferenceFileChange = (file) => {
        if (!file) {
            setReferenceFile(null);
            setReferencePreview(null);
            return;
        }
        setReferenceFile(file);
        if (file.type.startsWith('video/')) {
            setReferencePreview(URL.createObjectURL(file));
        } else if (file.type.startsWith('image/')) {
            setReferencePreview(URL.createObjectURL(file));
        } else {
            setReferencePreview(null);
        }
        setCompareResults(null);
        setCompareError(null);
    };

    const handleSuspectedFileChange = (file) => {
        if (!file) {
            setSuspectedFile(null);
            setSuspectedPreview(null);
            return;
        }
        setSuspectedFile(file);
        if (file.type.startsWith('video/') || file.type.startsWith('image/')) {
            setSuspectedPreview(URL.createObjectURL(file));
        } else {
            setSuspectedPreview(null);
        }
        setCompareResults(null);
        setCompareError(null);
    };

    const handleCompareAnalyze = async () => {
        if (!referenceFile || !suspectedFile) return;
        setIsComparing(true);
        setCompareError(null);
        setCompareResults(null);

        const formData = new FormData();
        formData.append('reference_media', referenceFile);
        formData.append('suspected_media', suspectedFile);

        try {
            const response = await fetch(`${API_BASE_URL}/analyze/compare`, {
                method: 'POST',
                body: formData,
            });

            const data = await response.json();

            if (!response.ok) {
                const detail = data.detail;
                throw new Error(
                    typeof detail === 'string' ? detail
                        : detail?.message || 'Comparison failed'
                );
            }

            setCompareResults(data);
        } catch (err) {
            setCompareError(err.message);
        } finally {
            setIsComparing(false);
        }
    };

    // ---- Existing renderHealthStatus (unchanged) ----
    const renderHealthStatus = () => {
        if (!systemHealth) return <span style={{ color: 'var(--text-secondary)' }}>Checking system...</span>;
        const st = systemHealth.overall_api_status || 'Unknown';
        const color = st === 'healthy' ? 'var(--success)' : 'var(--danger)';
        return (
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                <span style={{ width: '8px', height: '8px', borderRadius: '50%', backgroundColor: color, boxShadow: `0 0 8px ${color}` }} />
                <span style={{ color, fontWeight: 600, fontSize: '0.875rem' }}>{st.toUpperCase()}</span>
            </div>
        );
    };

    // ---- Existing renderResults (unchanged) ----
    const renderResults = () => {
        if (!results) return null;
        const isFake = results.is_likely_deepfake;
        const confidence = (results.deepfake_probability * 100).toFixed(1);
        const verdictColor = isFake ? 'var(--danger)' : 'var(--success)';
        const verdictText = isFake ? 'FAKE' : 'REAL';

        const barData = {
            labels: Object.keys(results.model_results || {}),
            datasets: [{
                label: 'Fake Probability',
                data: Object.values(results.model_results || {}).map(r => r.probability ? r.probability * 100 : 0),
                backgroundColor: 'rgba(59, 130, 246, 0.6)',
                borderColor: 'rgba(59, 130, 246, 1)',
                borderWidth: 1,
                borderRadius: 4,
            }],
        };

        const doughnutData = {
            labels: ['Real', 'Fake'],
            datasets: [{
                data: [100 - (results.deepfake_probability * 100), results.deepfake_probability * 100],
                backgroundColor: ['rgba(16, 185, 129, 0.6)', 'rgba(239, 68, 68, 0.6)'],
                borderColor: ['rgba(16, 185, 129, 1)', 'rgba(239, 68, 68, 1)'],
                borderWidth: 1,
            }],
        };

        return (
            <div className="animate-fade-in" style={{ marginTop: '2rem' }}>
                <div className="card" style={{ textAlign: 'center', marginBottom: '2rem', borderTop: `4px solid ${verdictColor}` }}>
                    <h2 style={{ fontSize: '1.5rem', marginBottom: '0.5rem' }}>Analysis Verdict</h2>
                    <div style={{ fontSize: '3rem', fontWeight: '800', color: verdictColor, textShadow: `0 0 20px ${verdictColor}40` }}>
                        {verdictText}
                    </div>
                    <p style={{ color: 'var(--text-secondary)', fontSize: '1.1rem' }}>
                        Confidence: <strong style={{ color: 'var(--text-primary)' }}>{confidence}%</strong>
                    </p>
                </div>

                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: '1.5rem' }}>
                    <div className="card">
                        <h3 style={{ marginBottom: '1rem', borderBottom: '1px solid rgba(255,255,255,0.1)', paddingBottom: '0.5rem' }}>Ensemble Score</h3>
                        <div style={{ height: '250px', display: 'flex', justifyContent: 'center' }}>
                            <Doughnut data={doughnutData} options={{ maintainAspectRatio: false, plugins: { legend: { position: 'bottom', labels: { color: '#94a3b8' } } } }} />
                        </div>
                    </div>
                    <div className="card">
                        <h3 style={{ marginBottom: '1rem', borderBottom: '1px solid rgba(255,255,255,0.1)', paddingBottom: '0.5rem' }}>Individual Model Scores</h3>
                        <div style={{ height: '250px' }}>
                            <Bar data={barData} options={{ maintainAspectRatio: false, scales: { y: { beginAtZero: true, max: 100, grid: { color: 'rgba(255,255,255,0.05)' }, ticks: { color: '#94a3b8' } }, x: { grid: { display: false }, ticks: { color: '#94a3b8' } } }, plugins: { legend: { display: false } } }} />
                        </div>
                    </div>
                </div>
            </div>
        );
    };

    // ---- TruthLens: renderCompareResults (new) ----
    const renderCompareResults = () => {
        if (!compareResults) return null;

        const ref = compareResults.reference_analysis;
        const sus = compareResults.suspected_analysis;

        return (
            <div className="animate-fade-in" style={{ marginTop: '2rem' }}>
                {/* Disclaimer banner */}
                <div style={{
                    background: 'rgba(245,158,11,0.08)',
                    border: '1px solid rgba(245,158,11,0.25)',
                    borderRadius: 'var(--radius-md)',
                    padding: '0.75rem 1rem',
                    marginBottom: '1.5rem',
                    display: 'flex',
                    alignItems: 'flex-start',
                    gap: '0.75rem',
                    fontSize: '0.82rem',
                    color: '#d1a822',
                    lineHeight: 1.5,
                }}>
                    <span style={{ fontSize: '1rem', flexShrink: 0 }}>ℹ️</span>
                    <span>
                        TruthLens independently evaluates the authenticity of the reference and suspected media.
                        {' '}<strong>An AI-generated classification alone does not establish that the media is a deepfake.</strong>
                        {' '}Contextual assessment will be available in Task 3.
                    </span>
                </div>

                {/* Meta row */}
                <div style={{ display: 'flex', gap: '1rem', marginBottom: '1.5rem', flexWrap: 'wrap', fontSize: '0.8rem', color: 'var(--text-secondary)' }}>
                    {compareResults.processing_time_seconds !== undefined && (
                        <span>⏱ {compareResults.processing_time_seconds}s</span>
                    )}
                    {compareResults.ensemble_method_used && (
                        <span>🔗 Ensemble: {compareResults.ensemble_method_used}</span>
                    )}
                    {compareResults.threshold_used !== undefined && (
                        <span>📊 Threshold: {compareResults.threshold_used}</span>
                    )}
                </div>

                {/* Two-column results */}
                <div style={{ display: 'flex', gap: '1.5rem', flexWrap: 'wrap' }}>
                    <AuthenticityCard
                        title="Reference Media"
                        analysis={ref}
                        previewUrl={referencePreview}
                        mediaType={referenceFile?.type?.startsWith('video/') ? 'video' : 'image'}
                    />
                    <AuthenticityCard
                        title="Suspected Media"
                        analysis={sus}
                        previewUrl={suspectedPreview}
                        mediaType={suspectedFile?.type?.startsWith('video/') ? 'video' : 'image'}
                    />
                </div>
            </div>
        );
    };

    // ---- Render ----
    return (
        <div className="App">
            {/* Header */}
            <header style={{
                padding: '1.5rem 2rem',
                borderBottom: '1px solid rgba(255,255,255,0.05)',
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
                background: 'rgba(15, 23, 42, 0.8)',
                backdropFilter: 'blur(10px)',
                position: 'sticky',
                top: 0,
                zIndex: 100,
            }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
                    <div style={{
                        width: '40px', height: '40px',
                        background: 'linear-gradient(135deg, var(--accent-primary), var(--accent-secondary))',
                        borderRadius: '8px', display: 'flex', alignItems: 'center',
                        justifyContent: 'center', fontWeight: 'bold', fontSize: '1.2rem',
                    }}>TL</div>
                    <div>
                        <h1 style={{ fontSize: '1.5rem', fontWeight: '700', letterSpacing: '-0.025em', margin: 0 }}>TruthLens</h1>
                        <p style={{ fontSize: '0.7rem', color: 'var(--text-secondary)', margin: 0, letterSpacing: '0.1em' }}>AI-POWERED DEEPFAKE DETECTION</p>
                    </div>
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '1.5rem' }}>
                    {renderHealthStatus()}
                    <button onClick={onLogout} className="btn btn-secondary" style={{ padding: '0.5rem 1rem', fontSize: '0.9rem' }}>Logout</button>
                </div>
            </header>

            <main className="container">
                {/* Hero */}
                <div style={{ textAlign: 'center', marginBottom: '2.5rem', paddingTop: '2rem' }}>
                    <h2 className="text-gradient" style={{ fontSize: '3rem', fontWeight: '800', marginBottom: '1rem', lineHeight: 1.2 }}>
                        {analysisMode === 'compare' ? 'Multi-Source Authenticity Verification' : 'Detect Deepfakes with\nEnterprise Precision'}
                    </h2>
                    <p style={{ color: 'var(--text-secondary)', fontSize: '1.1rem', maxWidth: '640px', margin: '0 auto' }}>
                        {analysisMode === 'compare'
                            ? 'Upload both reference and suspected media. TruthLens independently analyzes each file — the reference is never assumed to be genuine.'
                            : 'Upload your media to analyze it against our multi-model ensemble engine.'}
                    </p>
                </div>

                {/* Mode Tab Switcher */}
                <div style={{ display: 'flex', justifyContent: 'center', marginBottom: '2rem' }}>
                    <div style={{
                        display: 'flex', background: 'rgba(30,41,59,0.8)',
                        borderRadius: '12px', padding: '4px', gap: '4px',
                        border: '1px solid rgba(255,255,255,0.07)',
                    }}>
                        {[
                            { id: 'single', label: '🔍 Single Analysis', desc: 'DeepSafe original' },
                            { id: 'compare', label: '⚖️ Compare Media', desc: 'TruthLens Task 1' },
                        ].map((tab) => (
                            <button
                                key={tab.id}
                                onClick={() => setAnalysisMode(tab.id)}
                                style={{
                                    padding: '0.6rem 1.4rem', borderRadius: '9px', border: 'none', cursor: 'pointer',
                                    fontWeight: '600', fontSize: '0.875rem', transition: 'all 0.2s ease',
                                    background: analysisMode === tab.id
                                        ? 'linear-gradient(135deg, var(--accent-primary), var(--accent-secondary))'
                                        : 'transparent',
                                    color: analysisMode === tab.id ? '#fff' : 'var(--text-secondary)',
                                    boxShadow: analysisMode === tab.id ? '0 2px 12px rgba(59,130,246,0.35)' : 'none',
                                }}
                            >
                                {tab.label}
                            </button>
                        ))}
                    </div>
                </div>

                {/* ============================================================
                    SINGLE ANALYSIS MODE — existing flow, completely unchanged
                    ============================================================ */}
                {analysisMode === 'single' && (
                    <>
                        <div className="card" style={{ maxWidth: '800px', margin: '0 auto', padding: '3rem', borderStyle: 'dashed', borderWidth: '2px', borderColor: 'rgba(255,255,255,0.1)', backgroundColor: 'rgba(30, 41, 59, 0.5)' }}>
                            <input
                                type="file"
                                id="file-upload"
                                style={{ display: 'none' }}
                                onChange={handleFileChange}
                                accept="image/*,video/*"
                            />
                            <label htmlFor="file-upload" style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', cursor: 'pointer' }}>
                                <div style={{
                                    width: '64px', height: '64px', borderRadius: '50%',
                                    backgroundColor: 'rgba(59, 130, 246, 0.1)',
                                    display: 'flex', alignItems: 'center', justifyContent: 'center',
                                    marginBottom: '1.5rem', color: 'var(--accent-primary)',
                                }}>
                                    <svg width="32" height="32" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
                                    </svg>
                                </div>
                                <span style={{ fontSize: '1.25rem', fontWeight: '600', marginBottom: '0.5rem' }}>
                                    {selectedFile ? selectedFile.name : 'Click to Upload or Drag & Drop'}
                                </span>
                                <span style={{ color: 'var(--text-secondary)' }}>Supported formats: JPG, PNG, MP4, AVI</span>
                            </label>
                        </div>

                        {previewUrl && (
                            <div className="animate-fade-in" style={{ marginTop: '2rem', maxWidth: '800px', margin: '2rem auto 0' }}>
                                <div className="card" style={{ overflow: 'hidden', padding: 0 }}>
                                    <div style={{ position: 'relative', width: '100%', height: '400px', backgroundColor: '#000' }}>
                                        {mediaType === 'video'
                                            ? <video src={previewUrl} controls style={{ width: '100%', height: '100%', objectFit: 'contain' }} />
                                            : <img src={previewUrl} alt="Preview" style={{ width: '100%', height: '100%', objectFit: 'contain' }} />
                                        }
                                    </div>
                                    <div style={{ padding: '1.5rem', display: 'flex', justifyContent: 'space-between', alignItems: 'center', backgroundColor: 'var(--bg-secondary)' }}>
                                        <div>
                                            <h3 style={{ fontSize: '1.1rem', fontWeight: '600' }}>Ready to Analyze</h3>
                                            <p style={{ color: 'var(--text-secondary)', fontSize: '0.9rem' }}>
                                                {selectedFile.size > 1024 * 1024 ? `${(selectedFile.size / (1024 * 1024)).toFixed(2)} MB` : `${(selectedFile.size / 1024).toFixed(2)} KB`}
                                            </p>
                                        </div>
                                        <div style={{ display: 'flex', gap: '0.5rem' }}>
                                            <button onClick={handleDemoVideo} className="btn btn-secondary">🎬 Demo Video</button>
                                            <button onClick={handleDemoAudio} className="btn btn-secondary">🎵 Demo Audio</button>
                                            <button
                                                className="btn btn-primary"
                                                onClick={handleAnalyze}
                                                disabled={isAnalyzing}
                                                style={{ opacity: isAnalyzing ? 0.7 : 1, minWidth: '150px' }}
                                            >
                                                {isAnalyzing ? 'Processing...' : 'Run DeepSafe'}
                                            </button>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        )}

                        {error && (
                            <div className="animate-fade-in" style={{ maxWidth: '800px', margin: '2rem auto 0', padding: '1rem', borderRadius: 'var(--radius-md)', backgroundColor: 'rgba(239, 68, 68, 0.1)', border: '1px solid rgba(239, 68, 68, 0.2)', color: 'var(--danger)', display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                                {error}
                            </div>
                        )}

                        <div style={{ maxWidth: '800px', margin: '0 auto' }}>
                            {renderResults()}
                        </div>
                    </>
                )}

                {/* ============================================================
                    COMPARE MODE — TruthLens Task 1
                    ============================================================ */}
                {analysisMode === 'compare' && (
                    <div style={{ maxWidth: '900px', margin: '0 auto' }}>
                        {/* Upload zones */}
                        <div className="card" style={{ padding: '2rem' }}>
                            <div style={{ display: 'flex', gap: '1.5rem', flexWrap: 'wrap', marginBottom: '1.5rem' }}>
                                <MediaUploadZone
                                    id="reference-upload"
                                    label="Reference Media"
                                    sublabel="The media you believe is original"
                                    file={referenceFile}
                                    preview={referencePreview}
                                    onFileChange={handleReferenceFileChange}
                                    disabled={isComparing}
                                />
                                <MediaUploadZone
                                    id="suspected-upload"
                                    label="Suspected Media"
                                    sublabel="The media you want to verify"
                                    file={suspectedFile}
                                    preview={suspectedPreview}
                                    onFileChange={handleSuspectedFileChange}
                                    disabled={isComparing}
                                />
                            </div>

                            {/* Analyze button */}
                            <button
                                onClick={handleCompareAnalyze}
                                disabled={!referenceFile || !suspectedFile || isComparing}
                                className="btn btn-primary"
                                style={{
                                    width: '100%', padding: '0.9rem',
                                    fontSize: '1rem', fontWeight: '700',
                                    opacity: (!referenceFile || !suspectedFile || isComparing) ? 0.5 : 1,
                                    cursor: (!referenceFile || !suspectedFile || isComparing) ? 'not-allowed' : 'pointer',
                                    display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '0.5rem',
                                }}
                            >
                                {isComparing ? (
                                    <>
                                        <span style={{ display: 'inline-block', width: '16px', height: '16px', border: '2px solid rgba(255,255,255,0.4)', borderTopColor: '#fff', borderRadius: '50%', animation: 'spin 0.8s linear infinite' }} />
                                        Analyzing both media...
                                    </>
                                ) : (
                                    <>⚖️ Analyze Both</>
                                )}
                            </button>
                        </div>

                        {/* Loading state */}
                        {isComparing && (
                            <div className="card animate-fade-in" style={{ marginTop: '1.5rem', padding: '1.5rem' }}>
                                <div style={{ display: 'flex', gap: '1.5rem', flexWrap: 'wrap' }}>
                                    {['Reference Media', 'Suspected Media'].map((label) => (
                                        <div key={label} style={{ flex: 1, minWidth: '200px' }}>
                                            <p style={{ fontSize: '0.8rem', fontWeight: '600', color: 'var(--text-secondary)', textTransform: 'uppercase', marginBottom: '0.5rem' }}>{label}</p>
                                            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', color: '#f59e0b', fontSize: '0.9rem' }}>
                                                <span>⏳</span> Processing...
                                            </div>
                                        </div>
                                    ))}
                                </div>
                            </div>
                        )}

                        {/* Error */}
                        {compareError && !isComparing && (
                            <div className="animate-fade-in" style={{ marginTop: '1.5rem', padding: '1rem', borderRadius: 'var(--radius-md)', backgroundColor: 'rgba(239,68,68,0.1)', border: '1px solid rgba(239,68,68,0.2)', color: 'var(--danger)', display: 'flex', gap: '0.75rem', alignItems: 'flex-start' }}>
                                <span>❌</span> {compareError}
                            </div>
                        )}

                        {/* Results */}
                        {renderCompareResults()}
                    </div>
                )}
            </main>

            <footer style={{ textAlign: 'center', padding: '3rem 0', color: 'var(--text-secondary)', fontSize: '0.9rem', marginTop: '4rem', borderTop: '1px solid rgba(255,255,255,0.05)' }}>
                <p>© {new Date().getFullYear()} TruthLens — AI-Powered Deepfake Detection & Digital Evidence Platform.</p>
                <p style={{ fontSize: '0.78rem', marginTop: '0.25rem', opacity: 0.6 }}>Built on DeepSafe Open Source.</p>
            </footer>
        </div>
    );
}

// ---------------------------------------------------------------------------
// App root (unchanged — routing, auth)
// ---------------------------------------------------------------------------
function App() {
    const [isAuthenticated, setIsAuthenticated] = useState(() => {
        return localStorage.getItem('token') !== null;
    });

    const handleLogin = (token) => {
        localStorage.setItem('token', token);
        setIsAuthenticated(true);
    };

    const handleLogout = () => {
        localStorage.clear();
        setIsAuthenticated(false);
    };

    return (
        <Router>
            <Routes>
                <Route path="/login" element={<Login onLogin={handleLogin} />} />
                <Route path="/register" element={<Register onLogin={handleLogin} />} />
                <Route
                    path="/"
                    element={
                        <ProtectedRoute isAuthenticated={isAuthenticated}>
                            <Dashboard onLogout={handleLogout} />
                        </ProtectedRoute>
                    }
                />
            </Routes>
        </Router>
    );
}

export default App;
