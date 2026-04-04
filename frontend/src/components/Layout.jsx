import { Link, useLocation } from 'react-router-dom';
import { useAuth } from '../api/auth';

const NAV_ITEMS = [
  { path: '/', label: 'Dashboard' },
  { path: '/scan', label: 'Analyse' },
  { path: '/settings', label: 'Paramètres' },
];

export default function Layout({ children }) {
  const { user, logout } = useAuth();
  const location = useLocation();

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Navbar — style One Click LCA */}
      <nav className="bg-white border-b border-gray-100 sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-6">
          <div className="flex items-center justify-between h-16">

            {/* Logo */}
            <div className="flex items-center gap-8">
              <Link to="/landing" className="flex items-center gap-2 flex-shrink-0">
                <div className="h-8 w-8 rounded-lg flex items-center justify-center bg-[#1a5c3a]">
                  <svg className="h-4 w-4 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                      d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
                  </svg>
                </div>
                <span className="text-base font-bold text-[#1a5c3a]" translate="no">GreenAudit</span>
              </Link>

              {/* Nav links */}
              <div className="hidden md:flex items-center gap-1">
                {NAV_ITEMS.map((item) => (
                  <Link
                    key={item.path}
                    to={item.path}
                    className={`px-4 py-2 rounded-full text-sm font-medium transition-colors ${
                      location.pathname === item.path
                        ? 'bg-[#eaf4ee] text-[#1a5c3a]'
                        : 'text-gray-600 hover:text-gray-900'
                    }`}
                  >
                    {item.label}
                  </Link>
                ))}
                {user?.is_superadmin && (
                  <Link
                    to="/admin"
                    className={`px-4 py-2 rounded-full text-sm font-medium transition-colors ${
                      location.pathname === '/admin'
                        ? 'bg-purple-100 text-purple-700'
                        : 'text-purple-600 hover:text-purple-900'
                    }`}
                  >
                    Admin
                  </Link>
                )}
              </div>
            </div>

            {/* Right side */}
            <div className="flex items-center gap-4">
              <span className="hidden sm:block text-sm text-gray-500">{user?.organization?.name || user?.company_name}</span>
              <button
                onClick={logout}
                className="text-sm font-medium text-gray-600 hover:text-gray-900 transition-colors"
              >
                Déconnexion
              </button>
            </div>
          </div>
        </div>
      </nav>

      <main className="max-w-7xl mx-auto px-6 py-8" key={location.pathname}>
        {children}
      </main>
    </div>
  );
}
