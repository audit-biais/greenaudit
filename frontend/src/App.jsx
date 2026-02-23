import { Component } from 'react';
import { BrowserRouter, Routes, Route, Navigate, useLocation } from 'react-router-dom';
import { AuthProvider, useAuth } from './api/auth';
import ProtectedRoute from './components/ProtectedRoute';
import Layout from './components/Layout';
import Landing from './pages/Landing';
import Login from './pages/Login';
import Dashboard from './pages/Dashboard';
import NewAudit from './pages/NewAudit';
import ClaimForm from './pages/ClaimForm';
import AuditResults from './pages/AuditResults';
import Settings from './pages/Settings';

class ErrorBoundary extends Component {
  constructor(props) {
    super(props);
    this.state = { error: null };
  }
  static getDerivedStateFromError(error) {
    return { error };
  }
  render() {
    if (this.state.error) {
      return (
        <div className="min-h-screen flex items-center justify-center bg-gray-50">
          <div className="bg-white p-8 rounded-xl shadow max-w-lg text-center">
            <h2 className="text-xl font-bold text-red-700 mb-2">Erreur</h2>
            <p className="text-gray-600 mb-4">{this.state.error.message}</p>
            <button
              onClick={() => { this.setState({ error: null }); window.location.href = '/'; }}
              className="px-4 py-2 bg-green-700 text-white rounded-lg"
            >
              Retour au dashboard
            </button>
          </div>
        </div>
      );
    }
    return this.props.children;
  }
}

function ProtectedPage({ children }) {
  return (
    <ProtectedRoute>
      <Layout>{children}</Layout>
    </ProtectedRoute>
  );
}

function HomeRoute() {
  const { partner, loading } = useAuth();
  if (loading) return (
    <div className="min-h-screen flex items-center justify-center">
      <div className="text-gray-400">Chargement...</div>
    </div>
  );
  if (partner) return <Navigate to="/dashboard" replace />;
  return <Landing />;
}

function AppRoutes() {
  const location = useLocation();

  return (
    <Routes key={location.pathname}>
      <Route path="/" element={<HomeRoute />} />
      <Route path="/login" element={<Login />} />
      <Route path="/dashboard" element={<ProtectedPage><Dashboard /></ProtectedPage>} />
      <Route path="/audits/new" element={<ProtectedPage><NewAudit /></ProtectedPage>} />
      <Route path="/audits/:auditId" element={<ProtectedPage><ClaimForm /></ProtectedPage>} />
      <Route path="/audits/:auditId/claims" element={<ProtectedPage><ClaimForm /></ProtectedPage>} />
      <Route path="/audits/:auditId/results" element={<ProtectedPage><AuditResults /></ProtectedPage>} />
      <Route path="/settings" element={<ProtectedPage><Settings /></ProtectedPage>} />
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}

export default function App() {
  return (
    <ErrorBoundary>
      <BrowserRouter>
        <AuthProvider>
          <AppRoutes />
        </AuthProvider>
      </BrowserRouter>
    </ErrorBoundary>
  );
}
