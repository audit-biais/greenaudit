import { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import api from '../api/client';

const VERDICT_STYLES = {
  conforme: 'bg-[#eaf4ee] text-[#1a5c3a]',
  non_conforme: 'bg-red-50 text-red-700',
  risque: 'bg-orange-50 text-orange-700',
  non_applicable: 'bg-gray-100 text-gray-500',
};
const VERDICT_LABELS = { conforme: 'Conforme', non_conforme: 'Non conforme', risque: 'Risque', non_applicable: 'N/A' };

const RISK_BAR_COLORS = { faible: 'bg-[#1a5c3a]', modere: 'bg-yellow-500', eleve: 'bg-orange-500', critique: 'bg-red-600' };

const CRITERION_LABELS = {
  specificity: 'Spécificité (Annexe I, 4bis)',
  compensation: 'Neutralité carbone (4quater)',
  labels: 'Labels (2bis)',
  proportionality: 'Proportionnalité (4ter)',
  future_commitment: 'Engagements futurs (Art. 6)',
  justification: 'Justification / Preuves',
  legal_requirement: 'Exigence légale (10bis)',
  agec_france: 'Loi AGEC France (Art. 13)',
};

const DOCUMENT_TYPE_LABELS = {
  ecolabel: 'Écolabel officiel',
  certification: 'Certification',
  rapport_interne: 'Rapport interne',
  autre: 'Autre document',
};

const DOCUMENT_TYPE_COLORS = {
  ecolabel: 'bg-[#eaf4ee] text-[#1a5c3a] border border-[#1a5c3a]/20',
  certification: 'bg-blue-50 text-blue-700 border border-blue-200',
  rapport_interne: 'bg-orange-50 text-orange-700 border border-orange-200',
  autre: 'bg-gray-100 text-gray-600 border border-gray-200',
};

function VerdictBadge({ verdict }) {
  return (
    <span className={`px-2.5 py-1 rounded-full text-xs font-medium ${VERDICT_STYLES[verdict] || VERDICT_STYLES.non_applicable}`}>
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
  const [monitoring, setMonitoring] = useState(null);
  const [monitoringLoading, setMonitoringLoading] = useState(false);
  const [monitoringError, setMonitoringError] = useState('');
  const [rewrites, setRewrites] = useState({});
  const [rewriteLoading, setRewriteLoading] = useState({});
  const [evidenceFiles, setEvidenceFiles] = useState({});
  const [evidenceUploading, setEvidenceUploading] = useState({});
  const [evidenceOpen, setEvidenceOpen] = useState({});
  const [evidenceDocType, setEvidenceDocType] = useState({});

  useEffect(() => {
    api.get(`/audits/${auditId}/results`)
      .then((res) => setResults(res.data))
      .catch((err) => setError(err.response?.data?.detail || 'Erreur lors du chargement'))
      .finally(() => setLoading(false));
  }, [auditId]);

  useEffect(() => {
    if (results?.status === 'completed') {
      api.get(`/audits/${auditId}/monitoring`)
        .then((res) => setMonitoring(res.data))
        .catch((err) => { if (err.response?.status === 404) setMonitoring(false); });
    }
  }, [results, auditId]);

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
    } catch {
      setError('Erreur lors du téléchargement du PDF');
    }
  };

  const handleEnableMonitoring = async () => {
    setMonitoringLoading(true);
    setMonitoringError('');
    try {
      const res = await api.post(`/audits/${auditId}/monitoring`, { frequency_days: 7 });
      setMonitoring(res.data);
    } catch (err) {
      setMonitoringError(err.response?.data?.detail || "Erreur lors de l'activation");
    } finally {
      setMonitoringLoading(false);
    }
  };

  const handleDisableMonitoring = async () => {
    try {
      await api.delete(`/audits/${auditId}/monitoring`);
      setMonitoring((prev) => ({ ...prev, is_active: false }));
    } catch (err) {
      setMonitoringError(err.response?.data?.detail || 'Erreur');
    }
  };

  const handleRewrite = async (claimId) => {
    setRewriteLoading((prev) => ({ ...prev, [claimId]: true }));
    try {
      const res = await api.post(`/claims/${claimId}/rewrite`);
      setRewrites((prev) => ({ ...prev, [claimId]: res.data.suggestion }));
    } catch (err) {
      setRewrites((prev) => ({ ...prev, [claimId]: err.response?.data?.detail || 'Erreur lors de la génération.' }));
    } finally {
      setRewriteLoading((prev) => ({ ...prev, [claimId]: false }));
    }
  };

  const loadEvidence = async (claimId) => {
    try {
      const res = await api.get(`/claims/${claimId}/evidence`);
      setEvidenceFiles((prev) => ({ ...prev, [claimId]: res.data }));
    } catch { /* silent */ }
  };

  const handleEvidenceToggle = (claimId) => {
    const opening = !evidenceOpen[claimId];
    setEvidenceOpen((prev) => ({ ...prev, [claimId]: opening }));
    if (opening && !evidenceFiles[claimId]) loadEvidence(claimId);
  };

  const handleEvidenceUpload = async (claimId, file) => {
    setEvidenceUploading((prev) => ({ ...prev, [claimId]: true }));
    const formData = new FormData();
    formData.append('file', file);
    formData.append('document_type', evidenceDocType[claimId] || 'autre');
    try {
      await api.post(`/claims/${claimId}/evidence`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });
      await loadEvidence(claimId);
    } catch (err) {
      alert(err.response?.data?.detail || "Erreur lors de l'upload");
    } finally {
      setEvidenceUploading((prev) => ({ ...prev, [claimId]: false }));
    }
  };

  const handleEvidenceDelete = async (claimId, evidenceId) => {
    if (!window.confirm('Supprimer ce fichier ?')) return;
    try {
      await api.delete(`/evidence/${evidenceId}`);
      setEvidenceFiles((prev) => ({
        ...prev,
        [claimId]: prev[claimId].filter((f) => f.id !== evidenceId),
      }));
    } catch { /* silent */ }
  };

  const formatSize = (bytes) => {
    if (bytes < 1024) return `${bytes} o`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(0)} Ko`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} Mo`;
  };

  const handleMarkRead = async (alertId) => {
    try {
      await api.patch(`/monitoring/alerts/${alertId}/read`);
      setMonitoring((prev) => ({
        ...prev,
        unread_alerts_count: Math.max(0, prev.unread_alerts_count - 1),
        alerts: prev.alerts.map((a) => a.id === alertId ? { ...a, is_read: true } : a),
      }));
    } catch { /* silent */ }
  };

  if (loading) return (
    <div className="flex justify-center items-center h-64">
      <p className="text-gray-400 text-sm">Chargement...</p>
    </div>
  );

  if (error && !results) return (
    <div className="max-w-4xl mx-auto">
      <div className="bg-red-50 text-red-700 p-4 rounded-xl text-sm">{error}</div>
      <Link to="/" className="mt-4 inline-block text-[#1a5c3a] hover:underline text-sm">← Dashboard</Link>
    </div>
  );

  if (!results) return null;

  return (
    <div className="max-w-5xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex items-start justify-between gap-4">
        <div>
          <Link to="/" className="text-xs text-[#1a5c3a] hover:underline">← Dashboard</Link>
          <h1 className="text-2xl font-black text-gray-900 mt-1">{results.company_name}</h1>
          <p className="text-sm text-gray-400 capitalize mt-0.5">{results.sector}</p>
        </div>
        <div className="flex gap-3 flex-shrink-0">
          <button
            onClick={handleGeneratePdf}
            disabled={generating}
            className="px-4 py-2.5 rounded-full text-sm font-semibold text-white bg-[#1a5c3a] hover:bg-[#14472d] transition-colors disabled:opacity-50"
          >
            {generating ? 'Génération...' : 'Générer le PDF'}
          </button>
          {reportInfo && (
            <button
              onClick={handleDownload}
              className="px-4 py-2.5 rounded-full text-sm font-semibold text-[#1a5c3a] border-2 border-[#1a5c3a] hover:bg-[#eaf4ee] transition-colors"
            >
              Télécharger →
            </button>
          )}
          <a
            href={`${api.defaults.baseURL}/audits/${auditId}/evidence/download-zip`}
            className="px-4 py-2.5 rounded-full text-sm font-semibold text-gray-600 border border-gray-200 hover:bg-gray-50 transition-colors"
            download
          >
            Dossier preuves ZIP
          </a>
        </div>
      </div>

      {error && (
        <div className="p-4 bg-red-50 border border-red-100 rounded-xl text-red-700 text-sm">{error}</div>
      )}

      {/* Score global */}
      <div className="bg-white rounded-2xl border border-gray-100 p-6">
        <p className="text-xs font-semibold uppercase tracking-widest text-[#1a5c3a] mb-4">Synthèse</p>
        <div className="grid grid-cols-2 sm:grid-cols-5 gap-4">
          <div className="text-center p-4 bg-gray-50 rounded-xl">
            <p className="text-3xl font-black text-gray-900">{results.global_score ?? '—'}</p>
            <p className="text-xs text-gray-400 mt-1">Score /100</p>
          </div>
          <div className="text-center p-4 bg-gray-50 rounded-xl">
            <div className={`inline-block px-3 py-1 rounded-full text-white text-sm font-semibold ${RISK_BAR_COLORS[results.risk_level] || 'bg-gray-400'}`}>
              {results.risk_level || '—'}
            </div>
            <p className="text-xs text-gray-400 mt-2">Niveau de risque</p>
          </div>
          <div className="text-center p-4 bg-[#eaf4ee] rounded-xl">
            <p className="text-2xl font-black text-[#1a5c3a]">{results.conforming_claims}</p>
            <p className="text-xs text-gray-500 mt-1">Conformes</p>
          </div>
          <div className="text-center p-4 bg-orange-50 rounded-xl">
            <p className="text-2xl font-black text-orange-600">{results.at_risk_claims}</p>
            <p className="text-xs text-gray-500 mt-1">À risque</p>
          </div>
          <div className="text-center p-4 bg-red-50 rounded-xl">
            <p className="text-2xl font-black text-red-700">{results.non_conforming_claims}</p>
            <p className="text-xs text-gray-500 mt-1">Non conformes</p>
          </div>
        </div>
      </div>

      {/* Share link */}
      {reportInfo?.share_token && (
        <div className="bg-[#eaf4ee] border border-[#1a5c3a]/20 rounded-xl p-4">
          <p className="text-sm text-[#1a5c3a]">
            <span className="font-semibold">Lien de partage client : </span>
            <code className="bg-white px-2 py-0.5 rounded text-xs border border-[#1a5c3a]/20">
              {window.location.origin}/api/audits/{auditId}/share/{reportInfo.share_token}
            </code>
          </p>
        </div>
      )}

      {/* Monitoring */}
      {results.status === 'completed' && (
        <div className="bg-white rounded-2xl border border-gray-100 p-6">
          <p className="text-xs font-semibold uppercase tracking-widest text-[#1a5c3a] mb-1">Monitoring</p>
          <h2 className="text-lg font-bold text-gray-900 mb-1">Monitoring continu</h2>
          <p className="text-sm text-gray-400 mb-4">
            Détecte automatiquement les nouvelles allégations sur le site chaque semaine.
          </p>

          {monitoring === null && <p className="text-sm text-gray-400">Chargement...</p>}

          {monitoring === false && (
            <div>
              {!results.website_url && (
                <p className="text-sm text-amber-700 bg-amber-50 px-3 py-2 rounded-xl mb-3">
                  Cet audit n'a pas d'URL de site web.
                </p>
              )}
              {monitoringError && <p className="text-sm text-red-600 mb-3">{monitoringError}</p>}
              <button
                onClick={handleEnableMonitoring}
                disabled={monitoringLoading || !results.website_url}
                className="px-4 py-2.5 rounded-full text-sm font-semibold text-white bg-[#1a5c3a] hover:bg-[#14472d] transition-colors disabled:opacity-50"
              >
                {monitoringLoading ? 'Activation...' : 'Activer le monitoring →'}
              </button>
            </div>
          )}

          {monitoring && typeof monitoring === 'object' && (
            <div>
              <div className="flex items-center justify-between mb-4">
                <div className="flex items-center gap-3">
                  <span className={`px-2.5 py-1 rounded-full text-xs font-medium ${monitoring.is_active ? 'bg-[#eaf4ee] text-[#1a5c3a]' : 'bg-gray-100 text-gray-500'}`}>
                    {monitoring.is_active ? 'Actif' : 'Inactif'}
                  </span>
                  {monitoring.unread_alerts_count > 0 && (
                    <span className="px-2.5 py-1 rounded-full text-xs font-medium bg-red-50 text-red-700">
                      {monitoring.unread_alerts_count} nouvelle{monitoring.unread_alerts_count > 1 ? 's' : ''} alerte{monitoring.unread_alerts_count > 1 ? 's' : ''}
                    </span>
                  )}
                </div>
                <button onClick={monitoring.is_active ? handleDisableMonitoring : handleEnableMonitoring}
                  className="text-sm text-gray-400 hover:text-gray-600 underline">
                  {monitoring.is_active ? 'Désactiver' : 'Réactiver'}
                </button>
              </div>

              {monitoring.last_checked_at && (
                <p className="text-xs text-gray-400 mb-4">
                  Dernier check : {new Date(monitoring.last_checked_at).toLocaleString('fr-FR')}
                  {monitoring.next_check_at && <> · Prochain : {new Date(monitoring.next_check_at).toLocaleDateString('fr-FR')}</>}
                </p>
              )}

              {monitoringError && <p className="text-sm text-red-600 mb-3">{monitoringError}</p>}

              {monitoring.alerts.length === 0 ? (
                <p className="text-sm text-gray-400">Aucune nouvelle allégation détectée.</p>
              ) : (
                <div className="space-y-2">
                  {monitoring.alerts.map((alert) => (
                    <div key={alert.id} className={`p-3 rounded-xl border ${alert.is_read ? 'bg-gray-50 border-gray-100' : 'bg-amber-50 border-amber-200'}`}>
                      <div className="flex items-start justify-between gap-3">
                        <p className="text-sm text-gray-700 flex-1">{alert.claim_text}</p>
                        {!alert.is_read && (
                          <button onClick={() => handleMarkRead(alert.id)}
                            className="shrink-0 text-xs text-amber-700 hover:text-amber-900 font-medium whitespace-nowrap">
                            Marquer lu
                          </button>
                        )}
                      </div>
                      <p className="text-xs text-gray-400 mt-1">
                        Détectée le {new Date(alert.detected_at).toLocaleDateString('fr-FR')}
                      </p>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}
        </div>
      )}

      {/* Détail par claim */}
      <div className="space-y-4">
        <p className="text-xs font-semibold uppercase tracking-widest text-[#1a5c3a]">Détail des allégations</p>
        {results.claims.map((claim, idx) => (
          <div key={claim.id} className="bg-white rounded-2xl border border-gray-100 overflow-hidden">
            <div className="px-5 py-4 border-b border-gray-50 flex items-center justify-between">
              <div className="flex items-center gap-3">
                <span className="text-xs text-gray-300 font-mono">#{idx + 1}</span>
                <VerdictBadge verdict={claim.overall_verdict} />
              </div>
              <span className="text-xs text-gray-400">{claim.support_type} · {claim.scope}</span>
            </div>
            <div className="px-5 py-3 bg-gray-50 border-b border-gray-50">
              <p className="italic text-sm text-gray-600">« {claim.claim_text} »</p>
              {(claim.overall_verdict === 'non_conforme' || claim.overall_verdict === 'risque') && (
                <div className="mt-3">
                  {!rewrites[claim.id] ? (
                    <button
                      onClick={() => handleRewrite(claim.id)}
                      disabled={rewriteLoading[claim.id]}
                      className="text-xs font-semibold px-3 py-1.5 rounded-full bg-orange-50 text-orange-700 hover:bg-orange-100 transition-colors disabled:opacity-50"
                    >
                      {rewriteLoading[claim.id] ? 'Génération...' : 'Suggérer une réécriture →'}
                    </button>
                  ) : (
                    <div className="mt-2 p-3 bg-white border border-orange-200 rounded-xl">
                      <p className="text-xs font-semibold text-orange-700 mb-1">Suggestion conforme EmpCo</p>
                      <p className="text-sm text-gray-700 italic">« {rewrites[claim.id]} »</p>
                      <button
                        onClick={() => setRewrites((prev) => { const n = {...prev}; delete n[claim.id]; return n; })}
                        className="mt-2 text-xs text-gray-400 hover:text-gray-600"
                      >
                        Effacer
                      </button>
                    </div>
                  )}
                </div>
              )}
            </div>
            {/* Evidence Vault */}
            <div className="px-5 py-3 border-b border-gray-50">
              <button
                onClick={() => handleEvidenceToggle(claim.id)}
                className="flex items-center gap-2 text-xs font-semibold text-gray-500 hover:text-gray-700 transition-colors"
              >
                <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15.172 7l-6.586 6.586a2 2 0 102.828 2.828l6.414-6.586a4 4 0 00-5.656-5.656l-6.415 6.585a6 6 0 108.486 8.486L20.5 13" />
                </svg>
                Pièces justificatives
                {evidenceFiles[claim.id]?.length > 0 && (
                  <span className="bg-[#eaf4ee] text-[#1a5c3a] text-xs font-bold px-1.5 py-0.5 rounded-full">
                    {evidenceFiles[claim.id].length}
                  </span>
                )}
                <span className="text-gray-400">{evidenceOpen[claim.id] ? '▲' : '▼'}</span>
              </button>

              {evidenceOpen[claim.id] && (
                <div className="mt-3 space-y-2">
                  {/* Liste des fichiers */}
                  {(evidenceFiles[claim.id] || []).map((f) => (
                    <div key={f.id} className="flex items-center justify-between p-2 bg-gray-50 rounded-lg">
                      <div className="flex items-center gap-2 min-w-0">
                        <svg className="h-4 w-4 text-gray-400 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                        </svg>
                        <span className="text-xs text-gray-700 truncate">{f.filename}</span>
                        <span className="text-xs text-gray-400 shrink-0">{formatSize(f.file_size)}</span>
                        {f.document_type && (
                          <span className={`text-xs font-medium px-1.5 py-0.5 rounded-full shrink-0 ${DOCUMENT_TYPE_COLORS[f.document_type] || DOCUMENT_TYPE_COLORS.autre}`}>
                            {f.document_type === 'ecolabel' ? '★ ' : ''}{DOCUMENT_TYPE_LABELS[f.document_type] || f.document_type}
                          </span>
                        )}
                      </div>
                      <div className="flex items-center gap-3 shrink-0">
                        <a
                          href={`${api.defaults.baseURL}/evidence/${f.id}/download`}
                          className="text-xs text-[#1a5c3a] font-semibold hover:underline"
                          download
                        >
                          Télécharger
                        </a>
                        <button
                          onClick={() => handleEvidenceDelete(claim.id, f.id)}
                          className="text-xs text-red-400 hover:text-red-600"
                        >
                          Supprimer
                        </button>
                      </div>
                    </div>
                  ))}

                  {/* Upload — sélecteur de type + fichier */}
                  <div className="flex items-center gap-2 flex-wrap">
                    <select
                      className="text-xs border border-gray-200 rounded-lg px-2 py-1.5 text-gray-700 bg-white focus:outline-none focus:ring-1 focus:ring-[#1a5c3a]"
                      value={evidenceDocType[claim.id] || 'autre'}
                      onChange={(e) => setEvidenceDocType((prev) => ({ ...prev, [claim.id]: e.target.value }))}
                      disabled={evidenceUploading[claim.id]}
                    >
                      <option value="ecolabel">Écolabel officiel (EU, Ange Bleu, ISO 14024)</option>
                      <option value="certification">Certification tierce</option>
                      <option value="rapport_interne">Rapport interne</option>
                      <option value="autre">Autre document</option>
                    </select>
                    <label className="flex items-center gap-1 cursor-pointer text-xs text-[#1a5c3a] font-semibold hover:underline">
                      <input
                        type="file"
                        className="hidden"
                        accept=".pdf,.jpg,.jpeg,.png,.webp,.doc,.docx"
                        disabled={evidenceUploading[claim.id]}
                        onChange={(e) => e.target.files[0] && handleEvidenceUpload(claim.id, e.target.files[0])}
                      />
                      {evidenceUploading[claim.id] ? 'Upload en cours...' : '+ Ajouter (PDF, image, Word — max 10 Mo)'}
                    </label>
                  </div>
                  {(evidenceDocType[claim.id] || 'autre') === 'ecolabel' && (
                    <p className="text-xs text-[#1a5c3a] bg-[#eaf4ee] px-2 py-1 rounded-lg">
                      Un Écolabel officiel déposé ici peut débloquer le verdict "Conforme" sur cette allégation lors de la prochaine analyse.
                    </p>
                  )}
                </div>
              )}
            </div>

            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="bg-[#1a5c3a] text-white">
                    <th className="px-4 py-2.5 text-left text-xs font-semibold">Critère</th>
                    <th className="px-4 py-2.5 text-left text-xs font-semibold">Verdict</th>
                    <th className="px-4 py-2.5 text-left text-xs font-semibold">Explication</th>
                    <th className="px-4 py-2.5 text-left text-xs font-semibold">Recommandation</th>
                  </tr>
                </thead>
                <tbody>
                  {claim.results
                    .sort((a, b) => {
                      const order = ['specificity', 'compensation', 'labels', 'proportionality', 'future_commitment', 'justification', 'legal_requirement', 'agec_france'];
                      const ia = order.indexOf(a.criterion); const ib = order.indexOf(b.criterion);
                      return (ia === -1 ? 99 : ia) - (ib === -1 ? 99 : ib);
                    })
                    .map((r) => (
                      <tr key={r.id} className="border-b border-gray-50 hover:bg-gray-50 transition-colors">
                        <td className="px-4 py-3 font-medium text-gray-700 text-xs whitespace-nowrap">{CRITERION_LABELS[r.criterion] || r.criterion}</td>
                        <td className="px-4 py-3"><VerdictBadge verdict={r.verdict} /></td>
                        <td className="px-4 py-3 text-xs text-gray-500">{r.explanation}</td>
                        <td className="px-4 py-3 text-xs text-gray-400">{r.recommendation || '—'}</td>
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
