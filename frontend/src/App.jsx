import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider } from './api/auth';
import ProtectedRoute from './components/ProtectedRoute';
import Layout from './components/Layout';
import Login from './pages/Login';
import Dashboard from './pages/Dashboard';
import NewAudit from './pages/NewAudit';
import ClaimForm from './pages/ClaimForm';
import AuditResults from './pages/AuditResults';
import Settings from './pages/Settings';

function ProtectedPage({ children }) {
  return (
    <ProtectedRoute>
      <Layout>{children}</Layout>
    </ProtectedRoute>
  );
}

export default function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <Routes>
          <Route path="/login" element={<Login />} />
          <Route path="/" element={<ProtectedPage><Dashboard /></ProtectedPage>} />
          <Route path="/audits/new" element={<ProtectedPage><NewAudit /></ProtectedPage>} />
          <Route path="/audits/:auditId/claims" element={<ProtectedPage><ClaimForm /></ProtectedPage>} />
          <Route path="/audits/:auditId/results" element={<ProtectedPage><AuditResults /></ProtectedPage>} />
          <Route path="/settings" element={<ProtectedPage><Settings /></ProtectedPage>} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </AuthProvider>
    </BrowserRouter>
  );
}
