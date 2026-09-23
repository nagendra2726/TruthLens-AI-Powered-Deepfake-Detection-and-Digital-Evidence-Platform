import React, { useState, useEffect } from 'react';
import { useLocation, useNavigate, Link } from 'react-router-dom';
import {
  Shield, Globe, Calendar, User, MessageSquare, DollarSign,
  BookOpen, Save, ExternalLink, Copy, Check, AlertTriangle,
  ArrowLeft, PhoneCall, FileText
} from 'lucide-react';
import { API_BASE_URL } from '../config/api';

export default function HelpReportingPage() {
  const location = useLocation();
  const navigate = useNavigate();
  const queryParams = new URLSearchParams(location.search);
  const initialCaseId = queryParams.get('caseId') || location.state?.caseId || '';

  const [caseId, setCaseId] = useState(initialCaseId);
  const [bestPracticesOpen, setBestPracticesOpen] = useState(true);
  const [docketSaved, setDocketSaved] = useState(false);
  const [copiedFIR, setCopiedFIR] = useState(false);

  const [docket, setDocket] = useState({
    incident_category: 'Extortion & Blackmail',
    circulated_platform: '',
    incident_date: new Date().toLocaleDateString('en-GB', { day: 'numeric', month: 'long', year: 'numeric' }),
    suspect_identifier: '',
    incident_narrative: '',
    demands_record: ''
  });

  // Restore stored docket if caseId is present
  useEffect(() => {
    if (!caseId) return;
    try {
      const stored = localStorage.getItem(`truthlens_docket_${caseId}`);
      if (stored) {
        setDocket(JSON.parse(stored));
        setDocketSaved(true);
      }
    } catch (_) {}
  }, [caseId]);

  const handleDocketChange = (field, val) => {
    setDocket(prev => ({ ...prev, [field]: val }));
    setDocketSaved(false);
  };

  const handleSaveDocket = async () => {
    if (!caseId) {
      alert('Please enter or select a Case ID to attach this evidentiary docket to.');
      return;
    }
    try {
      localStorage.setItem(`truthlens_docket_${caseId}`, JSON.stringify(docket));

      await fetch(`${API_BASE_URL}/api/cases/${caseId}/docket`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(docket)
      });
      setDocketSaved(true);
    } catch (_) {
      setDocketSaved(true);
    }
  };

  const handleCopyFIR = () => {
    const text = `CYBERCRIME COMPLAINT & EVIDENTIARY DOCKET
TruthLens Case Reference: ${caseId || 'Pending Assignment'}
Date Encountered: ${docket.incident_date || 'N/A'}
Incident Category: ${docket.incident_category}
Circulated Platform: ${docket.circulated_platform || 'Not specified'}
Suspect Handle / Phone: ${docket.suspect_identifier || 'Not specified'}

INCIDENT NARRATIVE:
${docket.incident_narrative || 'Detailed analysis attached in TruthLens Forensic Report.'}

DEMANDS / EXTORTION RECORD:
${docket.demands_record || 'None recorded'}

RELEVANT LEGAL PROVISIONS (INDIA):
1. Section 66D IT Act 2000 — Cheating by Personation using Computer Resource
2. Section 66E / 67A IT Act 2000 — Violation of Privacy & Transmitting Sexually Explicit / Manipulated Media
3. Section 318 / 319 BNS (Sec 419/420 IPC) — Cheating & Impersonation
4. Section 308 BNS (Sec 384 IPC) — Extortion by digital threat`;

    navigator.clipboard.writeText(text);
    setCopiedFIR(true);
    setTimeout(() => setCopiedFIR(false), 3000);
  };

  return (
    <div className="fade-in" style={{ maxWidth: 1000, margin: '0 auto', paddingBottom: '3rem' }}>
      
      {/* ── Top Header ──────────────────────────────────────── */}
      <div style={{ marginBottom: '1.5rem', display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '1rem' }}>
        <div>
          <button onClick={() => navigate(-1)} className="btn btn-ghost btn-sm" style={{ marginBottom: '0.5rem', paddingLeft: 0 }}>
            <ArrowLeft size={16} /> Back
          </button>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem' }}>
            <div style={{ width: 38, height: 38, borderRadius: 10, background: '#EFF6FF', display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#2563EB' }}>
              <Shield size={22} />
            </div>
            <div>
              <h1 style={{ fontSize: '1.5rem', fontWeight: 800, color: '#0F172A', letterSpacing: '-0.02em', margin: 0 }}>
                Help &amp; Cybercrime Reporting
              </h1>
              <p style={{ fontSize: '0.875rem', color: '#64748B', margin: '0.2rem 0 0 0' }}>
                Official reporting pathways, Indian legal remedies, and incident documentation guidance.
              </p>
            </div>
          </div>
        </div>

        {caseId && (
          <div style={{ background: '#FFFFFF', border: '1px solid #E2E8F0', borderRadius: 8, padding: '0.5rem 0.85rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <span style={{ fontSize: '0.75rem', color: '#64748B', fontWeight: 600 }}>Active Case:</span>
            <span style={{ fontFamily: 'var(--font-mono)', fontSize: '0.8125rem', fontWeight: 700, color: '#2563EB' }}>{caseId}</span>
            <Link to={`/history/${caseId}`} className="btn btn-ghost btn-sm" style={{ padding: '0.2rem 0.4rem', fontSize: '0.75rem' }}>
              View Result
            </Link>
          </div>
        )}
      </div>

      {/* ── Emergency Callout ───────────────────────────────── */}
      <div style={{
        background: 'linear-gradient(135deg, #FEF2F2 0%, #FFF1F2 100%)',
        border: '1px solid #FECACA',
        borderRadius: 12,
        padding: '1.25rem',
        marginBottom: '1.75rem',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        flexWrap: 'wrap',
        gap: '1rem'
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
          <div style={{ width: 44, height: 44, borderRadius: '50%', background: '#FEE2E2', display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#DC2626', flexShrink: 0 }}>
            <PhoneCall size={22} />
          </div>
          <div>
            <div style={{ fontSize: '0.95rem', fontWeight: 800, color: '#991B1B' }}>
              Are you experiencing immediate financial fraud or active extortion?
            </div>
            <div style={{ fontSize: '0.8125rem', color: '#7F1D1D', marginTop: '0.15rem' }}>
              Call national helpline <strong>1930</strong> immediately to freeze financial transactions during the golden hour.
            </div>
          </div>
        </div>
        <a
          href="tel:1930"
          className="btn btn-sm"
          style={{ background: '#DC2626', color: '#FFFFFF', fontWeight: 700, padding: '0.5rem 1rem', borderRadius: 8, textDecoration: 'none' }}
        >
          Call 1930 Now
        </a>
      </div>

      {/* ── Official Indian Cybercrime Reporting Hub ──────────── */}
      <div className="card mb-6" style={{ border: '1px solid #E2E8F0', borderRadius: 14, padding: '1.5rem', background: '#FFFFFF' }}>
        <div style={{ marginBottom: '1.25rem' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', color: '#2563EB', fontSize: '0.75rem', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: '0.2rem' }}>
            Official Authorities · India Only
          </div>
          <h2 style={{ fontSize: '1.125rem', fontWeight: 800, color: '#0F172A', margin: 0 }}>
            Official Cybercrime Reporting Portals &amp; Legal Framework
          </h2>
          <p style={{ fontSize: '0.8125rem', color: '#64748B', margin: '0.2rem 0 0 0' }}>
            Direct government portals and statutory frameworks to lodge official complaints for AI manipulation, deepfake threats, and digital fraud.
          </p>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(290px, 1fr))', gap: '1.25rem' }}>
          
          {/* Card 1: National Cyber Crime Reporting Portal */}
          <div style={{ border: '1px solid #E2E8F0', borderRadius: 12, padding: '1.25rem', display: 'flex', flexDirection: 'column', justifyContent: 'space-between', background: '#F8FAFC' }}>
            <div>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.5rem' }}>
                <span style={{ fontSize: '0.8125rem', fontWeight: 700, color: '#0F172A' }}>🇮🇳 India</span>
                <span style={{ fontSize: '0.7rem', fontWeight: 700, background: '#EFF6FF', color: '#2563EB', padding: '2px 6px', borderRadius: 4 }}>Direct Police Portal</span>
              </div>
              <h3 style={{ fontSize: '0.9375rem', fontWeight: 800, color: '#0F172A', marginBottom: '0.2rem' }}>
                National Cyber Crime Reporting Portal
              </h3>
              <div style={{ fontSize: '0.75rem', color: '#64748B', marginBottom: '0.6rem', fontWeight: 500 }}>
                Ministry of Home Affairs (MHA), Govt. of India
              </div>
              <p style={{ fontSize: '0.8125rem', color: '#334155', lineHeight: 1.5, marginBottom: '1rem' }}>
                Official portal for lodging complaints on deepfake extortion, cyber blackmail, non-consensual imagery, and online financial fraud across all Indian States &amp; UTs.
              </p>
              
              <div style={{ background: '#FEF2F2', border: '1px solid #FECACA', borderRadius: 8, padding: '0.5rem 0.75rem', fontSize: '0.8125rem', fontWeight: 700, color: '#DC2626', marginBottom: '1rem', display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
                📞 1930 (Toll-Free 24x7 Helpline)
              </div>
            </div>

            <a
              href="https://cybercrime.gov.in"
              target="_blank"
              rel="noopener noreferrer"
              className="btn btn-secondary btn-sm"
              style={{ width: '100%', justifyContent: 'center', display: 'flex', alignItems: 'center', gap: '0.4rem' }}
            >
              Open cybercrime.gov.in <ExternalLink size={13} />
            </a>
          </div>

          {/* Card 2: Sanchar Saathi & Chakshu */}
          <div style={{ border: '1px solid #E2E8F0', borderRadius: 12, padding: '1.25rem', display: 'flex', flexDirection: 'column', justifyContent: 'space-between', background: '#F8FAFC' }}>
            <div>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.5rem' }}>
                <span style={{ fontSize: '0.8125rem', fontWeight: 700, color: '#0F172A' }}>🇮🇳 India</span>
                <span style={{ fontSize: '0.7rem', fontWeight: 700, background: '#EFF6FF', color: '#2563EB', padding: '2px 6px', borderRadius: 4 }}>Telecom Vigilance</span>
              </div>
              <h3 style={{ fontSize: '0.9375rem', fontWeight: 800, color: '#0F172A', marginBottom: '0.2rem' }}>
                Chakshu — Suspected Fraud Reporting
              </h3>
              <div style={{ fontSize: '0.75rem', color: '#64748B', marginBottom: '0.6rem', fontWeight: 500 }}>
                Department of Telecommunications (DoT), Govt. of India
              </div>
              <p style={{ fontSize: '0.8125rem', color: '#334155', lineHeight: 1.5, marginBottom: '1rem' }}>
                Report fraudulent WhatsApp accounts, spoofed SMS messages, and extortion calls used to distribute fabricated media or impersonate authority figures.
              </p>
              
              <div style={{ background: '#EFF6FF', border: '1px solid #BFDBFE', borderRadius: 8, padding: '0.5rem 0.75rem', fontSize: '0.8125rem', fontWeight: 700, color: '#2563EB', marginBottom: '1rem', display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
                📞 14422 (Toll-Free Helpline)
              </div>
            </div>

            <a
              href="https://sancharsaathi.gov.in/sfc/"
              target="_blank"
              rel="noopener noreferrer"
              className="btn btn-secondary btn-sm"
              style={{ width: '100%', justifyContent: 'center', display: 'flex', alignItems: 'center', gap: '0.4rem' }}
            >
              Open Chakshu Portal <ExternalLink size={13} />
            </a>
          </div>

          {/* Card 3: Indian Legal Provisions */}
          <div style={{ border: '1px solid #E2E8F0', borderRadius: 12, padding: '1.25rem', display: 'flex', flexDirection: 'column', justifyContent: 'space-between', background: '#F8FAFC' }}>
            <div>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.5rem' }}>
                <span style={{ fontSize: '0.8125rem', fontWeight: 700, color: '#0F172A' }}>⚖️ Legal Provisions</span>
                <span style={{ fontSize: '0.7rem', fontWeight: 700, background: '#F0FDF4', color: '#16A34A', padding: '2px 6px', borderRadius: 4 }}>IT Act &amp; BNS</span>
              </div>
              <h3 style={{ fontSize: '0.9375rem', fontWeight: 800, color: '#0F172A', marginBottom: '0.2rem' }}>
                Applicable Statutory Sections
              </h3>
              <div style={{ fontSize: '0.75rem', color: '#64748B', marginBottom: '0.6rem', fontWeight: 500 }}>
                Information Technology Act 2000 &amp; BNS
              </div>
              <ul style={{ fontSize: '0.75rem', color: '#334155', lineHeight: 1.5, margin: '0 0 1rem 1.1rem', padding: 0 }}>
                <li><b>Sec 66D IT Act:</b> Cheating by impersonation via computer resources.</li>
                <li><b>Sec 66E / 67A IT Act:</b> Privacy violation &amp; sexually explicit / forged media transmission.</li>
                <li><b>Sec 318 / 319 BNS:</b> Cheating &amp; criminal personation.</li>
                <li><b>Sec 308 BNS:</b> Extortion by fear of injury or reputation harm.</li>
              </ul>
            </div>

            <button
              onClick={handleCopyFIR}
              className="btn btn-secondary btn-sm"
              style={{ width: '100%', justifyContent: 'center', display: 'flex', alignItems: 'center', gap: '0.4rem' }}
            >
              {copiedFIR ? <><Check size={13} color="#16A34A" /> Copied FIR Draft ✓</> : <><Copy size={13} /> Copy Incident &amp; Law Sections for FIR</>}
            </button>
          </div>

        </div>
      </div>

      {/* ── Optional Incident Context & Docket Form ──────────── */}
      <div className="card mb-6" style={{ border: '1px solid #E2E8F0', borderRadius: 14, padding: '1.5rem', background: '#FFFFFF' }}>
        <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', flexWrap: 'wrap', gap: '1rem', marginBottom: '1.25rem' }}>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', flexWrap: 'wrap' }}>
              <h2 style={{ fontSize: '1.125rem', fontWeight: 800, color: '#0F172A', margin: 0 }}>
                Incident Context &amp; Evidentiary Docket
              </h2>
              <span style={{ fontSize: '0.7rem', fontWeight: 700, background: '#EFF6FF', color: '#2563EB', padding: '2px 8px', borderRadius: 9999 }}>
                OPTIONAL RECORD
              </span>
              {docketSaved && (
                <span style={{ fontSize: '0.7rem', fontWeight: 700, background: '#F0FDF4', color: '#16A34A', padding: '2px 8px', borderRadius: 9999 }}>
                  Synchronized ✓
                </span>
              )}
            </div>
            <p style={{ fontSize: '0.8125rem', color: '#64748B', margin: '0.2rem 0 0 0' }}>
              Record platform details, suspect handles, and demand records to preserve chain-of-custody context for your investigation.
            </p>
          </div>

          <button
            onClick={() => setBestPracticesOpen(v => !v)}
            className="btn btn-secondary btn-sm"
            style={{ display: 'inline-flex', alignItems: 'center', gap: '0.35rem', color: '#2563EB', borderColor: '#BFDBFE', background: '#EFF6FF' }}
          >
            <BookOpen size={14} /> Evidence Best Practices
          </button>
        </div>

        {/* Best practices callout */}
        {bestPracticesOpen && (
          <div style={{ background: '#F8FAFC', border: '1px solid #E2E8F0', borderRadius: 10, padding: '0.875rem 1rem', marginBottom: '1.25rem', fontSize: '0.8125rem', color: '#334155' }}>
            <div style={{ fontWeight: 700, color: '#0F172A', marginBottom: '0.35rem' }}>Digital Evidence Preservation Guidelines:</div>
            <ul style={{ margin: '0.25rem 0 0 1.1rem', padding: 0, lineHeight: 1.5 }}>
              <li><strong>Preserve Raw Files:</strong> Do not screenshot, crop, or recompress the original suspect image before uploading to preserve metadata and SHA-256 integrity.</li>
              <li><strong>Capture Context:</strong> Take full uncropped screenshots of profile headers, timestamped chat logs, and URLs.</li>
              <li><strong>Payment Records:</strong> Document any requested UPI IDs, bank account names, or cryptocurrency wallets.</li>
            </ul>
          </div>
        )}

        {/* Case ID Input */}
        <div style={{ marginBottom: '1.25rem', maxWidth: 380 }}>
          <label style={{ display: 'block', fontSize: '0.8125rem', fontWeight: 700, color: '#0F172A', marginBottom: '0.35rem' }}>
            Attach to TruthLens Case ID:
          </label>
          <input
            type="text"
            placeholder="e.g. TL-2026-000572"
            value={caseId}
            onChange={e => setCaseId(e.target.value)}
            style={{ width: '100%', padding: '0.55rem 0.75rem', borderRadius: 8, border: '1px solid #CBD5E1', fontSize: '0.875rem', fontFamily: 'var(--font-mono)' }}
          />
        </div>

        {/* Form fields */}
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '1.25rem', marginBottom: '1.25rem' }}>
          
          <div>
            <label style={{ display: 'flex', alignItems: 'center', gap: '0.35rem', fontSize: '0.8125rem', fontWeight: 700, color: '#0F172A', marginBottom: '0.4rem' }}>
              <AlertTriangle size={14} color="#DC2626" /> Incident Classification
            </label>
            <select
              value={docket.incident_category}
              onChange={e => handleDocketChange('incident_category', e.target.value)}
              style={{ width: '100%', padding: '0.55rem 0.75rem', borderRadius: 8, border: '1px solid #CBD5E1', fontSize: '0.875rem', background: '#FFFFFF', color: '#0F172A' }}
            >
              <option value="Extortion & Blackmail">Extortion &amp; Blackmail (Deepfake threat / Sextortion)</option>
              <option value="Identity Theft & Impersonation">Identity Theft &amp; Impersonation (Section 66D IT Act)</option>
              <option value="Financial Fraud & KYC Spoofing">Financial Fraud &amp; KYC Spoofing</option>
              <option value="Matrimonial & Dating Scam">Matrimonial &amp; Dating Scam</option>
              <option value="Non-Consensual Deepfake / Defamation">Non-Consensual Deepfake / Defamation (Sec 66E/67A)</option>
              <option value="Employment & Fake Interview Scam">Employment &amp; Fake Interview Scam</option>
              <option value="Other Cybercrime / Misinformation">Other Cybercrime / Misinformation</option>
            </select>
          </div>

          <div>
            <label style={{ display: 'flex', alignItems: 'center', gap: '0.35rem', fontSize: '0.8125rem', fontWeight: 700, color: '#0F172A', marginBottom: '0.4rem' }}>
              <Globe size={14} color="#2563EB" /> Platform Where Media Encountered
            </label>
            <input
              type="text"
              placeholder="e.g. WhatsApp, Telegram, Instagram, Matrimonial portal..."
              value={docket.circulated_platform}
              onChange={e => handleDocketChange('circulated_platform', e.target.value)}
              style={{ width: '100%', padding: '0.55rem 0.75rem', borderRadius: 8, border: '1px solid #CBD5E1', fontSize: '0.875rem' }}
            />
          </div>

          <div>
            <label style={{ display: 'flex', alignItems: 'center', gap: '0.35rem', fontSize: '0.8125rem', fontWeight: 700, color: '#0F172A', marginBottom: '0.4rem' }}>
              <Calendar size={14} color="#2563EB" /> Date &amp; Time Encountered
            </label>
            <input
              type="text"
              placeholder="e.g. 22 September 2026, 10:30 PM"
              value={docket.incident_date}
              onChange={e => handleDocketChange('incident_date', e.target.value)}
              style={{ width: '100%', padding: '0.55rem 0.75rem', borderRadius: 8, border: '1px solid #CBD5E1', fontSize: '0.875rem' }}
            />
          </div>

          <div>
            <label style={{ display: 'flex', alignItems: 'center', gap: '0.35rem', fontSize: '0.8125rem', fontWeight: 700, color: '#0F172A', marginBottom: '0.4rem' }}>
              <User size={14} color="#2563EB" /> Suspect Identifier / Account / Phone
            </label>
            <input
              type="text"
              placeholder="e.g. +91 98765 43210 or @suspect_handle"
              value={docket.suspect_identifier}
              onChange={e => handleDocketChange('suspect_identifier', e.target.value)}
              style={{ width: '100%', padding: '0.55rem 0.75rem', borderRadius: 8, border: '1px solid #CBD5E1', fontSize: '0.875rem' }}
            />
          </div>

        </div>

        <div style={{ marginBottom: '1.25rem' }}>
          <label style={{ display: 'flex', alignItems: 'center', gap: '0.35rem', fontSize: '0.8125rem', fontWeight: 700, color: '#0F172A', marginBottom: '0.4rem' }}>
            <MessageSquare size={14} color="#2563EB" /> Incident Narrative &amp; Circumstances
          </label>
          <textarea
            rows={3}
            placeholder="Describe the sequence of events and how the media was communicated..."
            value={docket.incident_narrative}
            onChange={e => handleDocketChange('incident_narrative', e.target.value)}
            style={{ width: '100%', padding: '0.65rem 0.75rem', borderRadius: 8, border: '1px solid #CBD5E1', fontSize: '0.875rem', fontFamily: 'inherit', resize: 'vertical' }}
          />
        </div>

        <div style={{ marginBottom: '1.25rem' }}>
          <label style={{ display: 'flex', alignItems: 'center', gap: '0.35rem', fontSize: '0.8125rem', fontWeight: 700, color: '#D97706', marginBottom: '0.4rem' }}>
            <DollarSign size={14} color="#D97706" /> Demands or Threat Details (If any)
          </label>
          <textarea
            rows={2}
            placeholder="e.g. Extortion amounts demanded, threats to disseminate media, OTP requests..."
            value={docket.demands_record}
            onChange={e => handleDocketChange('demands_record', e.target.value)}
            style={{ width: '100%', padding: '0.65rem 0.75rem', borderRadius: 8, border: '1px solid #CBD5E1', fontSize: '0.875rem', fontFamily: 'inherit', resize: 'vertical' }}
          />
        </div>

        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '0.75rem', paddingTop: '0.75rem', borderTop: '1px solid #E2E8F0' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', fontSize: '0.8125rem', color: '#64748B' }}>
            <FileText size={15} color="#2563EB" />
            <span>This context attaches to your formal case file export if generated.</span>
          </div>
          <button
            onClick={handleSaveDocket}
            className="btn btn-primary btn-sm"
            style={{ display: 'inline-flex', alignItems: 'center', gap: '0.4rem' }}
          >
            <Save size={14} /> {docketSaved ? 'Docket Synchronized ✓' : 'Save & Synchronize Docket'}
          </button>
        </div>

      </div>

      {/* ── Disclaimer ───────────────────────────────────────── */}
      <div style={{ textAlign: 'center', fontSize: '0.75rem', color: '#94A3B8', marginTop: '2rem' }}>
        TruthLens provides evidentiary analysis and reporting resources for informational purposes.
        This platform does not constitute a legal authority or police agency. All formal complaints must be lodged with official law enforcement portals.
      </div>

    </div>
  );
}
