import React, { useState, useCallback } from 'react';
import {
  BrowserRouter as Router,
  Routes, Route, Navigate, useLocation,
} from 'react-router-dom';
import { AuthProvider, useAuth } from './context/AuthContext';

import Login        from './components/Login';
import Register     from './components/Register';
import AppShell     from './components/AppShell';
import DashboardPage   from './components/DashboardPage';
import NewAnalysisPage from './components/NewAnalysisPage';
import ResultPage      from './components/ResultPage';
import HistoryPage     from './components/HistoryPage';
import ProfilePage     from './components/ProfilePage';
import HelpReportingPage from './components/HelpReportingPage';
import LandingPage       from './components/LandingPage';

import './App.css';

// ── Toast System ──────────────────────────────────────────
function ToastContainer({ toasts, onRemove }) {
  return (
    <div className="toast-container">
      {toasts.map(t => (
        <div key={t.id} className={`toast toast-${t.type || 'info'}`}>
          <div className="toast-message">{t.message}</div>
          <button className="toast-close" onClick={() => onRemove(t.id)} aria-label="Dismiss">×</button>
        </div>
      ))}
    </div>
  );
}

function useToast() {
  const [toasts, setToasts] = useState([]);
  const add = useCallback((message, type = 'info') => {
    const id = Date.now();
    setToasts(prev => [...prev, { id, message, type }]);
    setTimeout(() => setToasts(prev => prev.filter(t => t.id !== id)), 4500);
  }, []);
  const remove = useCallback(id => setToasts(prev => prev.filter(t => t.id !== id)), []);
  return { toasts, add, remove };
}

// ── Route Guards ──────────────────────────────────────────
const ProtectedRoute = ({ children }) => {
  const { user, loading } = useAuth();
  const location = useLocation();

  if (loading) {
    return (
      <div style={{
        minHeight: '100vh', display: 'flex', flexDirection: 'column',
        alignItems: 'center', justifyContent: 'center',
        background: 'var(--bg)', gap: '1rem',
      }}>
        <div className="spinner" style={{ width: 36, height: 36, borderTopColor: 'var(--blue)' }} />
        <span style={{ fontSize: '0.9rem', color: 'var(--text-muted)' }}>Loading TruthLens…</span>
      </div>
    );
  }

  if (!user) return <Navigate to="/login" state={{ from: location }} replace />;
  return children;
};

const PublicOnlyRoute = ({ children }) => {
  const { user, loading } = useAuth();
  if (loading) return null;
  if (user) return <Navigate to="/dashboard" replace />;
  return children;
};

// ── App Shell Wrapper ─────────────────────────────────────
function AppShellWrapper({ children, onToast, sessionAnalyses, setSessionAnalyses }) {
  const { user, userProfile, logout } = useAuth();

  const displayName = userProfile?.name || user?.displayName || user?.email?.split('@')[0] || 'User';

  const handleLogout = async () => {
    try {
      await logout();
    } catch (err) {
      onToast?.('Sign out failed. Please try again.', 'error');
    }
  };

  return (
    <AppShell username={displayName} onLogout={handleLogout}>
      {React.cloneElement(children, {
        onAnalysisComplete: () => setSessionAnalyses(n => n + 1),
        sessionAnalyses,
        onLogout: handleLogout,
      })}
    </AppShell>
  );
}

// ── Root ──────────────────────────────────────────────────
function AppRoutes() {
  const { toasts, add: toast, remove } = useToast();
  const [sessionAnalyses, setSessionAnalyses] = useState(0);

  return (
    <>
      <Routes>
        {/* Public landing / home page */}
        <Route path="/" element={<LandingPage />} />

        {/* Public auth pages */}
        <Route path="/login"  element={<PublicOnlyRoute><Login /></PublicOnlyRoute>} />
        <Route path="/signup" element={<PublicOnlyRoute><Register /></PublicOnlyRoute>} />
        {/* Backward compat */}
        <Route path="/register" element={<Navigate to="/signup" replace />} />

        {/* Protected pages */}
        <Route path="/dashboard" element={
          <ProtectedRoute>
            <AppShellWrapper onToast={toast} sessionAnalyses={sessionAnalyses} setSessionAnalyses={setSessionAnalyses}>
              <DashboardPage />
            </AppShellWrapper>
          </ProtectedRoute>
        } />

        <Route path="/analyze" element={
          <ProtectedRoute>
            <AppShellWrapper onToast={toast} sessionAnalyses={sessionAnalyses} setSessionAnalyses={setSessionAnalyses}>
              <NewAnalysisPage />
            </AppShellWrapper>
          </ProtectedRoute>
        } />
        {/* Backward compat */}
        <Route path="/new-analysis" element={<Navigate to="/analyze" replace />} />

        <Route path="/history" element={
          <ProtectedRoute>
            <AppShellWrapper onToast={toast} sessionAnalyses={sessionAnalyses} setSessionAnalyses={setSessionAnalyses}>
              <HistoryPage />
            </AppShellWrapper>
          </ProtectedRoute>
        } />

        <Route path="/history/:caseId" element={
          <ProtectedRoute>
            <AppShellWrapper onToast={toast} sessionAnalyses={sessionAnalyses} setSessionAnalyses={setSessionAnalyses}>
              <ResultPage />
            </AppShellWrapper>
          </ProtectedRoute>
        } />

        {/* /result/:caseId as alias for /history/:caseId */}
                {/* /case/:caseId as alias for case details */}
        <Route path="/case/:caseId" element={
          <ProtectedRoute>
            <AppShellWrapper onToast={toast} sessionAnalyses={sessionAnalyses} setSessionAnalyses={setSessionAnalyses}>
              <ResultPage />
            </AppShellWrapper>
          </ProtectedRoute>
        } />

        <Route path="/result/:caseId" element={
          <ProtectedRoute>
            <AppShellWrapper onToast={toast} sessionAnalyses={sessionAnalyses} setSessionAnalyses={setSessionAnalyses}>
              <ResultPage />
            </AppShellWrapper>
          </ProtectedRoute>
        } />

        <Route path="/profile" element={
          <ProtectedRoute>
            <AppShellWrapper onToast={toast} sessionAnalyses={sessionAnalyses} setSessionAnalyses={setSessionAnalyses}>
              <ProfilePage />
            </AppShellWrapper>
          </ProtectedRoute>
        } />

        <Route path="/api-keys" element={<Navigate to="/dashboard" replace />} />
        <Route path="/keys" element={<Navigate to="/dashboard" replace />} />

        <Route path="/help-reporting" element={
          <ProtectedRoute>
            <AppShellWrapper onToast={toast} sessionAnalyses={sessionAnalyses} setSessionAnalyses={setSessionAnalyses}>
              <HelpReportingPage />
            </AppShellWrapper>
          </ProtectedRoute>
        } />
        <Route path="/reporting" element={<Navigate to="/help-reporting" replace />} />

        {/* Catch-all */}
        <Route path="*" element={<Navigate to="/dashboard" replace />} />
      </Routes>

      <ToastContainer toasts={toasts} onRemove={remove} />
    </>
  );
}

export default function App() {
  return (
    <AuthProvider>
      <Router>
        <AppRoutes />
      </Router>
    </AuthProvider>
  );
}
