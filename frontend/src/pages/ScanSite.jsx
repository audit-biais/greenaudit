import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import api from '../api/client';
import { useAuth } from '../api/auth';

const SECTORS = [
  { value: 'e-commerce', label: 'E-commerce' },
  { value: 'cosmetiques', label: 'Cosmétiques' },
  { value: 'alimentaire', label: 'Alimentaire' },
  { value: 'textile', label: 'Textile' },
  { value: 'services', label: 'Services' },
  { value: 'energie', label: 'Énergie' },
  { value: 'autre', label: 'Autre' },
];

const RISK_COLORS = {
  faible: 'text-green-700 bg-green-50 border-green-200',
  modere: 'text-yellow-700 bg-yellow-50 border-yellow-200',
  eleve: 'text-orange-700 bg-orange-50 border-orange-200',
  critique: 'text-red-700 bg-red-50 border-red-200',
};

const VERDICT_COLORS = {
  conforme: 'bg-green-100 text-green-800',
  risque: 'bg-yellow-100 text-yellow-800',
  non_conforme: 'bg-red-100 text-red-800',
};

const VERDICT_LABELS = {
  conforme: 'Conforme',
  risque: 'Risque',
  non_conforme: 'Non conforme',
};

export default function ScanSite() {
  const navigate = useNavigate();
  const { user } = useAuth();
  const isPro = ['partner', 'pro', 'enterprise'].includes(user?.subscription_plan);

  const [url, setUrl] = useState('');
  const [companyName, setCompanyName] = useState('');
  const [sector, setSector] = useState('autre');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [results, setResults] = useState(null);
  const [step, setStep] = useState('form'); // form, scanning, results
  const [upgradeLoading, setUpgradeLoading] = useState(false);

  const handleUpgradePartner = async () => {
    setUpgradeLoading(true);
    try {
      const res = await api.post('/payment/create-checkout-partner');
      window.location.href = res.data.checkout_url;
    } catch {
      alert('Erreur lors de la redirection. Réessayez.');
      setUpgradeLoading(false);
    }
  };

  const handleScan = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);
    setStep('scanning');

    try {
      const { data } = await api.post('/audits/scan', {
        url,
        company_name: companyName,
        sector,
      });
      setResults(data);
      setStep('results');
    } catch (err) {
      if (err.response?.status === 402) {
        setStep('limit');
      } else {
        const detail = err.response?.data?.detail || 'Erreur lors du scan';
        setError(detail);
        setStep('form');
      }
    } finally {
      setLoading(false);
    }
  };

  if (step === 'scanning') {
    return (
      <div className="max-w-2xl mx-auto">
        <div className="bg-white rounded-xl shadow p-12 text-center">
          <div className="animate-spin w-12 h-12 border-4 border-green-200 border-t-green-700 rounded-full mx-auto mb-6" />
          <h2 className="text-xl font-bold text-gray-800 mb-2">Analyse en cours...</h2>
          <p className="text-gray-500 mb-1">Scan du site : {url}</p>
          <p className="text-gray-400 text-sm">
            Extraction des allégations environnementales et analyse de conformité EmpCo.
            Cela peut prendre 30 à 60 secondes.
          </p>
        </div>
      </div>
    );
  }

  if (step === 'limit') {
    return (
      <div className="max-w-2xl mx-auto">
        <div className="bg-white rounded-xl shadow p-12 text-center">
          <div className="text-4xl mb-4">🔒</div>
          <h2 className="text-xl font-bold text-gray-800 mb-2">Limite de 5 scans atteinte</h2>
          <p className="text-gray-500 mb-6">
            Le plan Starter inclut 5 scans gratuits. Passez au plan Partner pour des scans illimités et l'accès à l'analyse complète avec rapport PDF.
          </p>
          <div className="flex flex-col sm:flex-row gap-3 justify-center">
            <button
              onClick={handleUpgradePartner}
              disabled={upgradeLoading}
              className="px-6 py-3 bg-[#1a5c3a] text-white font-semibold rounded-full hover:bg-[#14472d] disabled:opacity-50 transition-colors"
            >
              {upgradeLoading ? 'Redirection...' : 'Passer au plan Partner — 990€/mois'}
            </button>
            <button
              onClick={() => setStep('form')}
              className="px-6 py-3 border border-gray-300 text-gray-700 font-medium rounded-full hover:bg-gray-50 transition-colors"
            >
              Retour
            </button>
          </div>
        </div>
      </div>
    );
  }

  if (step === 'results' && results) {
    return (
      <div className="max-w-4xl mx-auto">
        <div className="flex items-center justify-between mb-6">
          <h1 className="text-2xl font-bold text-gray-800">Résultats du scan</h1>
          <div className="flex gap-3">
            <button
              onClick={() => { setStep('form'); setResults(null); setUrl(''); setCompanyName(''); }}
              className="px-4 py-2 text-sm border border-gray-300 rounded-lg hover:bg-gray-50"
            >
              Nouveau scan
            </button>
            {isPro ? (
              <button
                onClick={() => navigate(`/audits/${results.audit_id}/claims`)}
                className="px-4 py-2 text-sm bg-[#1a5c3a] text-white rounded-lg hover:bg-[#15803d]"
              >
                Compléter et analyser →
              </button>
            ) : (
              <button
                onClick={handleUpgradePartner}
                disabled={upgradeLoading}
                className="px-4 py-2 text-sm bg-[#1a5c3a] text-white rounded-lg hover:bg-[#15803d] disabled:opacity-50"
              >
                {upgradeLoading ? 'Redirection...' : 'Obtenir le rapport complet →'}
              </button>
            )}
          </div>
        </div>

        {/* Bandeau informatif */}
        <div className="bg-[#eff6ff] border border-blue-200 rounded-xl px-4 py-3 mb-5 flex items-start gap-3">
          <svg className="h-5 w-5 text-blue-500 shrink-0 mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          <p className="text-sm text-blue-800">
            <span className="font-semibold">Scan terminé.</span> Certaines allégations ont pu être manquées (images, PDFs, pages non standard).
            Cliquez sur <strong>Compléter et analyser</strong> pour ajouter des allégations manuellement avant de générer le rapport final.
          </p>
        </div>

        {/* Score global */}
        <div className={`rounded-xl border-2 p-6 mb-6 ${RISK_COLORS[results.risk_level] || 'border-gray-200'}`}>
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-lg font-semibold">{results.company_name}</h2>
              <p className="text-sm opacity-75">{results.website_url}</p>
            </div>
            <div className="text-right">
              <div className="text-3xl font-bold">{results.global_score?.toFixed(0)}/100</div>
              <div className="text-sm font-medium capitalize">Risque {results.risk_level}</div>
            </div>
          </div>
          <p className="mt-3 text-xs opacity-60 italic">Score provisoire — sera recalculé après analyse complète des preuves et labels.</p>
          <div className="flex gap-6 mt-4 text-sm">
            <span className="flex items-center gap-1.5">
              <span className="w-3 h-3 rounded-full bg-green-500 inline-block" />
              {results.conforming_claims} conforme{results.conforming_claims > 1 ? 's' : ''}
            </span>
            <span className="flex items-center gap-1.5">
              <span className="w-3 h-3 rounded-full bg-yellow-500 inline-block" />
              {results.at_risk_claims} à risque
            </span>
            <span className="flex items-center gap-1.5">
              <span className="w-3 h-3 rounded-full bg-red-500 inline-block" />
              {results.non_conforming_claims} non conforme{results.non_conforming_claims > 1 ? 's' : ''}
            </span>
          </div>
        </div>

        {/* Claims détectées */}
        <h3 className="text-lg font-semibold text-gray-800 mb-3">
          {results.total_claims} allégation{results.total_claims > 1 ? 's' : ''} détectée{results.total_claims > 1 ? 's' : ''}
        </h3>
        <div className="space-y-3">
          {results.claims?.map((claim, i) => (
            <div key={claim.id || i} className="bg-white rounded-lg shadow p-4 border-l-4"
              style={{ borderLeftColor: claim.overall_verdict === 'conforme' ? '#16a34a' : claim.overall_verdict === 'risque' ? '#ca8a04' : '#dc2626' }}
            >
              <div className="flex items-start justify-between gap-3">
                <p className="text-sm text-gray-700 flex-1">"{claim.claim_text}"</p>
                <span className={`text-xs font-medium px-2 py-1 rounded-full whitespace-nowrap ${VERDICT_COLORS[claim.overall_verdict] || 'bg-gray-100'}`}>
                  {VERDICT_LABELS[claim.overall_verdict] || claim.overall_verdict}
                </span>
              </div>
              {claim.results?.filter(r => r.verdict !== 'non_applicable').length > 0 && (
                <div className="mt-2 flex flex-wrap gap-1.5">
                  {claim.results.filter(r => r.verdict !== 'non_applicable').map((r, j) => (
                    <span key={j} className={`text-xs px-2 py-0.5 rounded ${VERDICT_COLORS[r.verdict] || 'bg-gray-100 text-gray-600'}`}>
                      {r.criterion === 'specificity' ? 'Spécificité' :
                       r.criterion === 'compensation' ? 'Neutralité carbone' :
                       r.criterion === 'labels' ? 'Labels' :
                       r.criterion === 'proportionality' ? 'Proportionnalité' :
                       r.criterion === 'future_commitment' ? 'Engagements futurs' :
                       r.criterion === 'justification' ? 'Preuves' :
                       r.criterion === 'legal_requirement' ? 'Exigences légales' :
                       r.criterion}
                    </span>
                  ))}
                </div>
              )}
            </div>
          ))}
        </div>
      </div>
    );
  }

  // Formulaire
  return (
    <div className="max-w-2xl mx-auto">
      <h1 className="text-2xl font-bold text-gray-800 mb-2">Analyse de site web</h1>
      <p className="text-gray-500 mb-8">
        Entrez l'URL d'un site pour scanner automatiquement ses allégations environnementales
        et les analyser selon la directive EmpCo (EU 2024/825).
      </p>

      <form onSubmit={handleScan} className="bg-white rounded-xl shadow p-6 space-y-5">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">URL du site</label>
          <input
            type="url"
            value={url}
            onChange={(e) => setUrl(e.target.value)}
            placeholder="https://example.com"
            required
            className="w-full px-4 py-2.5 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-green-500"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Nom de l'entreprise</label>
          <input
            type="text"
            value={companyName}
            onChange={(e) => setCompanyName(e.target.value)}
            placeholder="Ex: Les Couleurs de Jeanne"
            required
            className="w-full px-4 py-2.5 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-green-500"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Secteur</label>
          <select
            value={sector}
            onChange={(e) => setSector(e.target.value)}
            className="w-full px-4 py-2.5 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-green-500"
          >
            {SECTORS.map((s) => (
              <option key={s.value} value={s.value}>{s.label}</option>
            ))}
          </select>
        </div>

        {error && (
          <div className="p-3 bg-red-50 border border-red-200 rounded-lg text-sm text-red-700">
            {error}
          </div>
        )}

        <button
          type="submit"
          disabled={loading}
          className="w-full py-3 bg-green-700 text-white font-medium rounded-lg hover:bg-green-800 disabled:opacity-50 transition-colors"
        >
          Lancer l'analyse
        </button>

        <p className="text-xs text-gray-400 text-center">
          Le scan extrait automatiquement les allégations environnementales du site
          et les analyse selon les 7 critères de la directive EmpCo.
        </p>
      </form>
    </div>
  );
}
