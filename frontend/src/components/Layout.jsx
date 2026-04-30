import { Link, useLocation } from 'react-router-dom';
import { useAuth } from '../api/auth';
import UpgradeModal from './UpgradeModal';

const NAV_ITEMS = [
  { path: '/', label: 'Dashboard' },
  { path: '/scan', label: 'Analyse' },
  { path: '/faq', label: 'Aide' },
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
          <div className="flex items-center justify-between h-32">

            {/* Logo */}
            <div className="flex items-center gap-8">
              <Link to="/landing" className="flex items-center gap-2 flex-shrink-0">
                <img src="/logo.png" alt="GreenAudit" className="h-28 w-auto object-contain" />
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
              {user?.is_superadmin && (
                <span className="hidden sm:block text-xs font-semibold px-2 py-1 rounded-full bg-purple-100 text-purple-700">SuperAdmin</span>
              )}
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
      <UpgradeModal />
    </div>
  );
}
