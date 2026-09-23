import React, { useState } from 'react';
import { User, Mail, LogOut, Edit2, Shield, CheckCircle2, AlertCircle } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { updateProfile } from 'firebase/auth';
import { auth } from '../config/firebase';
import { useNavigate } from 'react-router-dom';

const ProfilePage = ({ onLogout }) => {
  const { user, userProfile } = useAuth();
  const navigate = useNavigate();
  const [editing, setEditing] = useState(false);
  const [name, setName] = useState(userProfile?.name || user?.displayName || '');
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);
  const [error, setError] = useState('');

  const displayName = userProfile?.name || user?.displayName || '—';
  const email = user?.email || '—';
  const provider = user?.providerData?.[0]?.providerId === 'google.com' ? 'Google' : 'Email & Password';
  const createdAt = user?.metadata?.creationTime
    ? new Date(user.metadata.creationTime).toLocaleDateString('en-IN', { day: '2-digit', month: 'long', year: 'numeric' })
    : '—';
  const initial = displayName !== '—' ? displayName.charAt(0).toUpperCase() : email.charAt(0).toUpperCase();

  const handleSave = async (e) => {
    e.preventDefault();
    if (!name.trim()) { setError('Name cannot be empty.'); return; }
    setSaving(true); setError('');
    try {
      if (auth.currentUser) {
        await updateProfile(auth.currentUser, { displayName: name.trim() });
      }
      setSaved(true);
      setEditing(false);
      setTimeout(() => setSaved(false), 2500);
    } catch (err) {
      setError(err.message || 'Could not save changes.');
    } finally { setSaving(false); }
  };

  const handleLogout = () => {
    if (onLogout) onLogout();
    else navigate('/login');
  };

  return (
    <div className="fade-in" style={{ maxWidth: 560, margin: '0 auto' }}>
      <h1 style={{ fontSize: '1.625rem', fontWeight: 800, color: 'var(--text)', marginBottom: '0.35rem', letterSpacing: '-0.02em' }}>
        Profile
      </h1>
      <p style={{ fontSize: '0.9375rem', color: 'var(--text-muted)', marginBottom: '2rem' }}>
        Manage your TruthLens account.
      </p>

      {/* Avatar */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '1.25rem', marginBottom: '2rem', padding: '1.5rem', background: 'var(--bg-white)', border: '1px solid var(--border)', borderRadius: 'var(--r-xl)', boxShadow: 'var(--shadow-sm)' }}>
        <div style={{
          width: 64, height: 64, borderRadius: '50%',
          background: 'var(--blue)', color: '#fff',
          fontWeight: 800, fontSize: '1.5rem',
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          flexShrink: 0,
        }}>
          {initial}
        </div>
        <div>
          <p style={{ fontWeight: 700, fontSize: '1.0625rem', color: 'var(--text)' }}>{displayName}</p>
          <p style={{ fontSize: '0.875rem', color: 'var(--text-muted)' }}>{email}</p>
        </div>
      </div>

      {/* Success / Error */}
      {saved && (
        <div className="alert alert-success mb-4">
          <CheckCircle2 size={16} style={{ flexShrink: 0 }} />
          <span>Profile updated successfully.</span>
        </div>
      )}
      {error && (
        <div className="alert alert-error mb-4">
          <AlertCircle size={16} style={{ flexShrink: 0 }} />
          <span>{error}</span>
        </div>
      )}

      {/* Profile Details */}
      <div className="card mb-4">
        <div className="flex justify-between items-center" style={{ marginBottom: '1.25rem' }}>
          <h2 style={{ fontSize: '0.9375rem', fontWeight: 700, color: 'var(--text)' }}>Personal Information</h2>
          {!editing && (
            <button onClick={() => { setEditing(true); setError(''); }} className="btn btn-ghost btn-sm" style={{ color: 'var(--blue)' }}>
              <Edit2 size={14} /> Edit
            </button>
          )}
        </div>

        {editing ? (
          <form onSubmit={handleSave}>
            <div className="form-group">
              <label className="label" htmlFor="profile-name">Full Name</label>
              <input id="profile-name" type="text" className="input"
                value={name} onChange={e => setName(e.target.value)}
                placeholder="Your full name" autoFocus />
            </div>
            <div className="flex gap-2">
              <button type="submit" disabled={saving} className="btn btn-primary btn-sm">
                {saving ? 'Saving…' : 'Save Changes'}
              </button>
              <button type="button" onClick={() => { setEditing(false); setError(''); setName(displayName !== '—' ? displayName : ''); }}
                className="btn btn-secondary btn-sm">
                Cancel
              </button>
            </div>
          </form>
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
            {[
              { icon: <User size={16} />, label: 'Full Name', value: displayName },
              { icon: <Mail size={16} />, label: 'Email', value: email },
            ].map(({ icon, label, value }) => (
              <div key={label} className="flex items-start gap-3">
                <div style={{ color: 'var(--text-faint)', marginTop: 2, flexShrink: 0 }}>{icon}</div>
                <div>
                  <p style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--text-muted)', marginBottom: '0.1rem' }}>{label}</p>
                  <p style={{ fontSize: '0.9375rem', color: 'var(--text)' }}>{value}</p>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Account Info */}
      <div className="card mb-6">
        <h2 style={{ fontSize: '0.9375rem', fontWeight: 700, color: 'var(--text)', marginBottom: '1.1rem' }}>Account Information</h2>
        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.875rem' }}>
          {[
            { icon: <Shield size={16} />, label: 'Sign-in method', value: provider },
            { icon: <CheckCircle2 size={16} />, label: 'Account created', value: createdAt },
          ].map(({ icon, label, value }) => (
            <div key={label} className="flex items-start gap-3">
              <div style={{ color: 'var(--text-faint)', marginTop: 2, flexShrink: 0 }}>{icon}</div>
              <div>
                <p style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--text-muted)', marginBottom: '0.1rem' }}>{label}</p>
                <p style={{ fontSize: '0.9375rem', color: 'var(--text)' }}>{value}</p>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Sign Out */}
      <button onClick={handleLogout} className="btn btn-danger btn-full" id="profile-logout-btn">
        <LogOut size={16} /> Sign Out
      </button>
    </div>
  );
};

export default ProfilePage;
