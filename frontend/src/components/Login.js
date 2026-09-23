import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Shield, Eye, EyeOff, AlertCircle } from 'lucide-react';
import { useAuth } from '../context/AuthContext';

const GoogleIcon = () => (
  <svg width="18" height="18" viewBox="0 0 18 18" fill="none">
    <path d="M17.64 9.2c0-.637-.057-1.251-.164-1.84H9v3.481h4.844c-.209 1.125-.843 2.078-1.796 2.717v2.258h2.908C16.46 14.013 17.64 11.804 17.64 9.2z" fill="#4285F4"/>
    <path d="M9 18c2.43 0 4.467-.806 5.956-2.184l-2.908-2.258c-.806.54-1.837.86-3.048.86-2.344 0-4.328-1.584-5.036-3.711H.957v2.332C2.438 15.983 5.482 18 9 18z" fill="#34A853"/>
    <path d="M3.964 10.707A5.41 5.41 0 013.682 9c0-.593.102-1.17.282-1.707V4.961H.957A8.996 8.996 0 000 9c0 1.452.348 2.827.957 4.039l3.007-2.332z" fill="#FBBC05"/>
    <path d="M9 3.58c1.321 0 2.508.454 3.44 1.345l2.582-2.58C13.463.891 11.426 0 9 0 5.482 0 2.438 2.017.957 4.961L3.964 6.293C4.672 4.166 6.656 3.58 9 3.58z" fill="#EA4335"/>
  </svg>
);

export default function Login() {
  const { login, googleLogin } = useAuth();
  const navigate = useNavigate();

  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [showPw, setShowPw] = useState(false);
  const [loading, setLoading] = useState(false);
  const [gLoading, setGLoading] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!email || !password) { setError('Please fill in all fields.'); return; }
    setLoading(true); setError('');
    try {
      await login(email, password);
      navigate('/dashboard', { replace: true });
    } catch (err) {
      setError(err.message || 'Sign in failed. Please check your credentials.');
    } finally { setLoading(false); }
  };

  const handleGoogle = async () => {
    setGLoading(true); setError('');
    try {
      await googleLogin();
      navigate('/dashboard', { replace: true });
    } catch (err) {
      if (err.code !== 'auth/popup-closed-by-user') setError(err.message || 'Google sign-in failed.');
    } finally { setGLoading(false); }
  };

  return (
    <div className="auth-page">
      <div className="auth-card">
        {/* Logo */}
        <div className="flex items-center gap-2 mb-8" style={{ justifyContent: 'center' }}>
          <div style={{ width: 36, height: 36, background: 'var(--blue)', borderRadius: 'var(--r-md)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
            <Shield size={20} strokeWidth={2.5} color="#fff" />
          </div>
          <span style={{ fontWeight: 800, fontSize: '1.15rem', color: 'var(--text)', letterSpacing: '-0.01em' }}>TruthLens</span>
        </div>

        <h1 style={{ fontSize: '1.5rem', fontWeight: 700, color: 'var(--text)', marginBottom: '0.35rem', textAlign: 'center' }}>
          Welcome back
        </h1>
        <p style={{ fontSize: '0.9rem', color: 'var(--text-muted)', textAlign: 'center', marginBottom: '1.75rem' }}>
          Sign in to continue to TruthLens.
        </p>

        {error && (
          <div className="alert alert-error mb-4" role="alert">
            <AlertCircle size={16} style={{ flexShrink: 0, marginTop: 1 }} />
            <span>{error}</span>
          </div>
        )}

        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label className="label" htmlFor="login-email">Email</label>
            <input
              id="login-email" type="email" className="input"
              placeholder="you@example.com"
              value={email} onChange={e => setEmail(e.target.value)}
              autoComplete="email" required
            />
          </div>

          <div className="form-group">
            <label className="label" htmlFor="login-password">Password</label>
            <div style={{ position: 'relative' }}>
              <input
                id="login-password" type={showPw ? 'text' : 'password'} className="input"
                placeholder="Your password"
                value={password} onChange={e => setPassword(e.target.value)}
                autoComplete="current-password" required
                style={{ paddingRight: '2.75rem' }}
              />
              <button type="button" onClick={() => setShowPw(s => !s)}
                style={{ position: 'absolute', right: '0.75rem', top: '50%', transform: 'translateY(-50%)', background: 'none', border: 'none', cursor: 'pointer', color: 'var(--text-faint)', display: 'flex', alignItems: 'center' }}
                aria-label={showPw ? 'Hide password' : 'Show password'}
              >
                {showPw ? <EyeOff size={17} /> : <Eye size={17} />}
              </button>
            </div>
            <div style={{ marginTop: '0.4rem', textAlign: 'right' }}>
              <span style={{ fontSize: '0.8125rem', color: 'var(--blue)', cursor: 'pointer' }}>Forgot password?</span>
            </div>
          </div>

          <button type="submit" className="btn btn-primary btn-full btn-lg mb-3" disabled={loading}>
            {loading ? (
              <span className="flex items-center gap-2">
                <span className="spinner" style={{ width: 17, height: 17 }} />
                Signing in…
              </span>
            ) : 'Sign In'}
          </button>
        </form>

        <div className="divider-text mb-3">or</div>

        <button onClick={handleGoogle} className="btn-google mb-4" disabled={gLoading}>
          {gLoading ? <span className="spinner" style={{ width: 17, height: 17 }} /> : <GoogleIcon />}
          Continue with Google
        </button>

        <p style={{ textAlign: 'center', fontSize: '0.875rem', color: 'var(--text-muted)' }}>
          Don't have an account?{' '}
          <Link to="/signup" style={{ color: 'var(--blue)', fontWeight: 600, textDecoration: 'none' }}>
            Create account
          </Link>
        </p>
      </div>
    </div>
  );
}
