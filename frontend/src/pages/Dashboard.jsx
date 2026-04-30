import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import api from '../api/client';
import { useAuth } from '../api/auth';

const STATUS_STYLES = {
  draft: 'bg-gray-100 text-gray-600',
  in_progress: 'bg-blue-50 text-blue-700',
  completed: 'bg-[#eaf4ee] text-[#1a5c3a]',
};
const STATUS_LABELS = { draft: 'Brouillon', in_progress: 'En cours', completed: 'Terminé' };

const RISK_STYLES = {
  faible: 'bg-[#eaf4ee] text-[#1a5c3a]',
  modere: 'bg-yellow-50 text-yellow-800',
  eleve: 'bg-orange-50 text-orange-800',
  critique: 'bg-red-50 text-red-800',
};
const RISK_LABELS = { faible: 'Faible', modere: 'Modéré', eleve: 'Élevé', critique: 'Critique' };

function formatDate(d) {
  if (!d) return '';
  return new Date(d).toLocaleDateString('fr-FR', { day: 'numeric', month: 'long', year: 'numeric' });
}

function scoreColor(score) {
  if (score == null) return '#9ca3af';
  if (score >= 80) return '#1a5c3a';
  if (score >= 60) return '#d97706';
  if (score >= 40) return '#ea580c';
  return '#dc2626';
}

