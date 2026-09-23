import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Scan, Cpu, Search, Users,
  FileText, CheckCircle2, AlertTriangle, HelpCircle,
  Sparkles, Layers, Image as ImageIcon
} from 'lucide-react';
import { useAuth } from '../context/AuthContext';

export default function DashboardPage() {
  const navigate = useNavigate();
  const { user, userProfile } = useAuth();
  const firstName = userProfile?.name?.split(' ')[0] || user?.displayName?.split(' ')[0] || '';

  const [activeStep, setActiveStep] = useState(0);

  // Auto-cycle through the 6 explanation steps every 4 seconds
  useEffect(() => {
    const timer = setInterval(() => {
      setActiveStep(prev => (prev + 1) % 6);
    }, 4000);
    return () => clearInterval(timer);
  }, []);

  const scrollToHowItWorks = () => {
    const el = document.getElementById('how-it-works');
    if (el) {
      el.scrollIntoView({ behavior: 'smooth' });
    }
  };

  const steps = [
    {
      num: '01',
      title: 'Upload Media',
      desc: 'Upload an image or supported media file to begin the evaluation process.',
      badge: 'Input Stage',
      visual: (
        <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', height: 110, background: '#F8FAFC', borderRadius: 10, border: '2px dashed #CBD5E1', padding: '0.75rem' }}>
          <div style={{ width: 36, height: 36, borderRadius: '50%', background: '#EFF6FF', display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#2563EB', marginBottom: '0.35rem' }}>
            <ImageIcon size={18} />
          </div>
          <span style={{ fontSize: '0.75rem', fontWeight: 600, color: '#334155' }}>Select or Drag Media</span>
          <span style={{ fontSize: '0.65rem', color: '#94A3B8' }}>JPEG, PNG, WebP, WAV</span>
        </div>
      )
    },
    {
      num: '02',
      title: 'Prepare',
      desc: 'The uploaded media is prepared and normalized for structured multi-modal analysis.',
      badge: 'Pre-Processing',
      visual: (
        <div style={{ display: 'flex', flexDirection: 'column', justifyContent: 'center', height: 110, background: '#F8FAFC', borderRadius: 10, border: '1px solid #E2E8F0', padding: '0.75rem 1rem' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.4rem' }}>
            <span style={{ fontSize: '0.7rem', fontWeight: 600, color: '#64748B' }}>SHA-256 Hashing</span>
            <CheckCircle2 size={13} color="#16A34A" />
          </div>
          <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.4rem' }}>
            <span style={{ fontSize: '0.7rem', fontWeight: 600, color: '#64748B' }}>Dimension Normalization</span>
            <CheckCircle2 size={13} color="#16A34A" />
          </div>
          <div style={{ display: 'flex', justifyContent: 'space-between' }}>
            <span style={{ fontSize: '0.7rem', fontWeight: 600, color: '#64748B' }}>Noise Profile Extraction</span>
            <CheckCircle2 size={13} color="#16A34A" />
          </div>
        </div>
      )
    },
    {
      num: '03',
      title: 'AI Detection',
      desc: 'The AI model analyzes visual patterns and generative artifacts associated with AI synthesis.',
      badge: 'Neural Inference',
      visual: (
        <div style={{ position: 'relative', height: 110, background: '#0F172A', borderRadius: 10, overflow: 'hidden', padding: '0.75rem', display: 'flex', flexDirection: 'column', justifyContent: 'space-between' }}>
          <div className="hero-scan-line" />
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <span style={{ fontSize: '0.7rem', fontWeight: 700, color: '#93C5FD', letterSpacing: '0.05em' }}>FREQUENCY SCAN</span>
            <span style={{ fontSize: '0.65rem', background: 'rgba(37,99,235,0.3)', color: '#BFDBFE', padding: '1px 6px', borderRadius: 4 }}>ACTIVE</span>
          </div>
          <div style={{ display: 'flex', gap: '0.35rem', flexWrap: 'wrap' }}>
            <span style={{ fontSize: '0.65rem', background: 'rgba(255,255,255,0.1)', color: '#F8FAFC', padding: '2px 6px', borderRadius: 4 }}>Upsampling Clues</span>
            <span style={{ fontSize: '0.65rem', background: 'rgba(255,255,255,0.1)', color: '#F8FAFC', padding: '2px 6px', borderRadius: 4 }}>CLIP Embeddings</span>
          </div>
        </div>
      )
    },
    {
      num: '04',
      title: 'Forensic Analysis',
      desc: 'Supporting image characteristics and pixel-level forensic indicators are examined.',
      badge: 'Signal Fusion',
      visual: (
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.4rem', height: 110 }}>
          <div style={{ background: '#EFF6FF', borderRadius: 8, padding: '0.5rem', display: 'flex', flexDirection: 'column', justifyContent: 'center' }}>
            <span style={{ fontSize: '0.65rem', color: '#64748B', fontWeight: 600 }}>Pixel Noise</span>
            <span style={{ fontSize: '0.75rem', color: '#1E40AF', fontWeight: 700 }}>Variance Check</span>
          </div>
          <div style={{ background: '#EFF6FF', borderRadius: 8, padding: '0.5rem', display: 'flex', flexDirection: 'column', justifyContent: 'center' }}>
            <span style={{ fontSize: '0.65rem', color: '#64748B', fontWeight: 600 }}>Resolution</span>
            <span style={{ fontSize: '0.75rem', color: '#1E40AF', fontWeight: 700 }}>2D FFT Spectral</span>
          </div>
          <div style={{ background: '#EFF6FF', borderRadius: 8, padding: '0.5rem', display: 'flex', flexDirection: 'column', justifyContent: 'center' }}>
            <span style={{ fontSize: '0.65rem', color: '#64748B', fontWeight: 600 }}>Brightness</span>
            <span style={{ fontSize: '0.75rem', color: '#1E40AF', fontWeight: 700 }}>LBP Texture</span>
          </div>
          <div style={{ background: '#EFF6FF', borderRadius: 8, padding: '0.5rem', display: 'flex', flexDirection: 'column', justifyContent: 'center' }}>
            <span style={{ fontSize: '0.65rem', color: '#64748B', fontWeight: 600 }}>Contrast</span>
            <span style={{ fontSize: '0.75rem', color: '#1E40AF', fontWeight: 700 }}>Edge Gradient</span>
          </div>
        </div>
      )
    },
    {
      num: '05',
      title: 'Face Verification',
      desc: 'When applicable, facial landmarks in two images are compared for biometric similarity.',
      badge: 'Identity Check',
      visual: (
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-around', height: 110, background: '#F8FAFC', borderRadius: 10, border: '1px solid #E2E8F0', padding: '0.5rem' }}>
          <div style={{ textAlign: 'center' }}>
            <div style={{ width: 32, height: 32, borderRadius: '50%', background: '#DBEAFE', display: 'inline-flex', alignItems: 'center', justifyContent: 'center', color: '#2563EB', marginBottom: 2 }}>
              <Users size={16} />
            </div>
            <div style={{ fontSize: '0.65rem', fontWeight: 600, color: '#64748B' }}>Reference</div>
          </div>
          <div style={{ fontSize: '0.75rem', fontWeight: 800, color: '#2563EB', background: '#EFF6FF', padding: '4px 8px', borderRadius: 6 }}>
            Cosine Match
          </div>
          <div style={{ textAlign: 'center' }}>
            <div style={{ width: 32, height: 32, borderRadius: '50%', background: '#DBEAFE', display: 'inline-flex', alignItems: 'center', justifyContent: 'center', color: '#2563EB', marginBottom: 2 }}>
              <Users size={16} />
            </div>
            <div style={{ fontSize: '0.65rem', fontWeight: 600, color: '#64748B' }}>Suspected</div>
          </div>
        </div>
      )
    },
    {
      num: '06',
      title: 'Final Assessment',
      desc: 'All available evidence signals are combined to provide an understandable assessment.',
      badge: 'Decision Engine',
      visual: (
        <div style={{ display: 'flex', flexDirection: 'column', justifyContent: 'space-around', height: 110, background: '#F8FAFC', borderRadius: 10, border: '1px solid #E2E8F0', padding: '0.5rem 0.75rem' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', fontSize: '0.7rem', fontWeight: 700, color: '#16A34A' }}>
            <CheckCircle2 size={13} /> Likely Real
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', fontSize: '0.7rem', fontWeight: 700, color: '#DC2626' }}>
            <AlertTriangle size={13} /> Likely AI-Generated
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', fontSize: '0.7rem', fontWeight: 700, color: '#D97706' }}>
            <HelpCircle size={13} /> Inconclusive
          </div>
        </div>
      )
    }
  ];

  const capabilities = [
    {
      icon: <Cpu size={22} color="#2563EB" />,
      title: 'AI Detection',
      desc: 'Analyze visual patterns to identify potential AI-generated content.'
    },
    {
      icon: <Search size={22} color="#2563EB" />,
      title: 'Forensic Analysis',
      desc: 'Review supporting image characteristics and forensic indicators.'
    },
    {
      icon: <Users size={22} color="#2563EB" />,
      title: 'Face Verification',
      desc: 'Compare faces between images when applicable.'
    },
    {
      icon: <FileText size={22} color="#2563EB" />,
      title: 'Digital Reports',
      desc: 'Generate structured analysis reports from completed cases.'
    }
  ];

  const whyPoints = [
    {
      title: 'Unified Analysis',
      desc: 'Multiple analysis capabilities — neural AI detection, pixel forensics, and face verification — unified in one reliable platform.'
    },
    {
      title: 'Understandable Results',
      desc: 'Results are presented in a simple, transparent format with clear risk tiers, confidence scores, and plain-language explanations.'
    },
    {
      title: 'Digital Evidence Support',
      desc: 'Analysis information can be exported into formal forensic PDF reports and structured digital case file archives.'
    }
  ];

  return (
    <div className="fade-in" style={{ maxWidth: 1080, margin: '0 auto', paddingBottom: '3rem' }}>

      {/* ── 1. HERO SECTION ─────────────────────────────────── */}
      <section style={{
        background: 'linear-gradient(135deg, #FFFFFF 0%, #F8FAFC 100%)',
        border: '1px solid #E2E8F0',
        borderRadius: 24,
        padding: '3rem 2.5rem',
        marginBottom: '3rem',
        boxShadow: '0 4px 20px -2px rgba(15, 23, 42, 0.05)',
      }}>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: '2.5rem', alignItems: 'center' }}>
          
          {/* Left Column: Headline & Action */}
          <div>
            <div style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: '0.4rem',
              background: '#EFF6FF',
              color: '#2563EB',
              fontSize: '0.8125rem',
              fontWeight: 700,
              padding: '0.35rem 0.85rem',
              borderRadius: 9999,
              marginBottom: '1rem',
              letterSpacing: '0.02em'
            }}>
              <Sparkles size={14} /> {firstName ? `Welcome, ${firstName} · See Beyond the Image.` : 'See Beyond the Image.'}
            </div>

            <h1 style={{
              fontSize: 'clamp(2rem, 3.8vw, 2.75rem)',
              fontWeight: 800,
              color: '#0F172A',
              lineHeight: 1.15,
              marginBottom: '1rem',
              letterSpacing: '-0.03em'
            }}>
              AI-Powered Digital Media Analysis
            </h1>

            <p style={{
              fontSize: '1.0625rem',
              color: '#64748B',
              lineHeight: 1.6,
              marginBottom: '2rem',
              maxWidth: 520
            }}>
              TruthLens helps analyze digital images for signs of AI generation and manipulation using AI-based detection and supporting forensic analysis.
            </p>

            <div style={{ display: 'flex', gap: '0.875rem', flexWrap: 'wrap' }}>
              <button
                onClick={() => navigate('/analyze')}
                className="btn btn-primary btn-lg"
                id="hero-start-analysis-btn"
                style={{ display: 'inline-flex', alignItems: 'center', gap: '0.5rem', fontSize: '0.9375rem' }}
              >
                <Scan size={18} /> Start New Analysis
              </button>

              <button
                onClick={scrollToHowItWorks}
                className="btn btn-secondary btn-lg"
                id="hero-learn-how-btn"
                style={{ fontSize: '0.9375rem' }}
              >
                Learn How It Works
              </button>
            </div>
          </div>

          {/* Right Column: Subtle Animated Visual Simulation */}
          <div className="hero-float-card" style={{
            background: '#FFFFFF',
            border: '1px solid #CBD5E1',
            borderRadius: 18,
            padding: '1.5rem',
            boxShadow: '0 20px 35px -10px rgba(15, 23, 42, 0.08), 0 1px 3px rgba(15, 23, 42, 0.05)',
            position: 'relative'
          }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '1rem' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                <div style={{ width: 10, height: 10, borderRadius: '50%', background: '#16A34A' }} />
                <span style={{ fontSize: '0.8125rem', fontWeight: 700, color: '#0F172A' }}>Live Forensic Inspection</span>
              </div>
              <span style={{ fontSize: '0.75rem', color: '#64748B', fontFamily: 'var(--font-mono)' }}>TL-SAMPLE-01</span>
            </div>

            {/* Media Simulation Frame with Scan Line */}
            <div style={{
              height: 170,
              background: 'linear-gradient(180deg, #1E293B 0%, #0F172A 100%)',
              borderRadius: 12,
              position: 'relative',
              overflow: 'hidden',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              marginBottom: '1rem'
            }}>
              <div className="hero-scan-line" />
              
              {/* Center Wireframe / Illustration */}
              <div style={{ textAlign: 'center', zIndex: 1 }}>
                <Layers size={42} color="#60A5FA" style={{ opacity: 0.85, marginBottom: '0.35rem' }} />
                <div style={{ fontSize: '0.75rem', fontWeight: 600, color: '#93C5FD', letterSpacing: '0.04em' }}>
                  MULTI-SIGNAL WAVEFORM
                </div>
              </div>
            </div>

            {/* Real-time Indicator Chips */}
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', fontSize: '0.8125rem', background: '#F8FAFC', padding: '0.45rem 0.75rem', borderRadius: 8, border: '1px solid #E2E8F0' }}>
                <span style={{ color: '#64748B', fontWeight: 500 }}>AI Detection Signal</span>
                <span style={{ color: '#2563EB', fontWeight: 700 }}>Resampling Analysis</span>
              </div>

              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', fontSize: '0.8125rem', background: '#F8FAFC', padding: '0.45rem 0.75rem', borderRadius: 8, border: '1px solid #E2E8F0' }}>
                <span style={{ color: '#64748B', fontWeight: 500 }}>Pixel Forensic Status</span>
                <span style={{ color: '#16A34A', fontWeight: 700 }}>Evaluated</span>
              </div>
            </div>
          </div>

        </div>
      </section>


      {/* ── 2. WHAT IS TRUTHLENS? SECTION ──────────────────── */}
      <section style={{
        background: '#FFFFFF',
        border: '1px solid #E2E8F0',
        borderRadius: 20,
        padding: '2.5rem 2rem',
        marginBottom: '3rem',
        boxShadow: 'var(--shadow-sm)',
        textAlign: 'center'
      }}>
        <div style={{ maxWidth: 720, margin: '0 auto' }}>
          <h2 style={{ fontSize: '1.625rem', fontWeight: 800, color: '#0F172A', marginBottom: '0.75rem', letterSpacing: '-0.02em' }}>
            What is TruthLens?
          </h2>
          <p style={{ fontSize: '1.0625rem', color: '#334155', lineHeight: 1.6, marginBottom: '0.75rem', fontWeight: 500 }}>
            TruthLens is an AI-powered digital media analysis platform designed to help identify potentially real, manipulated, or AI-generated images.
          </p>
          <p style={{ fontSize: '0.9375rem', color: '#64748B', lineHeight: 1.6 }}>
            It combines AI-based detection with supporting image and forensic analysis to provide an understandable assessment of digital media.
          </p>
        </div>
      </section>


      {/* ── 3. HOW TRUTHLENS WORKS (6 STEPS) ───────────────── */}
      <section id="how-it-works" style={{ marginBottom: '3rem' }}>
        <div style={{ textAlign: 'center', marginBottom: '2rem' }}>
          <div style={{ fontSize: '0.8125rem', fontWeight: 700, color: '#2563EB', textTransform: 'uppercase', letterSpacing: '0.06em', marginBottom: '0.35rem' }}>
            Methodology
          </div>
          <h2 style={{ fontSize: '1.75rem', fontWeight: 800, color: '#0F172A', letterSpacing: '-0.02em' }}>
            How TruthLens Works
          </h2>
          <p style={{ fontSize: '0.9375rem', color: '#64748B', maxWidth: 560, margin: '0.4rem auto 0' }}>
            An automated, step-by-step pipeline designed for clarity and forensic diligence.
          </p>
        </div>

        {/* 6 Step Grid */}
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: '1.25rem' }}>
          {steps.map((s, idx) => (
            <div
              key={s.num}
              className="step-card"
              onClick={() => setActiveStep(idx)}
              style={{
                borderColor: activeStep === idx ? '#2563EB' : '#E2E8F0',
                background: activeStep === idx ? '#FFFFFF' : '#FFFFFF',
                boxShadow: activeStep === idx ? '0 10px 25px -5px rgba(37, 99, 235, 0.1)' : 'var(--shadow-sm)'
              }}
            >
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.75rem' }}>
                <span style={{ fontSize: '1.25rem', fontWeight: 800, color: activeStep === idx ? '#2563EB' : '#94A3B8', fontFamily: 'var(--font-mono)' }}>
                  {s.num}
                </span>
                <span style={{ fontSize: '0.7rem', fontWeight: 700, background: activeStep === idx ? '#EFF6FF' : '#F1F5F9', color: activeStep === idx ? '#2563EB' : '#64748B', padding: '3px 8px', borderRadius: 6 }}>
                  {s.badge}
                </span>
              </div>

              <h3 style={{ fontSize: '1.0625rem', fontWeight: 700, color: '#0F172A', marginBottom: '0.35rem' }}>
                {s.title}
              </h3>
              
              <p style={{ fontSize: '0.875rem', color: '#64748B', lineHeight: 1.5, marginBottom: '1rem', minHeight: 40 }}>
                {s.desc}
              </p>

              {s.visual}
            </div>
          ))}
        </div>
      </section>


      {/* ── 4. CORE CAPABILITIES (4 CARDS ONLY) ─────────────── */}
      <section style={{ marginBottom: '3rem' }}>
        <div style={{ textAlign: 'center', marginBottom: '2rem' }}>
          <div style={{ fontSize: '0.8125rem', fontWeight: 700, color: '#2563EB', textTransform: 'uppercase', letterSpacing: '0.06em', marginBottom: '0.35rem' }}>
            Features
          </div>
          <h2 style={{ fontSize: '1.75rem', fontWeight: 800, color: '#0F172A', letterSpacing: '-0.02em' }}>
            Core Capabilities
          </h2>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', gap: '1.25rem' }}>
          {capabilities.map(c => (
            <div key={c.title} className="capability-card">
              <div style={{ width: 44, height: 44, borderRadius: 12, background: '#EFF6FF', display: 'flex', alignItems: 'center', justifyContent: 'center', marginBottom: '1.25rem' }}>
                {c.icon}
              </div>
              <h3 style={{ fontSize: '1.0625rem', fontWeight: 700, color: '#0F172A', marginBottom: '0.5rem' }}>
                {c.title}
              </h3>
              <p style={{ fontSize: '0.875rem', color: '#64748B', lineHeight: 1.55, margin: 0 }}>
                {c.desc}
              </p>
            </div>
          ))}
        </div>
      </section>


      {/* ── 5. COMPACT PROCESS VISUAL ───────────────────────── */}
      <section style={{
        background: '#FFFFFF',
        border: '1px solid #E2E8F0',
        borderRadius: 20,
        padding: '2.5rem 2rem',
        marginBottom: '3rem',
        boxShadow: 'var(--shadow-sm)',
        textAlign: 'center'
      }}>
        <div style={{ fontSize: '0.8125rem', fontWeight: 700, color: '#2563EB', textTransform: 'uppercase', letterSpacing: '0.06em', marginBottom: '0.5rem' }}>
          Simple 3-Step Process
        </div>
        
        <div style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          gap: '1rem',
          flexWrap: 'wrap',
          fontSize: '1.125rem',
          fontWeight: 800,
          color: '#0F172A',
          letterSpacing: '0.02em',
          marginBottom: '1rem'
        }}>
          <span>UPLOAD</span>
          <span style={{ color: '#2563EB' }}>→</span>
          <span>ANALYZE</span>
          <span style={{ color: '#2563EB' }}>→</span>
          <span>REVIEW</span>
        </div>

        <p style={{ fontSize: '0.9375rem', color: '#64748B', lineHeight: 1.6, maxWidth: 500, margin: '0 auto' }}>
          Upload your media &nbsp;↓&nbsp; TruthLens analyzes it &nbsp;↓&nbsp; Review the assessment and evidence.
        </p>
      </section>


      {/* ── 6. WHY TRUTHLENS? SECTION (3 POINTS) ─────────────── */}
      <section style={{ marginBottom: '3.5rem' }}>
        <div style={{ textAlign: 'center', marginBottom: '2rem' }}>
          <h2 style={{ fontSize: '1.75rem', fontWeight: 800, color: '#0F172A', letterSpacing: '-0.02em' }}>
            Why TruthLens?
          </h2>
          <p style={{ fontSize: '0.9375rem', color: '#64748B', margin: '0.4rem 0 0' }}>
            Designed for investigative rigor, privacy, and actionable transparency.
          </p>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '1.25rem' }}>
          {whyPoints.map(p => (
            <div key={p.title} className="why-card">
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.6rem' }}>
                <CheckCircle2 size={18} color="#16A34A" />
                <h3 style={{ fontSize: '1rem', fontWeight: 700, color: '#0F172A', margin: 0 }}>
                  {p.title}
                </h3>
              </div>
              <p style={{ fontSize: '0.875rem', color: '#64748B', lineHeight: 1.55, margin: 0 }}>
                {p.desc}
              </p>
            </div>
          ))}
        </div>
      </section>


      {/* ── 7. INFORMATIONAL SECTION (BOTTOM) ────────────────── */}
      <section style={{
        background: '#EFF6FF',
        border: '1px solid #BFDBFE',
        borderRadius: 20,
        padding: '2.5rem 2rem',
        textAlign: 'center',
        color: '#1E40AF',
        marginBottom: '2.5rem',
      }}>
        <h2 style={{ fontSize: '1.25rem', fontWeight: 800, color: '#1E40AF', marginBottom: '0.5rem', letterSpacing: '-0.02em' }}>
          Learn more about how TruthLens analyzes digital media.
        </h2>
        <p style={{ fontSize: '0.9375rem', color: '#2563EB', maxWidth: 540, margin: '0 auto', lineHeight: 1.55 }}>
          Our multi-signal pipeline combines neural network feature analysis, pixel-level resampling forensics, and facial verification for comprehensive digital evidence evaluation.
        </p>
      </section>


      {/* ── 8. DISCLAIMER & FOOTER ──────────────────────────── */}
      <div style={{
        background: '#F1F5F9',
        border: '1px solid #E2E8F0',
        borderRadius: 12,
        padding: '1rem 1.25rem',
        fontSize: '0.8125rem',
        color: '#64748B',
        textAlign: 'center',
        marginBottom: '2rem',
        lineHeight: 1.5
      }}>
        TruthLens provides AI-assisted digital media analysis. Results may contain errors and should be independently reviewed.
      </div>

      <footer style={{
        textAlign: 'center',
        fontSize: '0.8125rem',
        color: '#94A3B8',
        paddingTop: '1rem',
        borderTop: '1px solid #E2E8F0'
      }}>
        <p style={{ fontWeight: 600, color: '#64748B', marginBottom: '0.25rem' }}>
          TruthLens
        </p>
        <p style={{ margin: '0 0 0.25rem 0' }}>
          AI-Powered Deepfake Detection &amp; Digital Evidence Platform
        </p>
        <p style={{ margin: 0 }}>
          TruthLens &copy; 2026
        </p>
      </footer>

    </div>
  );
}
