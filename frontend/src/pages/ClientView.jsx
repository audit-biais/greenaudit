import { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import axios from 'axios';

const API_BASE = import.meta.env.VITE_API_URL || 'https://greenaudit-production.up.railway.app/api';

const VERDICT_STYLES = {
  conforme: { bg: 'bg-green-50', text: 'text-green-700', label: 'Conforme', dot: 'bg-green-500' },
  non_conforme: { bg: 'bg-red-50', text: 'text-red-700', label: 'Non conforme', dot: 'bg-red-500' },
  risque: { bg: 'bg-orange-50', text: 'text-orange-700', label: 'À risque', dot: 'bg-orange-400' },
};

const RISK_COLORS = {
  faible: '#1a5c3a',
  modere: '#ca8a04',
  eleve: '#ea580c',
  critique: '#dc2626',
};

const RISK_LABELS = {
  faible: 'Faible',
  modere: 'Modéré',
  eleve: 'Élevé',
  critique: 'Critique',
};

export default function ClientView() {
  const { token } = useParams();
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [downloading, setDownloading] = useState('');

  useEffect(() => {
    axios.get(`${API_BASE}/share/${token}`)
      .then((res) => setData(res.data))
      .catch(() => setError('Ce lien est invalide ou a expiré.'))
      .finally(() => setLoading(false));
  }, [token]);

  const handleDownload = async (type) => {
    setDownloading(type);
    try {
      const res = await axios.get(`${API_BASE}/share/${token}/${type}`, { responseType: 'blob' });
      const url = window.URL.createObjectURL(res.data);
      const a = document.createElement('a');
      a.href = url;
      a.download = type === 'pdf'
        ? `rapport_greenaudit_${data.company_name}.pdf`
        : `dossier_preuves_${data.company_name}.zip`;
      a.click();
      window.URL.revokeObjectURL(url);
    } catch {
      // silently ignore
    } finally {
      setDownloading('');
    }
  };

  if (loading) return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50">
      <p className="text-gray-400 text-sm">Chargement...</p>
    </div>
  );

  if (error) return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50">
      <div className="bg-white rounded-2xl shadow p-10 max-w-md text-center">
        <p className="text-2xl mb-2">🔒</p>
        <h2 className="text-lg font-bold text-gray-800 mb-2">Lien invalide</h2>
        <p className="text-sm text-gray-500">{error}</p>
      </div>
    </div>
  );

  const { branding, claims } = data;
  const primary = branding.primary_color;
  const logoUrl = branding.has_logo ? `${API_BASE}/share/${token}/logo` : null;

  const scoreColor = data.risk_level ? RISK_COLORS[data.risk_level] : primary;

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header cabinet */}
      <header className="bg-white border-b border-gray-100">
        <div className="max-w-4xl mx-auto px-6 py-4 flex items-center justify-between">
          {logoUrl
            ? <img src={logoUrl} alt={branding.cabinet_name} className="h-10 object-contain" />
            : <span className="font-bold text-lg" style={{ color: primary }}>{branding.cabinet_name}</span>
          }
          <span className="text-xs text-gray-400">Espace client confidentiel</span>
        </div>
      </header>

      <main className="max-w-4xl mx-auto px-6 py-10 space-y-8">
        {/* Titre audit */}
        <div>
          <h1 className="text-2xl font-black text-gray-900">{data.company_name}</h1>
          <p className="text-sm text-gray-400 mt-1 capitalize">
            {data.sector}
            {data.completed_at && (
              <span className="ml-3">
                · Analysé le {new Date(data.completed_at).toLocaleDateString('fr-FR')}
              </span>
            )}
          </p>
        </div>

        {/* Score + téléchargements */}
        <div className="bg-white rounded-2xl border border-gray-100 p-6">
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-6">
            {/* Score */}
            <div className="flex items-center gap-6">
              <div className="text-center">
                <p className="text-5xl font-black" style={{ color: scoreColor }}>
                  {data.global_score ?? '—'}
                </p>
                <p className="text-xs text-gray-400 mt-1">Score /100</p>
              </div>
              {data.risk_level && (
                <div>
                  <span
                    className="px-3 py-1.5 rounded-full text-white text-sm font-semibold"
                    style={{ backgroundColor: scoreColor }}
                  >
                    Risque {RISK_LABELS[data.risk_level] || data.risk_level}
                  </span>
                  <div className="flex gap-4 mt-3 text-xs text-gray-500">
                    <span className="text-green-700 font-semibold">{data.conforming_claims} conformes</span>
                    <span className="text-orange-600 font-semibold">{data.at_risk_claims} à risque</span>
                    <span className="text-red-600 font-semibold">{data.non_conforming_claims} non conformes</span>
                  </div>
                </div>
              )}
            </div>

            {/* Boutons téléchargement */}
            <div className="flex flex-col gap-3 sm:items-end">
              {data.has_pdf && (
                <button
                  onClick={() => handleDownload('pdf')}
                  disabled={downloading === 'pdf'}
                  className="px-5 py-2.5 rounded-full text-sm font-semibold text-white transition-opacity disabled:opacity-50"
                  style={{ backgroundColor: primary }}
                >
                  {downloading === 'pdf' ? 'Téléchargement...' : 'Télécharger le rapport PDF'}
                </button>
              )}
              {data.has_evidence && (
                <button
                  onClick={() => handleDownload('zip')}
                  disabled={downloading === 'zip'}
                  className="px-5 py-2.5 rounded-full text-sm font-semibold text-gray-600 border border-gray-200 hover:bg-gray-50 transition-colors disabled:opacity-50"
                >
                  {downloading === 'zip' ? 'Téléchargement...' : 'Dossier preuves ZIP'}
                </button>
              )}
            </div>
          </div>
        </div>

        {/* Liste des allégations */}
        <div>
          <h2 className="text-xs font-semibold uppercase tracking-widest text-gray-400 mb-4">
            Allégations analysées ({claims.length})
          </h2>
          <div className="space-y-3">
            {claims.map((claim) => {
              const style = VERDICT_STYLES[claim.overall_verdict] || VERDICT_STYLES.non_conforme;
              return (
                <div
                  key={claim.id}
                  className="bg-white rounded-xl border border-gray-100 p-4 flex items-start gap-4"
                >
                  <span className={`mt-1.5 w-2.5 h-2.5 rounded-full flex-shrink-0 ${style.dot}`} />
                  <div className="flex-1 min-w-0">
                    <p className="text-sm text-gray-800">{claim.claim_text}</p>
                    <div className="flex items-center gap-3 mt-1.5">
                      <span className={`text-xs font-medium px-2 py-0.5 rounded-full ${style.bg} ${style.text}`}>
                        {style.label}
                      </span>
                      {claim.is_corrected && (
                        <span className="text-xs text-green-600 font-medium">Corrigée</span>
                      )}
                      {claim.evidence_count > 0 && (
                        <span className="text-xs text-gray-400">
                          {claim.evidence_count} preuve{claim.evidence_count > 1 ? 's' : ''}
                        </span>
                      )}
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Footer */}
        <footer className="text-center text-xs text-gray-300 pt-4 pb-8">
          <p>Rapport généré par <span style={{ color: primary }}>{branding.cabinet_name}</span> via GreenAudit</p>
          <p className="mt-1">Conformité Directive EmpCo (EU 2024/825) · Ce lien est personnel et confidentiel</p>
        </footer>
      </main>
    </div>
  );
}
