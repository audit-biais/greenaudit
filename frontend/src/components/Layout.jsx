import { Link, useLocation } from 'react-router-dom';
import { useAuth } from '../api/auth';

const NAV_ITEMS = [
  { path: '/', label: 'Dashboard' },
  { path: '/settings', label: 'Paramètres' },
];

export default function Layout({ children }) {
  const { partner, logout } = useAuth();
  const location = useLocation();

  return (
    <div className="min-h-screen bg-gray-50">
      <nav className="bg-green-800 text-white shadow-lg">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <div className="flex items-center gap-8">
              <Link to="/" className="text-xl font-bold tracking-tight">
                GreenAudit
              </Link>
              <div className="hidden md:flex gap-1">
                {NAV_ITEMS.map((item) => (
                  <Link
                    key={item.path}
                    to={item.path}
                    className={`px-3 py-2 rounded-md text-sm font-medium transition-colors ${
                      location.pathname === item.path
                        ? 'bg-green-900 text-white'
                        : 'text-green-100 hover:bg-green-700'
                    }`}
                  >
                    {item.label}
                  </Link>
                ))}
              </div>
            </div>
            <div className="flex items-center gap-4">
              <span className="text-sm text-green-200">{partner?.company_name}</span>
              <button
                onClick={logout}
                className="text-sm text-green-200 hover:text-white transition-colors"
              >
                Déconnexion
              </button>
            </div>
          </div>
        </div>
      </nav>
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {children}
      </main>
    </div>
  );
}
