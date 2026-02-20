import { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import api from '../api/client';

const VERDICT_COLORS = {
  conforme: 'bg-green-100 text-green-800',
  non_conforme: 'bg-red-100 text-red-800',
  risque: 'bg-orange-100 text-orange-800',
  non_applicable: 'bg-gray-100 text-gray-600',
};

const VERDICT_LABELS = {
  conforme: 'Conforme',
  non_conforme: 'Non conforme',
  risque: 'Risque',
  non_applicable: 'N/A',
};

const RISK_COLORS = {
  faible: 'bg-green-500',
  modere: 'bg-yellow-500',
  eleve: 'bg-orange-500',
  critique: 'bg-red-600',
};

const CRITERION_LABELS = {
  specificity: 'Spécificité',
  compensation: 'Neutralité carbone',
  labels: 'Labels',
  proportionality: 'Proportionnalité',
  future_commitment: 'Engagements futurs',
  justification: 'Justification / Preuves',
};

function VerdictBadge({ verdict }) {
  return (
    <span className={`px-2 py-0.5 rounded text-xs font-medium ${VERDICT_COLORS[verdict] || VERDICT_COLORS.non_applicable}`}>
      {VERDICT_LABELS[verdict] || verdict}
    </span>
  );
}

export default function AuditResults() {
  const { auditId } = useParams();
  const [results, setResults] = useState(null);
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);
  const [reportInfo, setReportInfo] = useState(null);
  const [error, setError] = useState('');

  useEffect(() => {
    api.get(`/audits/${auditId}/results`)
      .then((res) => setResults(res.data))
      .catch((err) => setError(err.response?.data?.detail || 'Erreur lors du chargement'))
      .finally(() => setLoading(false));
  }, [auditId]);

  const handleGeneratePdf = async () => {
    setGenerating(true);
    try {
      const res = await api.post(`/audits/${auditId}/report`);
      setReportInfo(res.data);
    } catch (err) {
      setError(err.response?.data?.detail || 'Erreur lors de la génération');
    } finally {
      setGenerating(false);
    }
  };

  const handleDownload = async () => {
    try {
      const res = await api.get(`/audits/${auditId}/report/download`, { responseType: 'blob' });
      const url = window.URL.createObjectURL(res.data);
      const a = document.createElement('a');
      a.href = url;
      a.download = `rapport_greenaudit_${results.company_name}.pdf`;
      a.click();
      window.URL.revokeObjectURL(url);
    } catch (err) {
      setError('Erreur lors du téléchargement du PDF');
    }
  };

  if (loading) {
    return <div className="flex justify-center items-center h-64"><div className="text-gray-500">Chargement...</div></div>;
  }

  if (error && !results) {
    return (
      <div className="max-w-4xl mx-auto p-6">
        <div className="bg-red-50 text-red-700 p-4 rounded-lg">{error}</div>
        <Link to="/" className="mt-4 inline-block text-green-700 hover:underline">Retour au dashboard</Link>
      </div>
    );
  }

  if (!results) return null;

  const scoreColor = results.risk_level ? RISK_COLORS[results.risk_level] : 'bg-gray-400';

  return (
    <div className="max-w-5xl mx-auto p-6 space-y-8">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <Link to="/" className="text-green-700 hover:underline text-sm">← Dashboard</Link>
          <h1 className="text-2xl font-bold text-gray-900 mt-1">{results.company_name}</h1>
        </div>
        <div className="flex gap-3">
          <button
            onClick={handleGeneratePdf}
            disabled={generating}
            className="px-4 py-2 bg-green-700 text-white rounded-lg hover:bg-green-800 disabled:opacity-50"
          >
            {generating ? 'Génération...' : 'Générer le PDF'}
          </button>
          {reportInfo && (
            <button
              onClick={handleDownload}
              className="px-4 py-2 bg-white border border-green-700 text-green-700 rounded-lg hover:bg-green-50"
            >
              Télécharger le PDF
            </button>
          )}
        </div>
      </div>

      {/* Score global */}
      <div className="bg-white rounded-xl shadow p-6">
        <h2 className="text-lg font-semibold text-gray-800 mb-4">Synthèse</h2>
        <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
          <div className="text-center p-4 bg-gray-50 rounded-lg">
            <div className="text-3xl font-bold text-gray-800">{results.global_score ?? '—'}</div>
            <div className="text-sm text-gray-500">Score /100</div>
          </div>
          <div className="text-center p-4 bg-gray-50 rounded-lg">
            <div className={`inline-block px-3 py-1 rounded-full text-white text-sm font-medium ${scoreColor}`}>
              {results.risk_level || '—'}
            </div>
            <div className="text-sm text-gray-500 mt-1">Niveau de risque</div>
          </div>
          <div className="text-center p-4 bg-green-50 rounded-lg">
            <div className="text-2xl font-bold text-green-700">{results.conforming_claims}</div>
            <div className="text-sm text-gray-500">Conformes</div>
          </div>
          <div className="text-center p-4 bg-orange-50 rounded-lg">
            <div className="text-2xl font-bold text-orange-600">{results.at_risk_claims}</div>
            <div className="text-sm text-gray-500">À risque</div>
          </div>
          <div className="text-center p-4 bg-red-50 rounded-lg">
            <div className="text-2xl font-bold text-red-700">{results.non_conforming_claims}</div>
            <div className="text-sm text-gray-500">Non conformes</div>
          </div>
        </div>
      </div>

      {/* Share link */}
      {reportInfo?.share_token && (
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
          <p className="text-sm text-blue-800">
            <span className="font-medium">Lien de partage client :</span>{' '}
            <code className="bg-blue-100 px-2 py-0.5 rounded text-xs">
              {window.location.origin}/api/audits/{auditId}/share/{reportInfo.share_token}
            </code>
          </p>
        </div>
      )}

      {/* Détail par claim */}
      <div className="space-y-6">
        <h2 className="text-lg font-semibold text-gray-800">Détail des allégations</h2>
        {results.claims.map((claim, idx) => (
          <div key={claim.id} className="bg-white rounded-xl shadow overflow-hidden">
            <div className="p-4 border-b border-gray-100 flex items-center justify-between">
              <div className="flex items-center gap-3">
                <span className="text-sm font-medium text-gray-400">#{idx + 1}</span>
                <VerdictBadge verdict={claim.overall_verdict} />
              </div>
              <span className="text-xs text-gray-400">{claim.support_type} · {claim.scope}</span>
            </div>
            <div className="p-4 bg-gray-50 border-b border-gray-100">
              <p className="italic text-gray-700">« {claim.claim_text} »</p>
            </div>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="bg-green-800 text-white">
                    <th className="px-4 py-2 text-left font-medium">Critère</th>
                    <th className="px-4 py-2 text-left font-medium">Verdict</th>
                    <th className="px-4 py-2 text-left font-medium">Explication</th>
                    <th className="px-4 py-2 text-left font-medium">Recommandation</th>
                  </tr>
                </thead>
                <tbody>
                  {claim.results
                    .sort((a, b) => {
                      const order = ['specificity', 'compensation', 'labels', 'proportionality', 'future_commitment', 'justification'];
                      return order.indexOf(a.criterion) - order.indexOf(b.criterion);
                    })
                    .map((r) => (
                      <tr key={r.id} className="border-b border-gray-100">
                        <td className="px-4 py-2 font-medium text-gray-700">{CRITERION_LABELS[r.criterion] || r.criterion}</td>
                        <td className="px-4 py-2"><VerdictBadge verdict={r.verdict} /></td>
                        <td className="px-4 py-2 text-gray-600">{r.explanation}</td>
                        <td className="px-4 py-2 text-gray-500">{r.recommendation || '—'}</td>
                      </tr>
                    ))}
                </tbody>
              </table>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
