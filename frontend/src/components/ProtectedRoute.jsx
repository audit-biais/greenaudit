import { Navigate } from 'react-router-dom';
import { useAuth } from '../api/auth';

export default function ProtectedRoute({ children }) {
  const { partner, loading } = useAuth();

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-gray-500">Chargement...</div>
      </div>
    );
  }

  if (!partner) {
    return <Navigate to="/login" replace />;
  }

  return children;
}
