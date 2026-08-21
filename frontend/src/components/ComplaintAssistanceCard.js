import React, { useState, useEffect } from 'react';

const DEFAULT_OFFICIAL_PORTAL = 'https://cybercrime.gov.in/';

export default function ComplaintAssistanceCard({
    caseId,
    assessment,
    apiBaseUrl,
    onDownloadForensicReport,
}) {
    const [eligibility, setEligibility] = useState(null);
    const [showForm, setShowForm] = useState(false);
    const [isGenerating, setIsGenerating] = useState(false);
    const [isDownloading, setIsDownloading] = useState(false);
    const [errorMessage, setErrorMessage] = useState(null);
    const [successMessage, setSuccessMessage] = useState(null);

    // Form inputs
    const [incidentDate, setIncidentDate] = useState('');
    const [incidentTime, setIncidentTime] = useState('');
    const [platform, setPlatform] = useState('Instagram');
    const [customPlatform, setCustomPlatform] = useState('');
    const [platformUrl, setPlatformUrl] = useState('');
    const [suspectedAccount, setSuspectedAccount] = useState('');
    const [incidentDescription, setIncidentDescription] = useState('');
    const [impactDescription, setImpactDescription] = useState('');
    const [additionalInfo, setAdditionalInfo] = useState('');

    // Generated draft state
    const [draftResponse, setDraftResponse] = useState(null);
    const [editableText, setEditableText] = useState('');
    const [isEditingDraft, setIsEditingDraft] = useState(false);
    const [copied, setCopied] = useState(false);

    useEffect(() => {
        if (!caseId) return;

        async function fetchEligibility() {
            try {
                const res = await fetch(`${apiBaseUrl}/cases/${caseId}/complaint-eligibility`);
                if (res.ok) {
                    const data = await res.json();
                    setEligibility(data);
                }
            } catch (err) {
                console.warn('Failed to fetch eligibility status', err);
            }
        }

        fetchEligibility();
    }, [caseId, apiBaseUrl]);

    if (!caseId) return null;

    const isHighRisk =
        assessment?.category === 'POTENTIAL_DEEPFAKE' &&
        assessment?.risk_level === 'HIGH';

    const finalPlatform = platform === 'Other' ? (customPlatform || 'Other') : platform;

    const handleGenerateDraft = async (e) => {
        if (e) e.preventDefault();
        setErrorMessage(null);
        setSuccessMessage(null);

        if (!incidentDescription || incidentDescription.trim().length < 10) {
            setErrorMessage('Please provide an incident description with at least 10 characters.');
            return;
        }

        setIsGenerating(true);
        try {
            const payload = {
                incident_date: incidentDate || null,
                incident_time: incidentTime || null,
                platform: finalPlatform || null,
                platform_url: platformUrl || null,
                suspected_account: suspectedAccount || null,
                incident_description: incidentDescription.trim(),
                impact_description: impactDescription.trim() || null,
                additional_info: additionalInfo.trim() || null,
            };

            const res = await fetch(`${apiBaseUrl}/cases/${caseId}/complaint-draft`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload),
            });

            if (!res.ok) {
                const errData = await res.json().catch(() => ({}));
                throw new Error(errData.detail || 'Failed to generate complaint draft.');
            }

            const data = await res.json();
            setDraftResponse(data);
            setEditableText(data.draft.full_text);
            setShowForm(false);
            setSuccessMessage('Complaint draft generated. Please review, edit if necessary, and export.');
        } catch (err) {
            setErrorMessage(err.message || 'Error generating complaint draft.');
        } finally {
            setIsGenerating(false);
        }
    };

    const handleDownloadDraft = async (format = 'pdf') => {
        setErrorMessage(null);
        setIsDownloading(true);
        try {
            const payload = {
                incident_date: incidentDate || null,
                incident_time: incidentTime || null,
                platform: finalPlatform || null,
                platform_url: platformUrl || null,
                suspected_account: suspectedAccount || null,
                incident_description: incidentDescription.trim() || 'Suspected deepfake incident.',
                impact_description: impactDescription.trim() || null,
                additional_info: additionalInfo.trim() || null,
            };

            const res = await fetch(
                `${apiBaseUrl}/cases/${caseId}/complaint-draft/download?format=${format}`,
                {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(payload),
                }
            );

            if (!res.ok) {
                const errData = await res.json().catch(() => ({}));
                throw new Error(errData.detail || `Failed to download ${format.toUpperCase()} draft.`);
            }

            const blob = await res.blob();
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `TruthLens_Complaint_Draft_${caseId}.${format}`;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            setTimeout(() => URL.revokeObjectURL(url), 60000);
        } catch (err) {
            setErrorMessage(err.message || 'Download failed.');
        } finally {
            setIsDownloading(false);
        }
    };

    const handleDownloadEvidencePackage = async () => {
        setErrorMessage(null);
        setIsDownloading(true);
        try {
            const payload = {
                incident_date: incidentDate || null,
                incident_time: incidentTime || null,
                platform: finalPlatform || null,
                platform_url: platformUrl || null,
                suspected_account: suspectedAccount || null,
                incident_description: incidentDescription.trim() || 'Suspected deepfake incident.',
                impact_description: impactDescription.trim() || null,
                additional_info: additionalInfo.trim() || null,
            };

            const res = await fetch(
                `${apiBaseUrl}/cases/${caseId}/evidence-package/download`,
                {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(payload),
                }
            );

            if (!res.ok) {
                const errData = await res.json().catch(() => ({}));
                throw new Error(errData.detail || 'Failed to download evidence package.');
            }

            const blob = await res.blob();
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `TruthLens_Evidence_${caseId}.zip`;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            setTimeout(() => URL.revokeObjectURL(url), 60000);
        } catch (err) {
            setErrorMessage(err.message || 'Evidence package download failed.');
        } finally {
            setIsDownloading(false);
        }
    };

    const handleCopyDraft = () => {
        const textToCopy = editableText || draftResponse?.draft?.full_text || '';
        if (!textToCopy) return;
        navigator.clipboard.writeText(textToCopy).then(() => {
            setCopied(true);
            setTimeout(() => setCopied(false), 3000);
        });
    };

    return (
        <div
            className="card animate-fade-in"
            style={{
                borderTop: '4px solid #8b5cf6',
                marginTop: '1.5rem',
                padding: '1.5rem 2rem',
                background: 'radial-gradient(ellipse at top right, rgba(139,92,246,0.06) 0%, transparent 70%)',
            }}
        >
            {/* Header */}
            <div
                style={{
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'center',
                    flexWrap: 'wrap',
                    gap: '0.75rem',
                    marginBottom: '1.25rem',
                    borderBottom: '1px solid rgba(255,255,255,0.06)',
                    paddingBottom: '0.75rem',
                }}
            >
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                    <span style={{ fontSize: '1.3rem' }}>🛡️</span>
                    <div>
                        <h3 style={{ fontSize: '1.1rem', fontWeight: '700', margin: 0, letterSpacing: '0.04em', textTransform: 'uppercase' }}>
                            Cybercrime Complaint Assistance
                        </h3>
                        <span style={{ fontSize: '0.78rem', color: 'var(--text-secondary)' }}>
                            Prepare a structured, user-reviewable complaint draft and evidence package
                        </span>
                    </div>
                </div>
                <span
                    style={{
                        fontSize: '0.75rem',
                        fontWeight: '700',
                        padding: '0.25rem 0.75rem',
                        borderRadius: '999px',
                        background: 'rgba(139,92,246,0.15)',
                        color: '#c084fc',
                        border: '1px solid rgba(139,92,246,0.3)',
                        letterSpacing: '0.05em',
                    }}
                >
                    TASK 5 · COMPLAINT DRAFTING
                </span>
            </div>

            {/* Case & Risk Overview Badges */}
            <div
                style={{
                    display: 'grid',
                    gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
                    gap: '0.75rem',
                    marginBottom: '1.25rem',
                }}
            >
                <div style={{ background: 'rgba(255,255,255,0.04)', borderRadius: '8px', padding: '0.85rem 1rem', border: '1px solid rgba(255,255,255,0.08)' }}>
                    <div style={{ fontSize: '0.7rem', textTransform: 'uppercase', color: 'var(--text-secondary)', marginBottom: '0.2rem' }}>Case Identifier</div>
                    <div style={{ fontSize: '0.95rem', fontWeight: '800', color: '#c084fc', fontFamily: 'monospace' }}>
                        {caseId}
                    </div>
                </div>
                <div style={{ background: 'rgba(255,255,255,0.04)', borderRadius: '8px', padding: '0.85rem 1rem', border: '1px solid rgba(255,255,255,0.08)' }}>
                    <div style={{ fontSize: '0.7rem', textTransform: 'uppercase', color: 'var(--text-secondary)', marginBottom: '0.2rem' }}>Decision Category</div>
                    <div style={{ fontSize: '0.9rem', fontWeight: '700', color: 'var(--text-primary)' }}>
                        {assessment?.category ? assessment.category.replace(/_/g, ' ') : 'N/A'}
                    </div>
                </div>
                <div style={{ background: 'rgba(255,255,255,0.04)', borderRadius: '8px', padding: '0.85rem 1rem', border: '1px solid rgba(255,255,255,0.08)' }}>
                    <div style={{ fontSize: '0.7rem', textTransform: 'uppercase', color: 'var(--text-secondary)', marginBottom: '0.2rem' }}>Assistance Status</div>
                    <div
                        style={{
                            fontSize: '0.9rem',
                            fontWeight: '700',
                            color: isHighRisk ? '#f87171' : '#60a5fa',
                        }}
                    >
                        {isHighRisk ? '⚠️ Review Recommended' : 'ℹ️ Draft Available on Request'}
                    </div>
                </div>
            </div>

            {/* Notification / Status Banner */}
            {isHighRisk ? (
                <div
                    style={{
                        background: 'rgba(239, 68, 68, 0.08)',
                        border: '1px solid rgba(239, 68, 68, 0.3)',
                        borderRadius: '8px',
                        padding: '1rem 1.25rem',
                        marginBottom: '1.25rem',
                        display: 'flex',
                        flexDirection: 'column',
                        gap: '0.5rem',
                    }}
                >
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', color: '#f87171', fontWeight: '700', fontSize: '0.95rem' }}>
                        <span>⚠️</span>
                        <span>POTENTIAL HIGH-RISK CASE IDENTIFIED</span>
                    </div>
                    <p style={{ margin: 0, fontSize: '0.85rem', color: 'var(--text-secondary)', lineHeight: 1.5 }}>
                        TruthLens detected a combination of signals that may warrant further review.
                        TruthLens can prepare a structured complaint draft using the available forensic evidence and your incident statement.
                    </p>
                </div>
            ) : (
                <div
                    style={{
                        background: 'rgba(59, 130, 246, 0.05)',
                        border: '1px solid rgba(59, 130, 246, 0.2)',
                        borderRadius: '8px',
                        padding: '0.85rem 1.25rem',
                        marginBottom: '1.25rem',
                    }}
                >
                    <p style={{ margin: 0, fontSize: '0.83rem', color: '#93c5fd', lineHeight: 1.5 }}>
                        ℹ️ {eligibility?.recommendation_text || 'Based on the current analysis, TruthLens does not automatically recommend a complaint. You may still review the case and prepare a draft if appropriate.'}
                    </p>
                </div>
            )}

            {/* Error & Success alerts */}
            {errorMessage && (
                <div style={{ padding: '0.75rem 1rem', borderRadius: '6px', background: 'rgba(239,68,68,0.15)', border: '1px solid rgba(239,68,68,0.3)', color: '#fca5a5', marginBottom: '1rem', fontSize: '0.85rem' }}>
                    ⚠️ {errorMessage}
                </div>
            )}
            {successMessage && (
                <div style={{ padding: '0.75rem 1rem', borderRadius: '6px', background: 'rgba(16,185,129,0.15)', border: '1px solid rgba(16,185,129,0.3)', color: '#6ee7b7', marginBottom: '1rem', fontSize: '0.85rem' }}>
                    ✓ {successMessage}
                </div>
            )}

            {/* Step 1: Initial CTA or Draft View Toggle */}
            {!showForm && !draftResponse && (
                <div style={{ display: 'flex', gap: '0.75rem', flexWrap: 'wrap' }}>
                    <button
                        id="btn-prepare-complaint-draft"
                        onClick={() => setShowForm(true)}
                        style={{
                            padding: '0.85rem 1.5rem',
                            background: 'linear-gradient(135deg, #7c3aed, #9333ea)',
                            color: 'white',
                            border: 'none',
                            borderRadius: '8px',
                            fontWeight: '700',
                            fontSize: '0.95rem',
                            cursor: 'pointer',
                            display: 'flex',
                            alignItems: 'center',
                            gap: '0.5rem',
                            boxShadow: '0 4px 15px rgba(124,58,237,0.35)',
                        }}
                    >
                        📝 PREPARE COMPLAINT DRAFT
                    </button>
                </div>
            )}

            {/* Step 2: User Incident Input Form */}
            {showForm && (
                <form
                    onSubmit={handleGenerateDraft}
                    style={{
                        background: 'rgba(15, 23, 42, 0.6)',
                        border: '1px solid rgba(255,255,255,0.08)',
                        borderRadius: '8px',
                        padding: '1.25rem',
                        marginBottom: '1.25rem',
                    }}
                >
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem', borderBottom: '1px solid rgba(255,255,255,0.06)', paddingBottom: '0.5rem' }}>
                        <span style={{ fontWeight: '700', fontSize: '0.95rem', color: '#c084fc' }}>
                            Incident Details & Particulars (User Input)
                        </span>
                        <span style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>
                            * TruthLens will not invent unknown facts
                        </span>
                    </div>

                    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '1rem', marginBottom: '1rem' }}>
                        <div>
                            <label style={{ display: 'block', fontSize: '0.78rem', color: 'var(--text-secondary)', marginBottom: '0.35rem', fontWeight: '600' }}>
                                Incident Date
                            </label>
                            <input
                                type="date"
                                value={incidentDate}
                                onChange={(e) => setIncidentDate(e.target.value)}
                                style={{
                                    width: '100%',
                                    padding: '0.6rem 0.8rem',
                                    borderRadius: '6px',
                                    background: 'rgba(255,255,255,0.05)',
                                    border: '1px solid rgba(255,255,255,0.15)',
                                    color: 'white',
                                    fontSize: '0.88rem',
                                }}
                            />
                        </div>

                        <div>
                            <label style={{ display: 'block', fontSize: '0.78rem', color: 'var(--text-secondary)', marginBottom: '0.35rem', fontWeight: '600' }}>
                                Incident Time (approx)
                            </label>
                            <input
                                type="time"
                                value={incidentTime}
                                onChange={(e) => setIncidentTime(e.target.value)}
                                style={{
                                    width: '100%',
                                    padding: '0.6rem 0.8rem',
                                    borderRadius: '6px',
                                    background: 'rgba(255,255,255,0.05)',
                                    border: '1px solid rgba(255,255,255,0.15)',
                                    color: 'white',
                                    fontSize: '0.88rem',
                                }}
                            />
                        </div>

                        <div>
                            <label style={{ display: 'block', fontSize: '0.78rem', color: 'var(--text-secondary)', marginBottom: '0.35rem', fontWeight: '600' }}>
                                Platform / Service
                            </label>
                            <select
                                value={platform}
                                onChange={(e) => setPlatform(e.target.value)}
                                style={{
                                    width: '100%',
                                    padding: '0.6rem 0.8rem',
                                    borderRadius: '6px',
                                    background: '#1e293b',
                                    border: '1px solid rgba(255,255,255,0.15)',
                                    color: 'white',
                                    fontSize: '0.88rem',
                                }}
                            >
                                <option value="Instagram">Instagram</option>
                                <option value="Facebook">Facebook</option>
                                <option value="WhatsApp">WhatsApp</option>
                                <option value="YouTube">YouTube</option>
                                <option value="X / Twitter">X / Twitter</option>
                                <option value="Telegram">Telegram</option>
                                <option value="LinkedIn">LinkedIn</option>
                                <option value="Other">Other (Specify)</option>
                            </select>
                        </div>

                        {platform === 'Other' && (
                            <div>
                                <label style={{ display: 'block', fontSize: '0.78rem', color: 'var(--text-secondary)', marginBottom: '0.35rem', fontWeight: '600' }}>
                                    Specify Platform Name
                                </label>
                                <input
                                    type="text"
                                    placeholder="e.g., Discord, Forum, Website"
                                    value={customPlatform}
                                    onChange={(e) => setCustomPlatform(e.target.value)}
                                    style={{
                                        width: '100%',
                                        padding: '0.6rem 0.8rem',
                                        borderRadius: '6px',
                                        background: 'rgba(255,255,255,0.05)',
                                        border: '1px solid rgba(255,255,255,0.15)',
                                        color: 'white',
                                        fontSize: '0.88rem',
                                    }}
                                />
                            </div>
                        )}
                    </div>

                    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '1rem', marginBottom: '1rem' }}>
                        <div>
                            <label style={{ display: 'block', fontSize: '0.78rem', color: 'var(--text-secondary)', marginBottom: '0.35rem', fontWeight: '600' }}>
                                Platform / Profile URL (optional)
                            </label>
                            <input
                                type="url"
                                placeholder="https://..."
                                value={platformUrl}
                                onChange={(e) => setPlatformUrl(e.target.value)}
                                style={{
                                    width: '100%',
                                    padding: '0.6rem 0.8rem',
                                    borderRadius: '6px',
                                    background: 'rgba(255,255,255,0.05)',
                                    border: '1px solid rgba(255,255,255,0.15)',
                                    color: 'white',
                                    fontSize: '0.88rem',
                                }}
                            />
                        </div>

                        <div>
                            <label style={{ display: 'block', fontSize: '0.78rem', color: 'var(--text-secondary)', marginBottom: '0.35rem', fontWeight: '600' }}>
                                Suspected Account / Handle (optional)
                            </label>
                            <input
                                type="text"
                                placeholder="@username or channel name"
                                value={suspectedAccount}
                                onChange={(e) => setSuspectedAccount(e.target.value)}
                                style={{
                                    width: '100%',
                                    padding: '0.6rem 0.8rem',
                                    borderRadius: '6px',
                                    background: 'rgba(255,255,255,0.05)',
                                    border: '1px solid rgba(255,255,255,0.15)',
                                    color: 'white',
                                    fontSize: '0.88rem',
                                }}
                            />
                        </div>
                    </div>

                    <div style={{ marginBottom: '1rem' }}>
                        <label style={{ display: 'block', fontSize: '0.78rem', color: '#c084fc', marginBottom: '0.35rem', fontWeight: '700' }}>
                            Incident Description / Statement of Facts *
                        </label>
                        <textarea
                            rows={3}
                            placeholder="Describe what occurred, how you became aware of the suspected manipulation, and where it was distributed..."
                            value={incidentDescription}
                            onChange={(e) => setIncidentDescription(e.target.value)}
                            required
                            style={{
                                width: '100%',
                                padding: '0.6rem 0.8rem',
                                borderRadius: '6px',
                                background: 'rgba(255,255,255,0.05)',
                                border: '1px solid rgba(255,255,255,0.15)',
                                color: 'white',
                                fontSize: '0.88rem',
                                lineHeight: 1.5,
                            }}
                        />
                    </div>

                    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '1rem', marginBottom: '1.25rem' }}>
                        <div>
                            <label style={{ display: 'block', fontSize: '0.78rem', color: 'var(--text-secondary)', marginBottom: '0.35rem', fontWeight: '600' }}>
                                Observed Harm / Impact Description (optional)
                            </label>
                            <textarea
                                rows={2}
                                placeholder="Describe any reputational, financial, or personal consequences..."
                                value={impactDescription}
                                onChange={(e) => setImpactDescription(e.target.value)}
                                style={{
                                    width: '100%',
                                    padding: '0.6rem 0.8rem',
                                    borderRadius: '6px',
                                    background: 'rgba(255,255,255,0.05)',
                                    border: '1px solid rgba(255,255,255,0.15)',
                                    color: 'white',
                                    fontSize: '0.85rem',
                                }}
                            />
                        </div>

                        <div>
                            <label style={{ display: 'block', fontSize: '0.78rem', color: 'var(--text-secondary)', marginBottom: '0.35rem', fontWeight: '600' }}>
                                Additional Information / Notes (optional)
                            </label>
                            <textarea
                                rows={2}
                                placeholder="Any additional context, witness details, or platform report IDs..."
                                value={additionalInfo}
                                onChange={(e) => setAdditionalInfo(e.target.value)}
                                style={{
                                    width: '100%',
                                    padding: '0.6rem 0.8rem',
                                    borderRadius: '6px',
                                    background: 'rgba(255,255,255,0.05)',
                                    border: '1px solid rgba(255,255,255,0.15)',
                                    color: 'white',
                                    fontSize: '0.85rem',
                                }}
                            />
                        </div>
                    </div>

                    <div style={{ display: 'flex', gap: '0.75rem', flexWrap: 'wrap' }}>
                        <button
                            type="submit"
                            id="btn-submit-generate-draft"
                            disabled={isGenerating}
                            style={{
                                padding: '0.75rem 1.25rem',
                                background: isGenerating ? 'rgba(124,58,237,0.3)' : 'linear-gradient(135deg, #7c3aed, #9333ea)',
                                color: 'white',
                                border: 'none',
                                borderRadius: '6px',
                                fontWeight: '700',
                                fontSize: '0.9rem',
                                cursor: isGenerating ? 'not-allowed' : 'pointer',
                            }}
                        >
                            {isGenerating ? '⏳ Compiling Draft...' : '✓ Generate Complaint Draft'}
                        </button>
                        <button
                            type="button"
                            onClick={() => setShowForm(false)}
                            style={{
                                padding: '0.75rem 1.25rem',
                                background: 'transparent',
                                color: 'var(--text-secondary)',
                                border: '1px solid rgba(255,255,255,0.1)',
                                borderRadius: '6px',
                                cursor: 'pointer',
                                fontSize: '0.9rem',
                            }}
                        >
                            Cancel
                        </button>
                    </div>
                </form>
            )}

            {/* Step 3: Complaint Draft Preview, Live Editor & Action Package */}
            {draftResponse && (
                <div
                    style={{
                        background: 'rgba(15, 23, 42, 0.7)',
                        border: '1px solid rgba(139,92,246,0.3)',
                        borderRadius: '8px',
                        padding: '1.25rem',
                        marginBottom: '1.25rem',
                    }}
                >
                    <div
                        style={{
                            display: 'flex',
                            justifyContent: 'space-between',
                            alignItems: 'center',
                            flexWrap: 'wrap',
                            gap: '0.5rem',
                            marginBottom: '1rem',
                            borderBottom: '1px solid rgba(255,255,255,0.06)',
                            paddingBottom: '0.5rem',
                        }}
                    >
                        <div>
                            <span style={{ fontWeight: '700', fontSize: '0.95rem', color: '#c084fc' }}>
                                📄 Complaint Draft Preview
                            </span>
                            <span style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', marginLeft: '0.5rem' }}>
                                (User-Reviewable Document)
                            </span>
                        </div>
                        <button
                            onClick={() => setIsEditingDraft(!isEditingDraft)}
                            style={{
                                padding: '0.35rem 0.75rem',
                                borderRadius: '4px',
                                background: isEditingDraft ? 'rgba(139,92,246,0.2)' : 'rgba(255,255,255,0.05)',
                                color: '#c084fc',
                                border: '1px solid rgba(139,92,246,0.4)',
                                fontSize: '0.8rem',
                                cursor: 'pointer',
                            }}
                        >
                            {isEditingDraft ? '✓ Done Editing' : '✏️ Edit Text Directly'}
                        </button>
                    </div>

                    {/* Live Editor / Preview box */}
                    {isEditingDraft ? (
                        <textarea
                            rows={14}
                            value={editableText}
                            onChange={(e) => setEditableText(e.target.value)}
                            style={{
                                width: '100%',
                                padding: '0.85rem',
                                borderRadius: '6px',
                                background: '#090d16',
                                border: '1px solid rgba(139,92,246,0.4)',
                                color: '#e2e8f0',
                                fontFamily: 'monospace',
                                fontSize: '0.82rem',
                                lineHeight: 1.5,
                                marginBottom: '1rem',
                            }}
                        />
                    ) : (
                        <pre
                            style={{
                                background: '#090d16',
                                border: '1px solid rgba(255,255,255,0.08)',
                                borderRadius: '6px',
                                padding: '1rem',
                                color: '#cbd5e1',
                                fontSize: '0.8rem',
                                lineHeight: 1.45,
                                maxHeight: '350px',
                                overflowY: 'auto',
                                whiteSpace: 'pre-wrap',
                                wordBreak: 'break-word',
                                fontFamily: 'monospace',
                                marginBottom: '1rem',
                            }}
                        >
                            {editableText || draftResponse.draft.full_text}
                        </pre>
                    )}

                    {/* Download & Packaging Actions */}
                    <div style={{ display: 'flex', gap: '0.65rem', flexWrap: 'wrap', marginBottom: '1rem' }}>
                        <button
                            id="btn-copy-complaint-draft"
                            onClick={handleCopyDraft}
                            style={{
                                padding: '0.7rem 1.1rem',
                                background: copied ? 'rgba(16,185,129,0.2)' : 'rgba(255,255,255,0.08)',
                                color: copied ? '#6ee7b7' : 'white',
                                border: '1px solid rgba(255,255,255,0.15)',
                                borderRadius: '6px',
                                fontSize: '0.88rem',
                                fontWeight: '600',
                                cursor: 'pointer',
                            }}
                        >
                            {copied ? '✓ Copied to Clipboard!' : '📋 Copy Draft Text'}
                        </button>

                        <button
                            id="btn-download-draft-txt"
                            onClick={() => handleDownloadDraft('txt')}
                            disabled={isDownloading}
                            style={{
                                padding: '0.7rem 1.1rem',
                                background: 'rgba(255,255,255,0.08)',
                                color: 'white',
                                border: '1px solid rgba(255,255,255,0.15)',
                                borderRadius: '6px',
                                fontSize: '0.88rem',
                                fontWeight: '600',
                                cursor: 'pointer',
                            }}
                        >
                            📄 Download TXT
                        </button>

                        <button
                            id="btn-download-draft-pdf"
                            onClick={() => handleDownloadDraft('pdf')}
                            disabled={isDownloading}
                            style={{
                                padding: '0.7rem 1.1rem',
                                background: 'linear-gradient(135deg, #2563eb, #3b82f6)',
                                color: 'white',
                                border: 'none',
                                borderRadius: '6px',
                                fontSize: '0.88rem',
                                fontWeight: '700',
                                cursor: 'pointer',
                            }}
                        >
                            📑 Download PDF Draft
                        </button>

                        <button
                            id="btn-download-evidence-package"
                            onClick={handleDownloadEvidencePackage}
                            disabled={isDownloading}
                            style={{
                                padding: '0.7rem 1.1rem',
                                background: 'linear-gradient(135deg, #7c3aed, #9333ea)',
                                color: 'white',
                                border: 'none',
                                borderRadius: '6px',
                                fontSize: '0.88rem',
                                fontWeight: '700',
                                cursor: 'pointer',
                            }}
                        >
                            📦 Download Evidence Package (ZIP)
                        </button>

                        <button
                            onClick={() => setShowForm(true)}
                            style={{
                                padding: '0.7rem 1.1rem',
                                background: 'transparent',
                                color: 'var(--text-secondary)',
                                border: '1px solid rgba(255,255,255,0.1)',
                                borderRadius: '6px',
                                fontSize: '0.88rem',
                                cursor: 'pointer',
                            }}
                        >
                            ✏️ Edit Incident Form
                        </button>
                    </div>

                    {/* Official Cybercrime Portal Handoff */}
                    <div
                        style={{
                            background: 'rgba(245, 158, 11, 0.08)',
                            border: '1px solid rgba(245, 158, 11, 0.25)',
                            borderRadius: '6px',
                            padding: '0.9rem 1.1rem',
                            display: 'flex',
                            justifyContent: 'space-between',
                            alignItems: 'center',
                            flexWrap: 'wrap',
                            gap: '0.75rem',
                        }}
                    >
                        <div>
                            <div style={{ fontWeight: '700', fontSize: '0.88rem', color: '#fbbf24', marginBottom: '0.2rem' }}>
                                🏛️ Official Cybercrime Reporting Portal
                            </div>
                            <div style={{ fontSize: '0.78rem', color: 'var(--text-secondary)' }}>
                                TruthLens does not automatically submit complaints. You can manually submit your reviewed draft through the official portal.
                            </div>
                        </div>
                        <a
                            id="btn-open-cybercrime-portal"
                            href={draftResponse.official_portal_url || DEFAULT_OFFICIAL_PORTAL}
                            target="_blank"
                            rel="noopener noreferrer"
                            style={{
                                padding: '0.65rem 1.1rem',
                                background: '#f59e0b',
                                color: '#0f172a',
                                borderRadius: '6px',
                                textDecoration: 'none',
                                fontWeight: '700',
                                fontSize: '0.85rem',
                                display: 'inline-flex',
                                alignItems: 'center',
                                gap: '0.35rem',
                            }}
                        >
                            OPEN OFFICIAL PORTAL ↗
                        </a>
                    </div>
                </div>
            )}

            {/* Legal Disclaimer Footer */}
            <div
                style={{
                    marginTop: '0.75rem',
                    padding: '0.75rem 1rem',
                    borderRadius: '6px',
                    background: 'rgba(255,255,255,0.02)',
                    border: '1px solid rgba(255,255,255,0.05)',
                }}
            >
                <p style={{ margin: 0, fontSize: '0.72rem', color: 'rgba(148,163,184,0.6)', textAlign: 'center', fontStyle: 'italic', lineHeight: 1.5 }}>
                    ⚖️ TruthLens provides AI-assisted analysis and complaint drafting support. The generated draft is not an official complaint and does not establish that a crime has occurred. Review all information carefully and submit only accurate information through the appropriate official channel. TruthLens does not automatically submit complaints.
                </p>
            </div>
        </div>
    );
}
