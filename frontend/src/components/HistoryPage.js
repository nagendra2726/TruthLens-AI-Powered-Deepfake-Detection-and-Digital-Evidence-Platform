import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Search, Eye, Download, Clock, SlidersHorizontal, Loader2,
  Archive, Trash2, AlertTriangle, CheckCircle2, X, Shield
} from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { db } from '../config/firebase';
import { collection, query, orderBy, onSnapshot, doc, deleteDoc } from 'firebase/firestore';

import { API_BASE_URL } from '../config/api';
import { downloadPDF } from '../utils/exportUtils';

export function getStoredHistory() {
  try { return JSON.parse(localStorage.getItem('truthlens_history') || '[]'); } catch { return []; }
}

const HistoryPage = () => {
  const { user } = useAuth();
  const [history, setHistory]   = useState([]);
  const [loading, setLoading]   = useState(true);
  const [search, setSearch]     = useState('');
  const [filter, setFilter]     = useState('ALL');
  const [sort, setSort]         = useState('NEWEST');
  const [dlId, setDlId]         = useState(null);
  const [dlCaseId, setDlCaseId] = useState(null);

  // Delete modal & toast state
  const [deleteTarget, setDeleteTarget] = useState(null);
  const [deleting, setDeleting] = useState(false);
  const [toastMessage, setToastMessage] = useState(null);

  const navigate = useNavigate();

  useEffect(() => {
    if (!user?.uid) {
      setHistory(getStoredHistory());
      setLoading(false);
      return;
    }
    setLoading(true);
    const q = query(collection(db, 'users', user.uid, 'analyses'), orderBy('createdAt', 'desc'));
    const unsub = onSnapshot(q, snap => {
      const items = [];
      snap.forEach(d => {
        const data = d.data();
        items.push({
          id: d.id,
          caseId: data.caseId || d.id,
          timestamp: data.timestamp || new Date().toISOString(),
          mode: data.mode || 'compare',
          filenames: [data.referenceFileName || 'File', data.suspectedFileName || ''],
          verdict: data.verdict || '',
          riskLevel: data.riskLevel || '',
          confidence: data.confidence || '',
          caseFileGenerated: Boolean(data.caseFileGenerated),
          data: data.data || data,
        });
      });
      setHistory(items);
      setLoading(false);
    }, () => { setHistory(getStoredHistory()); setLoading(false); });
    return () => unsub();
  }, [user]);

  const handleCaseFileAction = async (item, e) => {
    e.stopPropagation();
    const caseId = item.caseId || item.id;
    setDlCaseId(caseId);
    try {
      if (!item.caseFileGenerated) {
        // Generate on demand
        await fetch(`${API_BASE_URL}/api/cases/${caseId}/generate`, { method: 'POST' });
        item.caseFileGenerated = true;
        setHistory(prev => prev.map(h => (h.caseId === caseId || h.id === caseId) ? { ...h, caseFileGenerated: true } : h));
        try {
          const stored = JSON.parse(localStorage.getItem('truthlens_history') || '[]');
          const updated = stored.map(s => (s.caseId === caseId || s.id === caseId) ? { ...s, caseFileGenerated: true } : s);
          localStorage.setItem('truthlens_history', JSON.stringify(updated));
        } catch (_) {}
      }

      // Download
      const res = await fetch(`${API_BASE_URL}/reports/${caseId}/case-file/download`);
      if (res.ok) {
        const blob = await res.blob();
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `TruthLens_Case_${caseId}.zip`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        setTimeout(() => URL.revokeObjectURL(url), 60000);
        return;
      }
      alert('Unable to download case file. Please try again.');
    } catch {
      alert('Unable to process case file. Please ensure the backend server is running.');
    } finally {
      setDlCaseId(null);
    }
  };

  const handleDownload = async (caseId, e) => {
    e.stopPropagation();
    setDlId(caseId);
    try {
      const res = await fetch(`${API_BASE_URL}/reports/${caseId}/download`);
      if (res.ok) {
        const blob = await res.blob();
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `TruthLens_Report_${caseId}.pdf`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        setTimeout(() => URL.revokeObjectURL(url), 60000);
        return;
      }
      const histItem = history.find(h => h.caseId === caseId || h.id === caseId);
      if (histItem?.data) {
        downloadPDF(histItem.data, caseId);
        return;
      }
      throw new Error('Report could not be retrieved.');
    } catch {
      const histItem = history.find(h => h.caseId === caseId || h.id === caseId);
      if (histItem?.data) {
        try {
          downloadPDF(histItem.data, caseId);
          return;
        } catch (_) {}
      }
      alert('Unable to download report. Please ensure the backend server is running.');
    } finally {
      setDlId(null);
    }
  };

  // Delete Handlers
  const handleDeleteClick = (item, e) => {
    e.stopPropagation();
    setDeleteTarget(item);
  };

  const handleCancelDelete = () => {
    if (!deleting) setDeleteTarget(null);
  };

  const handleConfirmDelete = async () => {
    if (!deleteTarget) return;
    const targetCaseId = deleteTarget.caseId || deleteTarget.id;
    setDeleting(true);
    try {
      if (user?.uid) {
        await deleteDoc(doc(db, 'users', user.uid, 'analyses', targetCaseId));
      }

      // Remove from localStorage
      try {
        const stored = JSON.parse(localStorage.getItem('truthlens_history') || '[]');
        const updated = stored.filter(s => s.caseId !== targetCaseId && s.id !== targetCaseId);
        localStorage.setItem('truthlens_history', JSON.stringify(updated));
      } catch (_) {}

      // Update state
      setHistory(prev => prev.filter(h => h.caseId !== targetCaseId && h.id !== targetCaseId));
      setDeleteTarget(null);
      setToastMessage({ text: 'Analysis deleted successfully.', type: 'success' });
      setTimeout(() => setToastMessage(null), 3500);
    } catch (err) {
      setToastMessage({ text: 'Unable to delete the analysis. Please try again.', type: 'error' });
      setTimeout(() => setToastMessage(null), 3500);
    } finally {
      setDeleting(false);
    }
  };

  const FILTERS = [
    { id: 'ALL', label: 'All' },
    { id: 'POTENTIAL_DEEPFAKE', label: 'Likely AI' },
    { id: 'LIKELY_AUTHENTIC', label: 'Likely Real' },
    { id: 'INCONCLUSIVE', label: 'Inconclusive' },
  ];

  const getVerdict = (v = '') => {
    if (v.includes('AUTHENTIC')) return { label: 'Likely Real', cls: 'badge-green' };
    if (v.includes('DEEPFAKE') || v.includes('FAKE') || v.includes('AI_GENERATED')) return { label: 'Likely AI-Generated', cls: 'badge-red' };
    return { label: 'Inconclusive', cls: 'badge-gray' };
  };

  const filtered = history
    .filter(item => {
      if (filter !== 'ALL') {
        const v = item.verdict || '';
        if (filter === 'POTENTIAL_DEEPFAKE' && !v.includes('DEEPFAKE') && !v.includes('FAKE') && !v.includes('AI_GENERATED')) return false;
        if (filter === 'LIKELY_AUTHENTIC' && !v.includes('AUTHENTIC')) return false;
        if (filter === 'INCONCLUSIVE' && (v.includes('AUTHENTIC') || v.includes('DEEPFAKE') || v.includes('FAKE'))) return false;
      }
      if (search.trim()) {
        const q = search.toLowerCase();
        const cid = (item.caseId || '').toLowerCase();
        const fn = (item.filenames || []).join(' ').toLowerCase();
        if (!cid.includes(q) && !fn.includes(q)) return false;
      }
      return true;
    })
    .sort((a, b) => {
      const da = new Date(a.timestamp || 0);
      const db = new Date(b.timestamp || 0);
      return sort === 'NEWEST' ? db - da : da - db;
    });

  return (
    <div className="fade-in">
      {/* Toast Notification */}
      {toastMessage && (
        <div style={{
          position: 'fixed',
          top: '1.5rem',
          right: '1.5rem',
          zIndex: 100,
          background: toastMessage.type === 'error' ? '#FEF2F2' : '#F0FDF4',
          color: toastMessage.type === 'error' ? '#DC2626' : '#16A34A',
          border: `1px solid ${toastMessage.type === 'error' ? '#FCA5A5' : '#86EFAC'}`,
          borderRadius: '10px',
          padding: '0.75rem 1.25rem',
          boxShadow: '0 4px 12px rgba(0,0,0,0.08)',
          display: 'flex',
          alignItems: 'center',
          gap: '0.5rem',
          fontSize: '0.875rem',
          fontWeight: 600
        }}>
          {toastMessage.type === 'error' ? <AlertTriangle size={16} /> : <CheckCircle2 size={16} />}
          <span>{toastMessage.text}</span>
          <button onClick={() => setToastMessage(null)} style={{ background: 'none', border: 'none', cursor: 'pointer', marginLeft: '0.5rem', color: 'inherit' }}>
            <X size={14} />
          </button>
        </div>
      )}

      {/* Delete Confirmation Modal */}
      {deleteTarget && (
        <div style={{
          position: 'fixed',
          inset: 0,
          background: 'rgba(15, 23, 42, 0.4)',
          backdropFilter: 'blur(2px)',
          zIndex: 99,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          padding: '1rem'
        }}>
          <div style={{
            background: '#FFFFFF',
            borderRadius: '16px',
            border: '1px solid #E2E8F0',
            padding: '1.75rem',
            maxWidth: 420,
            width: '100%',
            boxShadow: '0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04)'
          }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '0.75rem' }}>
              <div style={{ width: 40, height: 40, borderRadius: '50%', background: '#FEF2F2', display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#DC2626' }}>
                <Trash2 size={20} />
              </div>
              <h3 style={{ fontSize: '1.125rem', fontWeight: 800, color: '#0F172A', margin: 0 }}>
                Delete Analysis?
              </h3>
            </div>

            <p style={{ fontSize: '0.875rem', color: '#64748B', lineHeight: 1.5, marginBottom: '1.5rem' }}>
              Are you sure you want to delete this analysis? This action cannot be undone.
            </p>

            <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '0.75rem' }}>
              <button
                onClick={handleCancelDelete}
                disabled={deleting}
                className="btn btn-secondary btn-sm"
              >
                Cancel
              </button>
              <button
                onClick={handleConfirmDelete}
                disabled={deleting}
                className="btn btn-sm"
                style={{
                  background: '#DC2626',
                  color: '#FFFFFF',
                  border: 'none',
                  fontWeight: 700,
                  padding: '0.45rem 1rem',
                  borderRadius: '8px'
                }}
              >
                {deleting ? 'Deleting…' : 'Delete'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Header */}
      <div style={{ marginBottom: '1.75rem' }}>
        <h1 style={{ fontSize: '1.625rem', fontWeight: 800, color: 'var(--text)', marginBottom: '0.35rem', letterSpacing: '-0.02em' }}>
          Analysis History
        </h1>
        <p style={{ fontSize: '0.9375rem', color: 'var(--text-muted)' }}>
          View and manage your previous TruthLens analyses.
        </p>
      </div>

      {/* Controls */}
      <div style={{ background: 'var(--bg-white)', border: '1px solid var(--border)', borderRadius: 'var(--r-lg)', padding: '1rem 1.25rem', marginBottom: '1.25rem', boxShadow: 'var(--shadow-sm)' }}>
        <div className="flex flex-wrap gap-3 items-center justify-between">
          {/* Search */}
          <div style={{ position: 'relative', flex: '1 1 260px' }}>
            <Search size={16} style={{ position: 'absolute', left: '0.875rem', top: '50%', transform: 'translateY(-50%)', color: 'var(--text-faint)' }} />
            <input type="text" className="input" placeholder="Search by case ID or filename…"
              value={search} onChange={e => setSearch(e.target.value)}
              style={{ paddingLeft: '2.5rem' }}
            />
          </div>
          {/* Filters */}
          <div className="flex gap-2 flex-wrap">
            {FILTERS.map(f => (
              <button key={f.id} onClick={() => setFilter(f.id)}
                className={`btn btn-sm ${filter === f.id ? 'btn-primary' : 'btn-secondary'}`}>
                {f.label}
              </button>
            ))}
          </div>
          {/* Sort */}
          <div className="flex items-center gap-2">
            <SlidersHorizontal size={15} style={{ color: 'var(--text-faint)' }} />
            <select value={sort} onChange={e => setSort(e.target.value)}
              style={{ background: 'var(--bg-white)', border: '1px solid var(--border-mid)', borderRadius: 'var(--r-md)', color: 'var(--text-2)', fontSize: '0.875rem', padding: '0.42rem 0.75rem', outline: 'none', cursor: 'pointer' }}>
              <option value="NEWEST">Newest first</option>
              <option value="OLDEST">Oldest first</option>
            </select>
          </div>
        </div>
      </div>

      {/* Content */}
      {loading ? (
        <div style={{ textAlign: 'center', padding: '5rem 1rem' }}>
          <Loader2 size={32} className="spin-anim" style={{ margin: '0 auto 0.75rem', color: 'var(--blue)' }} />
          <p style={{ color: 'var(--text-muted)' }}>Loading history…</p>
        </div>
      ) : filtered.length === 0 ? (
        <div className="empty-state">
          <div className="empty-icon"><Clock size={24} /></div>
          <h3 style={{ fontSize: '1rem', fontWeight: 700, color: 'var(--text)', marginBottom: '0.35rem' }}>
            {search || filter !== 'ALL' ? 'No matches found' : 'No analyses yet'}
          </h3>
          <p style={{ fontSize: '0.875rem', color: 'var(--text-muted)', maxWidth: 340, margin: '0 auto 1.25rem' }}>
            {search || filter !== 'ALL' ? 'Try adjusting your search or filters.' : 'Start a new analysis to see your results here.'}
          </p>
          {!search && filter === 'ALL' && (
            <button onClick={() => navigate('/analyze')} className="btn btn-primary">Start New Analysis</button>
          )}
        </div>
      ) : (
        <div style={{ background: 'var(--bg-white)', border: '1px solid var(--border)', borderRadius: 'var(--r-lg)', overflow: 'hidden', boxShadow: 'var(--shadow-sm)' }}>
          {/* Desktop table */}
          <div className="desktop-only" style={{ overflowX: 'auto' }}>
            <table className="tl-table">
              <thead>
                <tr>
                  <th>Case ID</th>
                  <th>Date</th>
                  <th>Filename</th>
                  <th>Result</th>
                  <th>AI Prob.</th>
                  <th>Risk</th>
                  <th>Confidence</th>
                  <th style={{ textAlign: 'right' }}>Actions</th>
                </tr>
              </thead>
              <tbody>
                {filtered.map(item => {
                  const vd = getVerdict(item.verdict);
                  const risk = item.riskLevel || '';
                  const riskCls = risk === 'HIGH' ? 'badge-red' : risk === 'LOW' ? 'badge-green' : 'badge-amber';
                  const aiProb = item.data?.result?.ai_probability ?? item.data?.suspected_analysis?.ai_probability ?? null;
                  const aiProbDisplay = aiProb != null ? `${(aiProb * 100).toFixed(1)}%` : '—';
                  return (
                    <tr key={item.id} style={{ cursor: 'pointer' }}
                      onClick={() => navigate(`/history/${item.caseId}`, { state: { resultData: item.data } })}>
                      <td><span style={{ fontFamily: 'var(--font-mono)', fontSize: '0.8125rem', fontWeight: 600, color: 'var(--text)' }}>{item.caseId}</span></td>
                      <td style={{ whiteSpace: 'nowrap' }}>{item.timestamp ? new Date(item.timestamp).toLocaleDateString('en-IN', { day: '2-digit', month: 'short', year: 'numeric' }) : '—'}</td>
                      <td style={{ maxWidth: 180 }}><span className="truncate" style={{ display: 'block' }}>{item.filenames?.[0] || '—'}</span></td>
                      <td><span className={`badge ${vd.cls}`}>{vd.label}</span></td>
                      <td style={{ fontFamily: 'var(--font-mono)', fontSize: '0.8125rem', fontWeight: 600, color: aiProb != null && aiProb >= 0.5 ? '#DC2626' : '#16A34A' }}>{aiProbDisplay}</td>
                      <td><span className={`badge ${riskCls}`}>{risk || '—'}</span></td>
                      <td style={{ color: 'var(--text-muted)', fontSize: '0.8125rem' }}>{item.confidence || '—'}</td>
                      <td>
                        <div className="flex gap-2 justify-between" style={{ justifyContent: 'flex-end', alignItems: 'center' }}>
                          <button onClick={e => { e.stopPropagation(); navigate(`/history/${item.caseId}`, { state: { resultData: item.data } }); }}
                            className="btn btn-ghost btn-sm" style={{ color: 'var(--blue)' }}>
                            <Eye size={14} /> View
                          </button>
                          <button onClick={e => { e.stopPropagation(); navigate(`/help-reporting?caseId=${item.caseId}`); }}
                            className="btn btn-ghost btn-sm" style={{ color: '#2563EB' }} title="Help & Reporting / Evidentiary Docket">
                            <Shield size={14} /> Reporting
                          </button>
                          <button onClick={e => handleDownload(item.caseId, e)} disabled={dlId === item.caseId}
                            className="btn btn-secondary btn-sm">
                            <Download size={14} /> {dlId === item.caseId ? '…' : 'Report'}
                          </button>
                          <button onClick={e => handleCaseFileAction(item, e)} disabled={dlCaseId === item.caseId}
                            className="btn btn-secondary btn-sm" title="Download Case File ZIP">
                            <Archive size={14} /> {dlCaseId === item.caseId ? '…' : 'Case File'}
                          </button>
                          <button
                            onClick={e => handleDeleteClick(item, e)}
                            className="btn btn-ghost btn-sm"
                            title="Delete analysis"
                            style={{ color: '#DC2626', padding: '0.35rem 0.5rem' }}
                            onMouseEnter={e => e.currentTarget.style.background = '#FEF2F2'}
                            onMouseLeave={e => e.currentTarget.style.background = 'transparent'}
                          >
                            <Trash2 size={14} />
                          </button>
                        </div>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>

          {/* Mobile cards */}
          <div className="mobile-only flex-col" style={{ gap: 0 }}>
            {filtered.map((item, idx) => {
              const vd = getVerdict(item.verdict);
              return (
                <div key={item.id}
                  style={{ padding: '1rem', borderBottom: idx < filtered.length - 1 ? '1px solid var(--border)' : 'none', cursor: 'pointer' }}
                  onClick={() => navigate(`/history/${item.caseId}`, { state: { resultData: item.data } })}>
                  <div className="flex justify-between items-start mb-2">
                    <span style={{ fontFamily: 'var(--font-mono)', fontSize: '0.8125rem', fontWeight: 600, color: 'var(--text)' }}>{item.caseId}</span>
                    <span className={`badge ${vd.cls}`}>{vd.label}</span>
                  </div>
                  <p style={{ fontSize: '0.8125rem', color: 'var(--text-muted)', marginBottom: '0.75rem' }}>
                    {item.filenames?.[0] || '—'} · {item.timestamp ? new Date(item.timestamp).toLocaleDateString('en-IN', { day: '2-digit', month: 'short' }) : ''}
                  </p>
                  <div className="flex gap-2 flex-wrap items-center">
                    <button onClick={e => { e.stopPropagation(); navigate(`/history/${item.caseId}`, { state: { resultData: item.data } }); }}
                      className="btn btn-ghost btn-sm" style={{ color: 'var(--blue)' }}>
                      <Eye size={14} /> View
                    </button>
                    <button onClick={e => { e.stopPropagation(); navigate(`/help-reporting?caseId=${item.caseId}`); }}
                      className="btn btn-ghost btn-sm" style={{ color: '#2563EB' }}>
                      <Shield size={14} /> Reporting
                    </button>
                    <button onClick={e => handleDownload(item.caseId, e)} disabled={dlId === item.caseId}
                      className="btn btn-secondary btn-sm">
                      <Download size={14} /> Report
                    </button>
                    <button onClick={e => handleCaseFileAction(item, e)} disabled={dlCaseId === item.caseId}
                      className="btn btn-secondary btn-sm">
                      <Archive size={14} /> Case File
                    </button>
                    <button
                      onClick={e => handleDeleteClick(item, e)}
                      className="btn btn-ghost btn-sm"
                      style={{ color: '#DC2626' }}
                    >
                      <Trash2 size={14} /> Delete
                    </button>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
};

export default HistoryPage;
