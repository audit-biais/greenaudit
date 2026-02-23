import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import api from '../api/client';

const STATUS_STYLES = {
  draft: 'bg-gray-100 text-gray-700',
  in_progress: 'bg-blue-100 text-blue-700',
  completed: 'bg-green-100 text-green-700',
};

const STATUS_LABELS = {
  draft: 'Brouillon',
  in_progress: 'En cours',
  completed: 'Terminé',
};

const RISK_STYLES = {
  faible: 'bg-green-100 text-green-800',
  modere: 'bg-yellow-100 text-yellow-800',
  eleve: 'bg-orange-100 text-orange-800',
  critique: 'bg-red-100 text-red-800',
};

const RISK_LABELS = {
  faible: 'Faible',
  modere: 'Modéré',
  eleve: 'Élevé',
  critique: 'Critique',
};

function formatDate(dateString) {
  if (!dateString) return '';
  return new Date(dateString).toLocaleDateString('fr-FR', {
    day: 'numeric',
    month: 'long',
    year: 'numeric',
  });
}

export default function Dashboard() {
  const navigate = useNavigate();
  const [audits, setAudits] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [deletingId, setDeletingId] = useState(null);
  // {audit_id: unread_count} — alertes monitoring non lues
  const [unreadAlerts, setUnreadAlerts] = useState({});

  useEffect(() => {
    fetchAudits();
  }, []);

  async function fetchAudits() {
    try {
      setLoading(true);
      setError(null);
      const [auditsRes, unreadRes] = await Promise.allSettled([
        api.get('/audits'),
        api.get('/monitoring/unread-summary'),
      ]);
      if (auditsRes.status === 'fulfilled') {
        setAudits(auditsRes.value.data);
      } else {
        setError('Impossible de charger les audits. Veuillez réessayer.');
      }
      if (unreadRes.status === 'fulfilled') {
        setUnreadAlerts(unreadRes.value.data);
      }
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
    } catch (err) {
      setError('Impossible de supprimer cet audit.');
    } finally {
      setDeletingId(null);
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center py-20">
        <div className="text-gray-500 text-lg">Chargement des audits...</div>
      </div>
    );
  }

  return (
    <div>
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
          <div>
            <h1 className="text-2xl font-bold" style={{ color: '#1B5E20' }}>
              Tableau de bord
            </h1>
            <p className="mt-1 text-sm text-gray-500">
              Gérez vos audits anti-greenwashing
            </p>
          </div>
          <button
            onClick={() => navigate('/audits/new')}
            className="inline-flex items-center gap-2 px-5 py-2.5 rounded-lg text-white font-medium text-sm cursor-pointer transition-colors duration-150"
            style={{ backgroundColor: '#1B5E20' }}
            onMouseEnter={(e) => (e.currentTarget.style.backgroundColor = '#2E7D32')}
            onMouseLeave={(e) => (e.currentTarget.style.backgroundColor = '#1B5E20')}
          >
            <svg
              xmlns="http://www.w3.org/2000/svg"
              className="h-5 w-5"
              viewBox="0 0 20 20"
              fill="currentColor"
            >
              <path
                fillRule="evenodd"
                d="M10 3a1 1 0 011 1v5h5a1 1 0 110 2h-5v5a1 1 0 11-2 0v-5H4a1 1 0 110-2h5V4a1 1 0 011-1z"
                clipRule="evenodd"
              />
            </svg>
            Nouvel audit
          </button>
      </div>

      <div>
        {/* Error banner */}
        {error && (
          <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm flex items-center justify-between">
            <span>{error}</span>
            <button
              onClick={() => setError(null)}
              className="text-red-500 hover:text-red-700 font-medium cursor-pointer"
            >
              Fermer
            </button>
          </div>
        )}

        {/* Empty state */}
        {audits.length === 0 ? (
          <div className="text-center py-20">
            <svg
              xmlns="http://www.w3.org/2000/svg"
              className="mx-auto h-16 w-16 text-gray-300"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
              strokeWidth={1}
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
              />
            </svg>
            <h2 className="mt-4 text-lg font-semibold text-gray-700">
              Aucun audit pour le moment
            </h2>
            <p className="mt-2 text-sm text-gray-500">
              Créez votre premier audit pour commencer l'analyse anti-greenwashing.
            </p>
            <button
              onClick={() => navigate('/audits/new')}
              className="mt-6 inline-flex items-center gap-2 px-5 py-2.5 rounded-lg text-white font-medium text-sm cursor-pointer transition-colors duration-150"
              style={{ backgroundColor: '#1B5E20' }}
              onMouseEnter={(e) => (e.currentTarget.style.backgroundColor = '#2E7D32')}
              onMouseLeave={(e) => (e.currentTarget.style.backgroundColor = '#1B5E20')}
            >
              <svg
                xmlns="http://www.w3.org/2000/svg"
                className="h-5 w-5"
                viewBox="0 0 20 20"
                fill="currentColor"
              >
                <path
                  fillRule="evenodd"
                  d="M10 3a1 1 0 011 1v5h5a1 1 0 110 2h-5v5a1 1 0 11-2 0v-5H4a1 1 0 110-2h5V4a1 1 0 011-1z"
                  clipRule="evenodd"
                />
              </svg>
              Créer un audit
            </button>
          </div>
        ) : (
          /* Audit cards grid */
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {audits.map((audit) => {
              const unreadCount = unreadAlerts[audit.id] || 0;
              return (
                <div
                  key={audit.id}
                  onClick={() => navigate(`/audits/${audit.id}`)}
                  className="bg-white rounded-xl shadow-sm border border-gray-200 p-6 cursor-pointer hover:shadow-md hover:border-gray-300 transition-all duration-150 flex flex-col"
                >
                  {/* Top row: company + delete + monitoring badge */}
                  <div className="flex items-start justify-between gap-3">
                    <div className="min-w-0 flex-1">
                      <div className="flex items-center gap-2">
                        <h3 className="text-lg font-semibold text-gray-900 truncate">
                          {audit.company_name}
                        </h3>
                        {unreadCount > 0 && (
                          <span className="shrink-0 inline-flex items-center justify-center h-5 min-w-5 px-1.5 rounded-full bg-red-600 text-white text-xs font-bold">
                            {unreadCount}
                          </span>
                        )}
                      </div>
                      <p className="text-sm text-gray-500 mt-0.5 capitalize">
                        {audit.sector}
                      </p>
                    </div>
                    {audit.status === 'draft' && (
                      <button
                        onClick={(e) => handleDelete(e, audit.id)}
                        disabled={deletingId === audit.id}
                        className="shrink-0 p-1.5 rounded-md text-gray-400 hover:text-red-600 hover:bg-red-50 transition-colors duration-150 cursor-pointer disabled:opacity-50"
                        title="Supprimer l'audit"
                      >
                        <svg
                          xmlns="http://www.w3.org/2000/svg"
                          className="h-5 w-5"
                          viewBox="0 0 20 20"
                          fill="currentColor"
                        >
                          <path
                            fillRule="evenodd"
                            d="M9 2a1 1 0 00-.894.553L7.382 4H4a1 1 0 000 2v10a2 2 0 002 2h8a2 2 0 002-2V6a1 1 0 100-2h-3.382l-.724-1.447A1 1 0 0011 2H9zM7 8a1 1 0 012 0v6a1 1 0 11-2 0V8zm5-1a1 1 0 00-1 1v6a1 1 0 102 0V8a1 1 0 00-1-1z"
                            clipRule="evenodd"
                          />
                        </svg>
                      </button>
                    )}
                  </div>

                  {/* Status + risk + monitoring badges */}
                  <div className="flex items-center gap-2 mt-4 flex-wrap">
                    <span
                      className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${STATUS_STYLES[audit.status] || 'bg-gray-100 text-gray-700'}`}
                    >
                      {STATUS_LABELS[audit.status] || audit.status}
                    </span>
                    {audit.risk_level && (
                      <span
                        className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${RISK_STYLES[audit.risk_level] || 'bg-gray-100 text-gray-700'}`}
                      >
                        Risque {RISK_LABELS[audit.risk_level] || audit.risk_level}
                      </span>
                    )}
                    {unreadCount > 0 && (
                      <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-red-50 text-red-700">
                        {unreadCount} alerte{unreadCount > 1 ? 's' : ''} monitoring
                      </span>
                    )}
                  </div>

                  {/* Stats row */}
                  <div className="mt-5 pt-4 border-t border-gray-100 grid grid-cols-2 gap-4">
                    <div>
                      <p className="text-xs text-gray-500 uppercase tracking-wide">
                        Allégations
                      </p>
                      <p className="mt-1 text-lg font-semibold text-gray-900">
                        {audit.total_claims ?? 0}
                      </p>
                    </div>
                    <div>
                      <p className="text-xs text-gray-500 uppercase tracking-wide">
                        Score global
                      </p>
                      <p
                        className="mt-1 text-lg font-semibold"
                        style={{
                          color:
                            audit.global_score != null
                              ? audit.global_score >= 80
                                ? '#1B5E20'
                                : audit.global_score >= 60
                                  ? '#F59E0B'
                                  : audit.global_score >= 40
                                    ? '#EA580C'
                                    : '#DC2626'
                              : '#9CA3AF',
                        }}
                      >
                        {audit.global_score != null
                          ? `${Number(audit.global_score).toFixed(0)}%`
                          : '\u2014'}
                      </p>
                    </div>
                  </div>

                  {/* Date */}
                  <p className="mt-4 text-xs text-gray-400">
                    Créé le {formatDate(audit.created_at)}
                  </p>
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
}
