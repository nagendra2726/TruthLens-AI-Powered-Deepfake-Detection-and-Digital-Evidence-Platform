import React, { useState, useEffect } from 'react';
import { NavLink, useNavigate, useLocation } from 'react-router-dom';
import { Shield, LayoutDashboard, Scan, Clock, User, LogOut, Menu, X, ChevronDown, HelpCircle } from 'lucide-react';

const AppShell = ({ children, onLogout, username = 'User' }) => {
  const [mobileOpen, setMobileOpen] = useState(false);
  const [profileOpen, setProfileOpen] = useState(false);
  const navigate = useNavigate();
  const location = useLocation();

  useEffect(() => { setMobileOpen(false); setProfileOpen(false); }, [location.pathname]);

  useEffect(() => {
    if (!profileOpen) return;
    const close = () => setProfileOpen(false);
    document.addEventListener('click', close);
    return () => document.removeEventListener('click', close);
  }, [profileOpen]);

  const navLinks = [
    { to: '/dashboard', label: 'Dashboard', icon: <LayoutDashboard size={16} /> },
    { to: '/analyze',   label: 'Analyze',   icon: <Scan size={16} /> },
    { to: '/history',   label: 'History',   icon: <Clock size={16} /> },
    { to: '/help-reporting', label: 'Help & Reporting', icon: <HelpCircle size={16} /> },
  ];

  const initial = username ? username.charAt(0).toUpperCase() : 'U';

  return (
    <div style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column', background: 'var(--bg)' }}>

      {/* ── Header ─────────────────────────────────────── */}
      <header style={{
        height: 'var(--nav-h)',
        background: 'rgba(255,255,255,0.95)',
        backdropFilter: 'blur(12px)',
        borderBottom: '1px solid var(--border)',
        boxShadow: 'var(--shadow-sm)',
        position: 'sticky', top: 0, zIndex: 100,
      }}>
        <div style={{
          display: 'flex', alignItems: 'center', justifyContent: 'space-between',
          height: '100%', maxWidth: 'var(--max-w)', margin: '0 auto', padding: '0 1.5rem',
        }}>

          {/* Brand */}
          <div
            onClick={() => navigate('/dashboard')}
            style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', cursor: 'pointer' }}
          >
            <div style={{
              width: 32, height: 32,
              background: 'var(--blue)',
              borderRadius: 'var(--r-md)',
              display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#fff',
            }}>
              <Shield size={17} strokeWidth={2.5} />
            </div>
            <span style={{ fontWeight: 800, fontSize: '1.05rem', color: 'var(--text)', letterSpacing: '-0.01em' }}>
              TruthLens
            </span>
          </div>

          {/* Desktop Nav */}
          <nav className="desktop-only" style={{ display: 'flex', alignItems: 'center', gap: '0.25rem' }}>
            {navLinks.map(({ to, label, icon }) => {
              const active = location.pathname.startsWith(to);
              return (
                <NavLink
                  key={to} to={to}
                  style={{
                    display: 'inline-flex', alignItems: 'center', gap: '0.4rem',
                    padding: '0.42rem 0.85rem',
                    borderRadius: 'var(--r-md)',
                    fontSize: '0.875rem', fontWeight: active ? 600 : 500,
                    textDecoration: 'none',
                    color: active ? 'var(--blue)' : 'var(--text-muted)',
                    background: active ? 'var(--bg-soft-blue)' : 'transparent',
                    transition: 'all var(--t-fast)',
                  }}
                >
                  {icon} {label}
                </NavLink>
              );
            })}
          </nav>

          {/* Right */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            {/* Profile dropdown */}
            <div style={{ position: 'relative' }}>
              <button
                onClick={e => { e.stopPropagation(); setProfileOpen(p => !p); }}
                className="btn btn-ghost desktop-only"
                style={{ padding: '0.35rem 0.6rem', gap: '0.5rem', display: 'inline-flex' }}
                aria-label="Account"
              >
                <div style={{
                  width: 30, height: 30, borderRadius: '50%',
                  background: 'var(--blue)', color: '#fff',
                  fontWeight: 700, fontSize: '0.8rem',
                  display: 'flex', alignItems: 'center', justifyContent: 'center',
                }}>
                  {initial}
                </div>
                <span style={{ fontSize: '0.875rem', fontWeight: 500, color: 'var(--text-2)', maxWidth: 120, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                  {username}
                </span>
                <ChevronDown size={14} style={{ color: 'var(--text-faint)', flexShrink: 0 }} />
              </button>

              {profileOpen && (
                <div style={{
                  position: 'absolute', top: 'calc(100% + 6px)', right: 0,
                  background: 'var(--bg-white)', border: '1px solid var(--border)',
                  borderRadius: 'var(--r-lg)', padding: '0.4rem',
                  minWidth: 175, boxShadow: 'var(--shadow-lg)',
                  zIndex: 200, animation: 'slideUp 0.15s ease',
                }}>
                  {[
                    { label: 'Profile', icon: <User size={14} />, action: () => navigate('/profile'), color: 'var(--text-2)' },
                  ].map(item => (
                    <button key={item.label} onClick={item.action}
                      style={{
                        display: 'flex', alignItems: 'center', gap: '0.6rem',
                        width: '100%', padding: '0.55rem 0.75rem',
                        background: 'none', border: 'none', cursor: 'pointer',
                        color: item.color, fontSize: '0.875rem', fontWeight: 500,
                        borderRadius: 'var(--r-sm)', textAlign: 'left',
                        transition: 'background var(--t-fast)',
                      }}
                      onMouseEnter={e => e.currentTarget.style.background = 'var(--bg-muted)'}
                      onMouseLeave={e => e.currentTarget.style.background = 'none'}
                    >
                      {item.icon} {item.label}
                    </button>
                  ))}
                  <hr style={{ border: 'none', borderTop: '1px solid var(--border)', margin: '0.3rem 0' }} />
                  <button onClick={onLogout}
                    style={{
                      display: 'flex', alignItems: 'center', gap: '0.6rem',
                      width: '100%', padding: '0.55rem 0.75rem',
                      background: 'none', border: 'none', cursor: 'pointer',
                      color: 'var(--danger)', fontSize: '0.875rem', fontWeight: 500,
                      borderRadius: 'var(--r-sm)', textAlign: 'left',
                      transition: 'background var(--t-fast)',
                    }}
                    onMouseEnter={e => e.currentTarget.style.background = 'var(--bg-soft-red)'}
                    onMouseLeave={e => e.currentTarget.style.background = 'none'}
                  >
                    <LogOut size={14} /> Sign out
                  </button>
                </div>
              )}
            </div>

            {/* Mobile hamburger */}
            <button
              className="mobile-only btn btn-ghost"
              onClick={() => setMobileOpen(o => !o)}
              style={{ padding: '0.45rem', display: 'none' }}
              aria-label="Menu"
            >
              {mobileOpen ? <X size={20} /> : <Menu size={20} />}
            </button>
          </div>
        </div>
      </header>

      {/* ── Mobile Nav ──────────────────────────────────── */}
      {mobileOpen && (
        <div className="mobile-only fade-in" style={{
          position: 'fixed', top: 'var(--nav-h)', left: 0, right: 0, bottom: 0,
          background: 'rgba(248,250,252,0.98)', backdropFilter: 'blur(12px)',
          zIndex: 99, padding: '1rem',
          flexDirection: 'column', gap: '0.4rem', display: 'flex',
        }}>
          {navLinks.map(({ to, label, icon }) => (
            <NavLink key={to} to={to} onClick={() => setMobileOpen(false)}
              style={({ isActive }) => ({
                display: 'flex', alignItems: 'center', gap: '0.75rem',
                padding: '0.85rem 1rem', borderRadius: 'var(--r-md)',
                fontSize: '1rem', fontWeight: 600, textDecoration: 'none',
                color: isActive ? 'var(--blue)' : 'var(--text-2)',
                background: isActive ? 'var(--bg-soft-blue)' : 'var(--bg-white)',
                border: `1px solid ${isActive ? '#BFDBFE' : 'var(--border)'}`,
              })}>
              {icon} {label}
            </NavLink>
          ))}
          <div style={{ marginTop: 'auto', display: 'flex', flexDirection: 'column', gap: '0.4rem' }}>
            <button onClick={() => { navigate('/profile'); setMobileOpen(false); }}
              className="btn btn-secondary btn-full" style={{ justifyContent: 'flex-start', fontSize: '1rem', padding: '0.85rem 1rem' }}>
              <User size={17} /> Profile
            </button>
            <button onClick={onLogout}
              className="btn btn-danger btn-full" style={{ justifyContent: 'flex-start', fontSize: '1rem', padding: '0.85rem 1rem' }}>
              <LogOut size={17} /> Sign out
            </button>
          </div>
        </div>
      )}

      {/* ── Content ─────────────────────────────────────── */}
      <main style={{ flex: 1, maxWidth: 'var(--max-w)', width: '100%', margin: '0 auto', padding: '2rem 1.5rem 5rem' }}>
        {children}
      </main>

      {/* ── Footer ──────────────────────────────────────── */}
      <footer style={{ borderTop: '1px solid var(--border)', background: 'var(--bg-white)', padding: '1.5rem', textAlign: 'center' }}>
        <p style={{ fontSize: '0.8125rem', color: 'var(--text-faint)', lineHeight: 1.6 }}>
          TruthLens © 2026 · AI-Powered Deepfake Detection & Digital Evidence Platform<br />
          <span>AI-assisted analysis. Results should be independently reviewed and should not be treated as definitive proof.</span>
        </p>
      </footer>
    </div>
  );
};

export default AppShell;
