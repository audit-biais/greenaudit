import { useState, useEffect } from 'react';
import api from '../api/client';

export default function UpgradeModal() {
  const [open, setOpen] = useState(false);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    const handler = () => setOpen(true);
    window.addEventListener('upgrade_required', handler);
    return () => window.removeEventListener('upgrade_required', handler);
  }, []);

  const handleUpgrade = async () => {
    setLoading(true);
    try {
      const res = await api.post('/payment/create-checkout');
      window.location.href = res.data.checkout_url;
    } catch (err) {
      alert('Erreur lors de la création du checkout. Réessayez.');
      setLoading(false);
    }
  };

  if (!open) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 px-4">
      <div className="bg-white rounded-2xl shadow-2xl max-w-md w-full p-8">
        {/* Header */}
        <div className="text-center mb-6">
          <div className="inline-flex items-center justify-center w-14 h-14 rounded-full bg-[#eaf4ee] mb-4">
            <svg className="w-7 h-7 text-[#1a5c3a]" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
            </svg>
          </div>
          <h2 className="text-xl font-bold text-gray-900">Fonctionnalité Pro</h2>
          <p className="text-gray-500 text-sm mt-1">
            Passez au plan Pro pour débloquer cette fonctionnalité.
          </p>
        </div>

        {/* Features */}
        <div className="bg-gray-50 rounded-xl p-4 mb-6 space-y-2">
          {[
            'Analyse complète — 8 règles EmpCo',
            'Rapport PDF complet avec recommandations',
            'Evidence Vault — preuves & certifications',
            'Suggestions de réécriture conformes',
            'Monitoring continu du site web',
            '15 audits/mois inclus',
          ].map((f) => (
            <div key={f} className="flex items-center gap-2 text-sm text-gray-700">
              <svg className="w-4 h-4 text-[#1a5c3a] flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
              </svg>
              {f}
            </div>
          ))}
        </div>

        {/* Price */}
        <div className="text-center mb-6">
          <span className="text-3xl font-bold text-gray-900">2 990€</span>
          <span className="text-gray-500 text-sm">/mois · Engagement 12 mois</span>
          <p className="text-xs text-gray-400 mt-1">ROI x6,7 — rentable dès le 2e client audité</p>
        </div>

        {/* Actions */}
        <div className="space-y-3">
          <button
            onClick={handleUpgrade}
            disabled={loading}
            className="w-full py-3 rounded-xl bg-[#1a5c3a] text-white font-semibold text-sm hover:bg-[#154d30] transition disabled:opacity-60"
          >
            {loading ? 'Redirection...' : 'Passer au plan Pro'}
          </button>
          <button
            onClick={() => setOpen(false)}
            className="w-full py-3 rounded-xl bg-gray-100 text-gray-600 font-medium text-sm hover:bg-gray-200 transition"
          >
            Fermer
          </button>
        </div>
      </div>
    </div>
  );
}
