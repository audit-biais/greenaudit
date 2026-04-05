import { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';

export default function PaymentSuccess() {
  const navigate = useNavigate();

  useEffect(() => {
    const t = setTimeout(() => navigate('/dashboard'), 5000);
    return () => clearTimeout(t);
  }, [navigate]);

  return (
    <div className="min-h-screen bg-gray-50 flex items-center justify-center px-4">
      <div className="bg-white rounded-2xl shadow-lg max-w-md w-full p-10 text-center">
        <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-[#eaf4ee] mb-5">
          <svg className="w-8 h-8 text-[#1a5c3a]" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
          </svg>
        </div>
        <h1 className="text-2xl font-bold text-gray-900 mb-2">Bienvenue sur le plan Pro</h1>
        <p className="text-gray-500 text-sm mb-6">
          Votre abonnement est actif. Toutes les fonctionnalités sont maintenant disponibles.
        </p>
        <p className="text-xs text-gray-400">Redirection automatique dans 5 secondes...</p>
        <button
          onClick={() => navigate('/dashboard')}
          className="mt-4 px-6 py-2.5 rounded-xl bg-[#1a5c3a] text-white text-sm font-semibold hover:bg-[#154d30] transition"
        >
          Aller au dashboard
        </button>
      </div>
    </div>
  );
}
