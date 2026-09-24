import React from 'react';
import { Link, useNavigate } from 'react-router-dom';
import {
  Shield, ArrowRight, Lock,
  Sparkles, Cpu, Fingerprint, Layers, Eye,
  ChevronRight
} from 'lucide-react';
import { useAuth } from '../context/AuthContext';

export default function LandingPage() {
  const { user } = useAuth();
  const navigate = useNavigate();

  return (
    <div style={{ minHeight: '100vh', background: '#F8FAFC', color: '#0F172A', display: 'flex', flexDirection: 'column' }}>
      
      {/* ── Top Navigation Bar ──────────────────────────────────────── */}
      <header style={{
        background: '#FFFFFF',
        borderBottom: '1px solid #E2E8F0',
        position: 'sticky',
        top: 0,
        zIndex: 50,
        padding: '0.85rem 1.5rem',
      }}>
        <div style={{
          maxWidth: 1140,
          margin: '0 auto',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
        }}>
          <Link to="/" style={{ display: 'flex', alignItems: 'center', gap: '0.6rem', textDecoration: 'none' }}>
            <div style={{
              width: 36,
              height: 36,
              background: '#2563EB',
              borderRadius: 8,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              boxShadow: '0 2px 6px rgba(37,99,235,0.25)',
            }}>
              <Shield size={20} color="#FFFFFF" strokeWidth={2.5} />
            </div>
            <div>
              <span style={{ fontSize: '1.2rem', fontWeight: 800, color: '#0F172A', letterSpacing: '-0.02em' }}>
                TruthLens
              </span>
              <span style={{ fontSize: '0.7rem', color: '#2563EB', fontWeight: 700, marginLeft: '6px', background: '#EFF6FF', padding: '2px 6px', borderRadius: 4 }}>
                RESEARCH
              </span>
            </div>
          </Link>

          <nav style={{ display: 'flex', alignItems: 'center', gap: '1.25rem' }}>
            {user ? (
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                <Link
                  to="/dashboard"
                  style={{
                    fontSize: '0.875rem',
                    fontWeight: 600,
                    color: '#475569',
                    textDecoration: 'none',
                    padding: '0.45rem 0.85rem',
                    borderRadius: 6,
                  }}
                >
                  Dashboard
                </Link>
                <Link
                  to="/analyze"
                  style={{
                    fontSize: '0.875rem',
                    fontWeight: 600,
                    color: '#FFFFFF',
                    background: '#2563EB',
                    textDecoration: 'none',
                    padding: '0.45rem 1rem',
                    borderRadius: 6,
                    display: 'inline-flex',
                    alignItems: 'center',
                    gap: '0.35rem',
                    boxShadow: '0 2px 4px rgba(37,99,235,0.2)',
                  }}
                >
                  New Analysis <ArrowRight size={15} />
                </Link>
              </div>
            ) : (
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                <Link
                  to="/login"
                  style={{
                    fontSize: '0.875rem',
                    fontWeight: 600,
                    color: '#475569',
                    textDecoration: 'none',
                    padding: '0.45rem 0.85rem',
                    borderRadius: 6,
                  }}
                >
                  Sign In
                </Link>
                <Link
                  to="/signup"
                  style={{
                    fontSize: '0.875rem',
                    fontWeight: 600,
                    color: '#FFFFFF',
                    background: '#2563EB',
                    textDecoration: 'none',
                    padding: '0.45rem 1rem',
                    borderRadius: 6,
                    display: 'inline-flex',
                    alignItems: 'center',
                    gap: '0.35rem',
                    boxShadow: '0 2px 4px rgba(37,99,235,0.2)',
                  }}
                >
                  Get Started <ChevronRight size={15} />
                </Link>
              </div>
            )}
          </nav>
        </div>
      </header>

      {/* ── Hero Section ───────────────────────────────────────────── */}
      <section style={{
        padding: '4rem 1.5rem 3.5rem',
        maxWidth: 1140,
        margin: '0 auto',
        width: '100%',
      }}>
        <div style={{ textAlign: 'center', maxWidth: 840, margin: '0 auto 3rem' }}>
          
          <div style={{
            display: 'inline-flex',
            alignItems: 'center',
            gap: '0.5rem',
            padding: '4px 12px',
            background: '#EFF6FF',
            border: '1px solid #BFDBFE',
            borderRadius: 9999,
            fontSize: '0.8125rem',
            fontWeight: 600,
            color: '#1D4ED8',
            marginBottom: '1.25rem',
          }}>
            <Sparkles size={14} />
            <span>AI-Powered Digital Evidence &amp; Deepfake Detection</span>
          </div>

          <h1 style={{
            fontSize: 'clamp(2rem, 4vw, 2.75rem)',
            fontWeight: 800,
            color: '#0F172A',
            lineHeight: 1.2,
            letterSpacing: '-0.03em',
            marginBottom: '1.25rem',
          }}>
            TruthLens: AI-Powered Deepfake Detection &amp; Digital Evidence Platform
          </h1>

          <p style={{
            fontSize: '1.1rem',
            lineHeight: 1.6,
            color: '#475569',
            maxWidth: 720,
            margin: '0 auto 2rem',
          }}>
            A rigorous, research-ready platform calibrated specifically for <strong>human facial image authenticity</strong>. Combines Vision Transformer neural inference, multi-signal pixel forensics, MTCNN biometric localization, and SHA-256 cryptographic chain of custody.
          </p>

          <div style={{ display: 'flex', justifyContent: 'center', gap: '1rem', flexWrap: 'wrap' }}>
            <button
              onClick={() => navigate(user ? '/analyze' : '/signup')}
              style={{
                fontSize: '1rem',
                fontWeight: 700,
                color: '#FFFFFF',
                background: '#2563EB',
                border: 'none',
                padding: '0.85rem 1.75rem',
                borderRadius: 8,
                cursor: 'pointer',
                display: 'inline-flex',
                alignItems: 'center',
                gap: '0.5rem',
                boxShadow: '0 4px 12px rgba(37,99,235,0.25)',
                transition: 'background 0.15s ease',
              }}
              onMouseOver={e => e.currentTarget.style.background = '#1D4ED8'}
              onMouseOut={e => e.currentTarget.style.background = '#2563EB'}
            >
              Analyze Media Now <ArrowRight size={18} />
            </button>

            <button
              onClick={() => navigate('/login')}
              style={{
                fontSize: '1rem',
                fontWeight: 600,
                color: '#334155',
                background: '#FFFFFF',
                border: '1px solid #CBD5E1',
                padding: '0.85rem 1.5rem',
                borderRadius: 8,
                cursor: 'pointer',
                display: 'inline-flex',
                alignItems: 'center',
                gap: '0.4rem',
              }}
              onMouseOver={e => e.currentTarget.style.background = '#F8FAFC'}
              onMouseOut={e => e.currentTarget.style.background = '#FFFFFF'}
            >
              <Lock size={16} /> Sign In to Workspace
            </button>
          </div>
        </div>

        {/* ── Key Feature Cards ──────────────────────────────────────── */}
        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(260px, 1fr))',
          gap: '1.25rem',
          marginTop: '1.5rem',
        }}>
          
          {/* Card 1 */}
          <div style={{
            background: '#FFFFFF',
            border: '1px solid #E2E8F0',
            borderRadius: 12,
            padding: '1.5rem',
            boxShadow: '0 1px 3px rgba(15,23,42,0.04)',
          }}>
            <div style={{
              width: 40,
              height: 40,
              background: '#EFF6FF',
              borderRadius: 8,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              marginBottom: '1rem',
              color: '#2563EB',
            }}>
              <Cpu size={22} />
            </div>
            <h3 style={{ fontSize: '1.05rem', fontWeight: 700, color: '#0F172A', marginBottom: '0.4rem' }}>
              Vision Transformer AI
            </h3>
            <p style={{ fontSize: '0.875rem', color: '#64748B', lineHeight: 1.5, margin: 0 }}>
              Evaluates visual and semantic artifacts using fine-tuned Vision Transformer architecture (<code>dima806/deepfake_vs_real_image_detection</code>) for calibrated probabilistic assessments.
            </p>
          </div>

          {/* Card 2 */}
          <div style={{
            background: '#FFFFFF',
            border: '1px solid #E2E8F0',
            borderRadius: 12,
            padding: '1.5rem',
            boxShadow: '0 1px 3px rgba(15,23,42,0.04)',
          }}>
            <div style={{
              width: 40,
              height: 40,
              background: '#F0FDF4',
              borderRadius: 8,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              marginBottom: '1rem',
              color: '#16A34A',
            }}>
              <Eye size={22} />
            </div>
            <h3 style={{ fontSize: '1.05rem', fontWeight: 700, color: '#0F172A', marginBottom: '0.4rem' }}>
              Human Face Localization
            </h3>
            <p style={{ fontSize: '0.875rem', color: '#64748B', lineHeight: 1.5, margin: 0 }}>
              MTCNN multi-task neural face detector pinpoints facial bounding boxes and confirms biometric context so non-facial media is never mischaracterized as deepfake evidence.
            </p>
          </div>

          {/* Card 3 */}
          <div style={{
            background: '#FFFFFF',
            border: '1px solid #E2E8F0',
            borderRadius: 12,
            padding: '1.5rem',
            boxShadow: '0 1px 3px rgba(15,23,42,0.04)',
          }}>
            <div style={{
              width: 40,
              height: 40,
              background: '#FFFBEB',
              borderRadius: 8,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              marginBottom: '1rem',
              color: '#D97706',
            }}>
              <Layers size={22} />
            </div>
            <h3 style={{ fontSize: '1.05rem', fontWeight: 700, color: '#0F172A', marginBottom: '0.4rem' }}>
              Multi-Signal Forensics
            </h3>
            <p style={{ fontSize: '0.875rem', color: '#64748B', lineHeight: 1.5, margin: 0 }}>
              Extracts objective physical indicators including Error Level Analysis (ELA), 2D Fourier spectral high-frequency decay ratios, and sensor noise residual variance.
            </p>
          </div>

          {/* Card 4 */}
          <div style={{
            background: '#FFFFFF',
            border: '1px solid #E2E8F0',
            borderRadius: 12,
            padding: '1.5rem',
            boxShadow: '0 1px 3px rgba(15,23,42,0.04)',
          }}>
            <div style={{
              width: 40,
              height: 40,
              background: '#F5F3FF',
              borderRadius: 8,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              marginBottom: '1rem',
              color: '#7C3AED',
            }}>
              <Fingerprint size={22} />
            </div>
            <h3 style={{ fontSize: '1.05rem', fontWeight: 700, color: '#0F172A', marginBottom: '0.4rem' }}>
              SHA-256 Digital Fingerprint
            </h3>
            <p style={{ fontSize: '0.875rem', color: '#64748B', lineHeight: 1.5, margin: 0 }}>
              Computes cryptographic SHA-256 hash digests directly on raw uploaded file bytes to guarantee chain-of-custody verification across reports and case file packages.
            </p>
          </div>

        </div>
      </section>

      {/* ── Architecture & Pipeline Section ────────────────────────── */}
      <section style={{
        background: '#FFFFFF',
        borderTop: '1px solid #E2E8F0',
        borderBottom: '1px solid #E2E8F0',
        padding: '3.5rem 1.5rem',
      }}>
        <div style={{ maxWidth: 1140, margin: '0 auto' }}>
          
          <div style={{ textAlign: 'center', marginBottom: '2.5rem' }}>
            <span style={{ fontSize: '0.75rem', fontWeight: 700, color: '#2563EB', textTransform: 'uppercase', letterSpacing: '0.08em' }}>
              Target Architecture
            </span>
            <h2 style={{ fontSize: '1.75rem', fontWeight: 800, color: '#0F172A', marginTop: '0.35rem' }}>
              End-to-End Verifiable Analysis Pipeline
            </h2>
            <p style={{ fontSize: '0.95rem', color: '#64748B', maxWidth: 640, margin: '0.5rem auto 0' }}>
              Every uploaded media file undergoes structured validation, biometric screening, neural inference, and cryptographic documentation.
            </p>
          </div>

          <div style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))',
            gap: '1rem',
          }}>
            {[
              { step: '01', title: 'Upload & Validation', desc: 'Strict MIME & format checking, corruption rejection, and raw SHA-256 digest computation.' },
              { step: '02', title: 'Face Localization', desc: 'MTCNN detects human facial boundaries and asserts human-image screening context.' },
              { step: '03', title: 'ViT Neural Inference', desc: 'Cached Vision Transformer generates authentic and AI-generated probabilities.' },
              { step: '04', title: 'Forensic Extraction', desc: 'Supporting optical characteristics, ELA compression profiles, and spectral ratios.' },
              { step: '05', title: 'Verifiable Evidence', desc: 'Export research-grade PDF reports or manually generate portable ZIP case packages.' },
            ].map(item => (
              <div
                key={item.step}
                style={{
                  background: '#F8FAFC',
                  border: '1px solid #E2E8F0',
                  borderRadius: 10,
                  padding: '1.25rem',
                }}
              >
                <div style={{ fontSize: '0.75rem', fontWeight: 800, color: '#2563EB', fontFamily: 'var(--font-mono)', marginBottom: '0.5rem' }}>
                  STEP {item.step}
                </div>
                <h4 style={{ fontSize: '0.95rem', fontWeight: 700, color: '#0F172A', marginBottom: '0.35rem' }}>
                  {item.title}
                </h4>
                <p style={{ fontSize: '0.8125rem', color: '#64748B', lineHeight: 1.5, margin: 0 }}>
                  {item.desc}
                </p>
              </div>
            ))}
          </div>

        </div>
      </section>

      {/* ── Footer ─────────────────────────────────────────────────── */}
      <footer style={{
        marginTop: 'auto',
        background: '#F8FAFC',
        borderTop: '1px solid #E2E8F0',
        padding: '2.5rem 1.5rem',
      }}>
        <div style={{
          maxWidth: 1140,
          margin: '0 auto',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          flexWrap: 'wrap',
          gap: '1rem',
        }}>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.35rem' }}>
              <Shield size={18} color="#2563EB" />
              <span style={{ fontSize: '0.95rem', fontWeight: 800, color: '#0F172A' }}>TruthLens</span>
            </div>
            <p style={{ fontSize: '0.8125rem', color: '#64748B', margin: 0 }}>
              AI-Powered Deepfake Detection and Digital Evidence Platform · Final Year Project
            </p>
          </div>

          <div style={{ textAlign: 'right', fontSize: '0.8125rem', color: '#94A3B8', maxWidth: 480 }}>
            AI-based image detection provides a probabilistic assessment and should not be treated as conclusive proof of authenticity or manipulation.
          </div>
        </div>
      </footer>

    </div>
  );
}