export default function Dashboard() {
  const navigate = useNavigate();
  const { user } = useAuth();
  const isPro = ['pro', 'enterprise'].includes(user?.subscription_plan);
  const [audits, setAudits] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [deletingId, setDeletingId] = useState(null);
  const [unreadAlerts, setUnreadAlerts] = useState({});

  useEffect(() => { fetchAudits(); }, []);

  async function fetchAudits() {
    try {
      setLoading(true);
      setError(null);
      const [auditsRes, unreadRes] = await Promise.allSettled([
        api.get('/audits'),
        api.get('/monitoring/unread-summary'),
      ]);
      if (auditsRes.status === 'fulfilled') setAudits(auditsRes.value.data);
      else setError('Impossible de charger les audits. Veuillez réessayer.');
      if (unreadRes.status === 'fulfilled') setUnreadAlerts(unreadRes.value.data);
    } finally {
      setLoading(false);
    }
  }

  async function handleDelete(e, auditId) {
    e.stopPropagation();
    if (!window.confirm('Supprimer cet audit brouillon ?')) return;
    try {
      setDeletingId(auditId);
      await api.delete(`/audits/${auditId}`);
      setAudits((prev) => prev.filter((a) => a.id !== auditId));
    } catch {
      setError('Impossible de supprimer cet audit.');
    } finally {
      setDeletingId(null);
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center py-20">
        <p className="text-gray-400 text-sm">Chargement des audits...</p>
      </div>
    );
  }

  return (
    <div>
      {/* Header */}
      <div className="flex items-center justify-between mb-8">
        <div>
          <p className="text-xs font-semibold uppercase tracking-widest text-[#1a5c3a] mb-1">Partenaire</p>
          <h1 className="text-2xl font-black text-gray-900">Tableau de bord</h1>
          <p className="mt-1 text-sm text-gray-500">Gérez vos audits anti-greenwashing</p>
        </div>
        <div className="flex items-center gap-3">
          {isPro && (
            <button
              onClick={() => navigate('/scan')}
              className="inline-flex items-center gap-2 px-4 py-2.5 rounded-full text-sm font-semibold text-[#1a5c3a] bg-[#eaf4ee] hover:bg-[#d4ecdd] transition-colors"
            >
              <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
              </svg>
              Scan de site
            </button>
          )}
          <button
            onClick={() => navigate('/audits/new')}
            className="inline-flex items-center gap-2 px-5 py-2.5 rounded-full text-sm font-semibold text-white bg-[#1a5c3a] hover:bg-[#14472d] transition-colors"
          >
            <svg className="h-4 w-4" viewBox="0 0 20 20" fill="currentColor">
              <path fillRule="evenodd" d="M10 3a1 1 0 011 1v5h5a1 1 0 110 2h-5v5a1 1 0 11-2 0v-5H4a1 1 0 110-2h5V4a1 1 0 011-1z" clipRule="evenodd" />
            </svg>
            Nouvel audit
          </button>
        </div>
      </div>

      {/* Error */}
      {error && (
        <div className="mb-6 p-4 bg-red-50 border border-red-100 rounded-xl text-red-700 text-sm flex items-center justify-between">
          <span>{error}</span>
          <button onClick={() => setError(null)} className="text-red-400 hover:text-red-600 font-medium">Fermer</button>
        </div>
      )}

      {/* Empty state */}
      {audits.length === 0 ? (
        <div className="text-center py-24 bg-white rounded-2xl border border-gray-100">
          <svg className="mx-auto h-14 w-14 text-gray-200" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1}>
            <path strokeLinecap="round" strokeLinejoin="round"
              d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
          </svg>
          <h2 className="mt-4 text-lg font-bold text-gray-700">Aucun audit pour le moment</h2>
          <p className="mt-2 text-sm text-gray-400">Créez votre premier audit pour commencer l'analyse.</p>
          <button
            onClick={() => navigate('/audits/new')}
            className="mt-6 inline-flex items-center gap-2 px-5 py-2.5 rounded-full text-sm font-semibold text-white bg-[#1a5c3a] hover:bg-[#14472d] transition-colors"
          >
            <svg className="h-4 w-4" viewBox="0 0 20 20" fill="currentColor">
              <path fillRule="evenodd" d="M10 3a1 1 0 011 1v5h5a1 1 0 110 2h-5v5a1 1 0 11-2 0v-5H4a1 1 0 110-2h5V4a1 1 0 011-1z" clipRule="evenodd" />
            </svg>
            Créer un audit
          </button>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
          {audits.map((audit) => {
            const unreadCount = unreadAlerts[audit.id] || 0;
            return (
              <div
                key={audit.id}
                onClick={() => navigate(`/audits/${audit.id}`)}
                className="bg-white rounded-2xl border border-gray-100 p-6 cursor-pointer hover:border-gray-200 hover:shadow-sm transition-all flex flex-col"
              >
                {/* Top */}
                <div className="flex items-start justify-between gap-3">
                  <div className="min-w-0 flex-1">
                    <div className="flex items-center gap-2">
                      <h3 className="text-base font-bold text-gray-900 truncate">
                        {audit.company_name.replace(' [DÉMO]', '')}
                      </h3>
                      {audit.company_name.includes('[DÉMO]') && (
                        <span className="shrink-0 text-xs font-semibold px-2 py-0.5 rounded-full bg-purple-50 text-purple-600 border border-purple-100">
                          Démo
                        </span>
                      )}
                      {unreadCount > 0 && (
                        <span className="shrink-0 inline-flex items-center justify-center h-5 min-w-5 px-1.5 rounded-full bg-red-600 text-white text-xs font-bold">
                          {unreadCount}
                        </span>
                      )}
                    </div>
                    <p className="text-xs text-gray-400 mt-0.5 capitalize">{audit.sector}</p>
                  </div>
                  {audit.status === 'draft' && (
                    <button
                      onClick={(e) => handleDelete(e, audit.id)}
                      disabled={deletingId === audit.id}
                      className="shrink-0 p-1.5 rounded-lg text-gray-300 hover:text-red-500 hover:bg-red-50 transition-colors disabled:opacity-50"
                    >
                      <svg className="h-4 w-4" viewBox="0 0 20 20" fill="currentColor">
                        <path fillRule="evenodd" d="M9 2a1 1 0 00-.894.553L7.382 4H4a1 1 0 000 2v10a2 2 0 002 2h8a2 2 0 002-2V6a1 1 0 100-2h-3.382l-.724-1.447A1 1 0 0011 2H9zM7 8a1 1 0 012 0v6a1 1 0 11-2 0V8zm5-1a1 1 0 00-1 1v6a1 1 0 102 0V8a1 1 0 00-1-1z" clipRule="evenodd" />
                      </svg>
                    </button>
                  )}
                </div>

                {/* Badges */}
                <div className="flex items-center gap-2 mt-4 flex-wrap">
                  <span className={`text-xs font-medium px-2.5 py-1 rounded-full ${STATUS_STYLES[audit.status] || 'bg-gray-100 text-gray-600'}`}>
                    {STATUS_LABELS[audit.status] || audit.status}
                  </span>
                  {audit.risk_level && (
                    <span className={`text-xs font-medium px-2.5 py-1 rounded-full ${RISK_STYLES[audit.risk_level] || 'bg-gray-100 text-gray-600'}`}>
                      Risque {RISK_LABELS[audit.risk_level] || audit.risk_level}
                    </span>
                  )}
                  {unreadCount > 0 && (
                    <span className="text-xs font-medium px-2.5 py-1 rounded-full bg-red-50 text-red-700">
                      {unreadCount} alerte{unreadCount > 1 ? 's' : ''}
                    </span>
                  )}
                  {audit.client_access?.exists && !audit.client_access.is_revoked && (
                    <span className="text-xs font-medium px-2.5 py-1 rounded-full bg-blue-50 text-blue-700">
                      Coffre-fort actif
                    </span>
                  )}
                </div>

                {/* Stats */}
                <div className="mt-5 pt-4 border-t border-gray-50 grid grid-cols-2 gap-4">
                  <div>
                    <p className="text-xs text-gray-400 uppercase tracking-wide">Allégations</p>
                    <p className="mt-1 text-xl font-black text-gray-900">{audit.total_claims ?? 0}</p>
                  </div>
                  <div>
                    <p className="text-xs text-gray-400 uppercase tracking-wide">Score</p>
                    <p className="mt-1 text-xl font-black" style={{ color: scoreColor(audit.global_score) }}>
                      {audit.global_score != null ? `${Number(audit.global_score).toFixed(0)}%` : '—'}
                    </p>
                  </div>
                </div>

                {/* Tracking coffre-fort */}
                {audit.client_access?.exists && !audit.client_access.is_revoked && (
                  <div className="mt-3 pt-3 border-t border-gray-50 flex items-center gap-4 text-xs text-gray-400">
                    <span title="Dernière ouverture">
                      {audit.client_access.last_opened_at
                        ? `Ouvert le ${new Date(audit.client_access.last_opened_at).toLocaleDateString('fr-FR', { day: 'numeric', month: 'short' })}`
                        : 'Pas encore ouvert'}
                    </span>
                    {audit.client_access.pdf_downloaded_at && (
                      <span className="text-green-600">PDF ✓</span>
                    )}
                    {audit.client_access.zip_downloaded_at && (
                      <span className="text-green-600">ZIP ✓</span>
                    )}
                  </div>
                )}

                <p className="mt-3 text-xs text-gray-300">Créé le {formatDate(audit.created_at)}</p>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
