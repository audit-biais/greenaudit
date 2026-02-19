import { useState, useEffect, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import api from '../api/client';

// ---------------------------------------------------------------------------
// Constantes
// ---------------------------------------------------------------------------

const SUPPORT_TYPE_OPTIONS = [
  { value: 'web', label: 'Site web' },
  { value: 'packaging', label: 'Packaging' },
  { value: 'publicite', label: 'Publicite' },
  { value: 'reseaux_sociaux', label: 'Reseaux sociaux' },
  { value: 'autre', label: 'Autre' },
];

const SCOPE_OPTIONS = [
  { value: 'produit', label: 'Produit' },
  { value: 'entreprise', label: 'Entreprise' },
];

const PROOF_TYPE_OPTIONS = [
  { value: 'certification_tierce', label: 'Certification tierce' },
  { value: 'rapport_interne', label: 'Rapport interne' },
  { value: 'donnees_fournisseur', label: 'Donnees fournisseur' },
  { value: 'aucune', label: 'Aucune' },
];

const VERDICT_STYLES = {
  conforme: 'bg-green-100 text-green-800 border-green-300',
  non_conforme: 'bg-red-100 text-red-800 border-red-300',
  risque: 'bg-yellow-100 text-yellow-800 border-yellow-300',
};

const VERDICT_LABELS = {
  conforme: 'Conforme',
  non_conforme: 'Non conforme',
  risque: 'Risque',
};

const EMPTY_FORM = {
  claim_text: '',
  support_type: 'web',
  scope: 'produit',
  product_name: '',
  has_proof: false,
  proof_description: '',
  proof_type: 'aucune',
  has_label: false,
  label_name: '',
  label_is_certified: false,
  is_future_commitment: false,
  target_date: '',
  has_independent_verification: false,
};

const STEPS = [
  { key: 'text', label: 'Texte et support' },
  { key: 'proof', label: 'Preuves' },
  { key: 'labels', label: 'Labels' },
  { key: 'future', label: 'Engagements futurs' },
];

// ---------------------------------------------------------------------------
// Composant principal
// ---------------------------------------------------------------------------

export default function ClaimForm() {
  const { audit_id } = useParams();
  const navigate = useNavigate();

  // Audit info
  const [audit, setAudit] = useState(null);
  const [loadingAudit, setLoadingAudit] = useState(true);

  // Claims list
  const [claims, setClaims] = useState([]);
  const [loadingClaims, setLoadingClaims] = useState(true);

  // Form state
  const [showForm, setShowForm] = useState(false);
  const [editingClaimId, setEditingClaimId] = useState(null);
  const [form, setForm] = useState({ ...EMPTY_FORM });
  const [currentStep, setCurrentStep] = useState(0);
  const [submitting, setSubmitting] = useState(false);

  // Analysis
  const [analyzing, setAnalyzing] = useState(false);

  // Errors
  const [error, setError] = useState(null);

  // -----------------------------------------------------------------------
  // Data fetching
  // -----------------------------------------------------------------------

  const fetchAudit = useCallback(async () => {
    try {
      const res = await api.get(`/audits/${audit_id}`);
      setAudit(res.data);
    } catch {
      setError("Impossible de charger les informations de l'audit.");
    } finally {
      setLoadingAudit(false);
    }
  }, [audit_id]);

  const fetchClaims = useCallback(async () => {
    try {
      const res = await api.get(`/audits/${audit_id}/claims`);
      setClaims(res.data);
    } catch {
      setError('Impossible de charger les allegations.');
    } finally {
      setLoadingClaims(false);
    }
  }, [audit_id]);

  useEffect(() => {
    fetchAudit();
    fetchClaims();
  }, [fetchAudit, fetchClaims]);

  // -----------------------------------------------------------------------
  // Form helpers
  // -----------------------------------------------------------------------

  const updateField = (field, value) => {
    setForm((prev) => ({ ...prev, [field]: value }));
  };

  const openNewForm = () => {
    setForm({ ...EMPTY_FORM });
    setEditingClaimId(null);
    setCurrentStep(0);
    setShowForm(true);
  };

  const openEditForm = (claim) => {
    setForm({
      claim_text: claim.claim_text || '',
      support_type: claim.support_type || 'web',
      scope: claim.scope || 'produit',
      product_name: claim.product_name || '',
      has_proof: claim.has_proof || false,
      proof_description: claim.proof_description || '',
      proof_type: claim.proof_type || 'aucune',
      has_label: claim.has_label || false,
      label_name: claim.label_name || '',
      label_is_certified: claim.label_is_certified || false,
      is_future_commitment: claim.is_future_commitment || false,
      target_date: claim.target_date || '',
      has_independent_verification: claim.has_independent_verification || false,
    });
    setEditingClaimId(claim.id);
    setCurrentStep(0);
    setShowForm(true);
  };

  const closeForm = () => {
    setShowForm(false);
    setEditingClaimId(null);
    setForm({ ...EMPTY_FORM });
    setCurrentStep(0);
  };

  // -----------------------------------------------------------------------
  // CRUD
  // -----------------------------------------------------------------------

  const handleSubmit = async () => {
    if (!form.claim_text.trim()) {
      setError("Le texte de l'allegation est requis.");
      setCurrentStep(0);
      return;
    }

    setSubmitting(true);
    setError(null);

    const payload = {
      ...form,
      product_name: form.scope === 'produit' ? form.product_name : null,
      proof_description: form.has_proof ? form.proof_description : null,
      proof_type: form.has_proof ? form.proof_type : 'aucune',
      label_name: form.has_label ? form.label_name : null,
      label_is_certified: form.has_label ? form.label_is_certified : false,
      target_date: form.is_future_commitment && form.target_date ? form.target_date : null,
      has_independent_verification: form.is_future_commitment
        ? form.has_independent_verification
        : false,
    };

    try {
      if (editingClaimId) {
        await api.put(`/claims/${editingClaimId}`, payload);
      } else {
        await api.post(`/audits/${audit_id}/claims`, payload);
      }
      closeForm();
      await fetchClaims();
    } catch {
      setError(
        editingClaimId
          ? "Erreur lors de la modification de l'allegation."
          : "Erreur lors de l'ajout de l'allegation."
      );
    } finally {
      setSubmitting(false);
    }
  };

  const handleDelete = async (claimId) => {
    if (!window.confirm('Supprimer cette allegation ?')) return;
    setError(null);
    try {
      await api.delete(`/claims/${claimId}`);
      await fetchClaims();
    } catch {
      setError("Erreur lors de la suppression de l'allegation.");
    }
  };

  // -----------------------------------------------------------------------
  // Analyse
  // -----------------------------------------------------------------------

  const handleAnalyze = async () => {
    if (claims.length === 0) {
      setError("Ajoutez au moins une allegation avant de lancer l'analyse.");
      return;
    }
    setAnalyzing(true);
    setError(null);
    try {
      await api.post(`/audits/${audit_id}/analyze`);
      navigate(`/audits/${audit_id}/results`);
    } catch {
      setError("Erreur lors du lancement de l'analyse.");
    } finally {
      setAnalyzing(false);
    }
  };

  // -----------------------------------------------------------------------
  // Step navigation
  // -----------------------------------------------------------------------

  const canGoNext = currentStep < STEPS.length - 1;
  const canGoPrev = currentStep > 0;
  const isLastStep = currentStep === STEPS.length - 1;

  // -----------------------------------------------------------------------
  // Render helpers
  // -----------------------------------------------------------------------

  const supportLabel = (value) =>
    SUPPORT_TYPE_OPTIONS.find((o) => o.value === value)?.label ?? value;

  const scopeLabel = (value) =>
    SCOPE_OPTIONS.find((o) => o.value === value)?.label ?? value;

  // -----------------------------------------------------------------------
  // Loading state
  // -----------------------------------------------------------------------

  if (loadingAudit || loadingClaims) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="inline-block h-10 w-10 animate-spin rounded-full border-4 border-[#1B5E20] border-t-transparent" />
          <p className="mt-4 text-gray-600">Chargement...</p>
        </div>
      </div>
    );
  }

  // -----------------------------------------------------------------------
  // Render
  // -----------------------------------------------------------------------

  return (
    <div className="min-h-screen bg-gray-50">
      {/* ----------------------------------------------------------------- */}
      {/* Header bar                                                        */}
      {/* ----------------------------------------------------------------- */}
      <header className="bg-[#1B5E20] text-white shadow-lg">
        <div className="mx-auto max-w-5xl px-4 py-6 sm:px-6 lg:px-8">
          <button
            onClick={() => navigate(-1)}
            className="mb-3 inline-flex items-center text-sm text-green-200 hover:text-white transition-colors"
          >
            <svg className="mr-1.5 h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
            </svg>
            Retour
          </button>

          {audit ? (
            <>
              <h1 className="text-2xl font-bold">
                Audit : {audit.company_name}
              </h1>
              <div className="mt-2 flex flex-wrap gap-4 text-sm text-green-100">
                <span>Secteur : {audit.sector}</span>
                {audit.website_url && <span>Site : {audit.website_url}</span>}
                <span className="inline-flex items-center rounded-full bg-white/20 px-2.5 py-0.5 text-xs font-medium">
                  {audit.status === 'draft'
                    ? 'Brouillon'
                    : audit.status === 'in_progress'
                      ? 'En cours'
                      : 'Termine'}
                </span>
              </div>
            </>
          ) : (
            <h1 className="text-2xl font-bold">Audit introuvable</h1>
          )}
        </div>
      </header>

      <main className="mx-auto max-w-5xl px-4 py-8 sm:px-6 lg:px-8">
        {/* --------------------------------------------------------------- */}
        {/* Error banner                                                    */}
        {/* --------------------------------------------------------------- */}
        {error && (
          <div className="mb-6 rounded-lg border border-red-300 bg-red-50 px-4 py-3 text-sm text-red-700 flex items-start gap-2">
            <svg className="mt-0.5 h-5 w-5 flex-shrink-0 text-red-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            <span>{error}</span>
            <button onClick={() => setError(null)} className="ml-auto text-red-500 hover:text-red-700">
              <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
        )}

        {/* --------------------------------------------------------------- */}
        {/* Action bar                                                       */}
        {/* --------------------------------------------------------------- */}
        <div className="mb-6 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
          <h2 className="text-lg font-semibold text-gray-800">
            Allegations environnementales ({claims.length})
          </h2>
          <div className="flex gap-3">
            <button
              onClick={openNewForm}
              disabled={showForm}
              className="inline-flex items-center rounded-lg bg-[#1B5E20] px-4 py-2.5 text-sm font-medium text-white shadow-sm hover:bg-[#2E7D32] transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <svg className="mr-2 h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
              </svg>
              Ajouter une allegation
            </button>
            <button
              onClick={handleAnalyze}
              disabled={analyzing || claims.length === 0}
              className="inline-flex items-center rounded-lg bg-[#2E7D32] px-4 py-2.5 text-sm font-medium text-white shadow-sm hover:bg-[#1B5E20] transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {analyzing ? (
                <>
                  <div className="mr-2 h-4 w-4 animate-spin rounded-full border-2 border-white border-t-transparent" />
                  Analyse en cours...
                </>
              ) : (
                <>
                  <svg className="mr-2 h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                  </svg>
                  Lancer l'analyse
                </>
              )}
            </button>
          </div>
        </div>

        {/* --------------------------------------------------------------- */}
        {/* Multi-step claim form                                           */}
        {/* --------------------------------------------------------------- */}
        {showForm && (
          <div className="mb-8 rounded-xl border border-gray-200 bg-white shadow-sm">
            {/* Form header */}
            <div className="border-b border-gray-200 bg-gray-50 px-6 py-4 rounded-t-xl">
              <div className="flex items-center justify-between">
                <h3 className="text-base font-semibold text-gray-800">
                  {editingClaimId ? "Modifier l'allegation" : 'Nouvelle allegation'}
                </h3>
                <button onClick={closeForm} className="text-gray-400 hover:text-gray-600 transition-colors">
                  <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </button>
              </div>

              {/* Stepper */}
              <nav className="mt-4 flex gap-1">
                {STEPS.map((step, idx) => (
                  <button
                    key={step.key}
                    type="button"
                    onClick={() => setCurrentStep(idx)}
                    className={`flex-1 rounded-lg px-3 py-2 text-xs font-medium transition-colors ${
                      idx === currentStep
                        ? 'bg-[#1B5E20] text-white shadow-sm'
                        : idx < currentStep
                          ? 'bg-[#2E7D32]/10 text-[#1B5E20]'
                          : 'bg-gray-100 text-gray-500'
                    }`}
                  >
                    <span className="hidden sm:inline">{idx + 1}. </span>
                    {step.label}
                  </button>
                ))}
              </nav>
            </div>

            {/* Form body */}
            <div className="px-6 py-6">
              {/* Step 1 -- Texte et support */}
              {currentStep === 0 && (
                <div className="space-y-5">
                  <div>
                    <label htmlFor="claim_text" className="block text-sm font-medium text-gray-700 mb-1">
                      Texte de l'allegation <span className="text-red-500">*</span>
                    </label>
                    <textarea
                      id="claim_text"
                      rows={4}
                      value={form.claim_text}
                      onChange={(e) => updateField('claim_text', e.target.value)}
                      placeholder='Ex: "Notre emballage est 100% recyclable et eco-responsable"'
                      className="block w-full rounded-lg border border-gray-300 px-3 py-2 text-sm shadow-sm placeholder:text-gray-400 focus:border-[#1B5E20] focus:ring-1 focus:ring-[#1B5E20] focus:outline-none"
                    />
                    <p className="mt-1 text-xs text-gray-500">
                      Copiez le texte exact tel qu'il apparait sur le support.
                    </p>
                  </div>

                  <div className="grid grid-cols-1 gap-5 sm:grid-cols-2">
                    <div>
                      <label htmlFor="support_type" className="block text-sm font-medium text-gray-700 mb-1">
                        Type de support
                      </label>
                      <select
                        id="support_type"
                        value={form.support_type}
                        onChange={(e) => updateField('support_type', e.target.value)}
                        className="block w-full rounded-lg border border-gray-300 px-3 py-2 text-sm shadow-sm focus:border-[#1B5E20] focus:ring-1 focus:ring-[#1B5E20] focus:outline-none"
                      >
                        {SUPPORT_TYPE_OPTIONS.map((opt) => (
                          <option key={opt.value} value={opt.value}>
                            {opt.label}
                          </option>
                        ))}
                      </select>
                    </div>

                    <div>
                      <label htmlFor="scope" className="block text-sm font-medium text-gray-700 mb-1">
                        Portee de l'allegation
                      </label>
                      <select
                        id="scope"
                        value={form.scope}
                        onChange={(e) => updateField('scope', e.target.value)}
                        className="block w-full rounded-lg border border-gray-300 px-3 py-2 text-sm shadow-sm focus:border-[#1B5E20] focus:ring-1 focus:ring-[#1B5E20] focus:outline-none"
                      >
                        {SCOPE_OPTIONS.map((opt) => (
                          <option key={opt.value} value={opt.value}>
                            {opt.label}
                          </option>
                        ))}
                      </select>
                    </div>
                  </div>

                  {form.scope === 'produit' && (
                    <div>
                      <label htmlFor="product_name" className="block text-sm font-medium text-gray-700 mb-1">
                        Nom du produit
                      </label>
                      <input
                        id="product_name"
                        type="text"
                        value={form.product_name}
                        onChange={(e) => updateField('product_name', e.target.value)}
                        placeholder="Ex: Shampoing solide BioClean"
                        className="block w-full rounded-lg border border-gray-300 px-3 py-2 text-sm shadow-sm placeholder:text-gray-400 focus:border-[#1B5E20] focus:ring-1 focus:ring-[#1B5E20] focus:outline-none"
                      />
                    </div>
                  )}
                </div>
              )}

              {/* Step 2 -- Preuves */}
              {currentStep === 1 && (
                <div className="space-y-5">
                  <label className="flex items-center gap-3 cursor-pointer">
                    <input
                      type="checkbox"
                      checked={form.has_proof}
                      onChange={(e) => updateField('has_proof', e.target.checked)}
                      className="h-4 w-4 rounded border-gray-300 text-[#1B5E20] focus:ring-[#1B5E20]"
                    />
                    <span className="text-sm font-medium text-gray-700">
                      L'entreprise dispose de preuves pour etayer cette allegation
                    </span>
                  </label>

                  {form.has_proof && (
                    <div className="ml-7 space-y-5 border-l-2 border-[#2E7D32]/20 pl-5">
                      <div>
                        <label htmlFor="proof_type" className="block text-sm font-medium text-gray-700 mb-1">
                          Type de preuve
                        </label>
                        <select
                          id="proof_type"
                          value={form.proof_type}
                          onChange={(e) => updateField('proof_type', e.target.value)}
                          className="block w-full rounded-lg border border-gray-300 px-3 py-2 text-sm shadow-sm focus:border-[#1B5E20] focus:ring-1 focus:ring-[#1B5E20] focus:outline-none"
                        >
                          {PROOF_TYPE_OPTIONS.map((opt) => (
                            <option key={opt.value} value={opt.value}>
                              {opt.label}
                            </option>
                          ))}
                        </select>
                      </div>

                      <div>
                        <label htmlFor="proof_description" className="block text-sm font-medium text-gray-700 mb-1">
                          Description de la preuve
                        </label>
                        <textarea
                          id="proof_description"
                          rows={3}
                          value={form.proof_description}
                          onChange={(e) => updateField('proof_description', e.target.value)}
                          placeholder="Decrivez la preuve fournie (nom du certificat, reference du rapport, etc.)"
                          className="block w-full rounded-lg border border-gray-300 px-3 py-2 text-sm shadow-sm placeholder:text-gray-400 focus:border-[#1B5E20] focus:ring-1 focus:ring-[#1B5E20] focus:outline-none"
                        />
                      </div>
                    </div>
                  )}

                  {!form.has_proof && (
                    <div className="rounded-lg border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-700">
                      <strong>Attention :</strong> L'absence de preuve entrainera un verdict "Non conforme"
                      sur le critere de tracabilite (Regle 6 - Directive EmpCo).
                    </div>
                  )}
                </div>
              )}

              {/* Step 3 -- Labels */}
              {currentStep === 2 && (
                <div className="space-y-5">
                  <label className="flex items-center gap-3 cursor-pointer">
                    <input
                      type="checkbox"
                      checked={form.has_label}
                      onChange={(e) => updateField('has_label', e.target.checked)}
                      className="h-4 w-4 rounded border-gray-300 text-[#1B5E20] focus:ring-[#1B5E20]"
                    />
                    <span className="text-sm font-medium text-gray-700">
                      Un label ou logo environnemental est associe a cette allegation
                    </span>
                  </label>

                  {form.has_label && (
                    <div className="ml-7 space-y-5 border-l-2 border-[#2E7D32]/20 pl-5">
                      <div>
                        <label htmlFor="label_name" className="block text-sm font-medium text-gray-700 mb-1">
                          Nom du label
                        </label>
                        <input
                          id="label_name"
                          type="text"
                          value={form.label_name}
                          onChange={(e) => updateField('label_name', e.target.value)}
                          placeholder="Ex: EU Ecolabel, FSC, AB, etc."
                          className="block w-full rounded-lg border border-gray-300 px-3 py-2 text-sm shadow-sm placeholder:text-gray-400 focus:border-[#1B5E20] focus:ring-1 focus:ring-[#1B5E20] focus:outline-none"
                        />
                      </div>

                      <label className="flex items-center gap-3 cursor-pointer">
                        <input
                          type="checkbox"
                          checked={form.label_is_certified}
                          onChange={(e) => updateField('label_is_certified', e.target.checked)}
                          className="h-4 w-4 rounded border-gray-300 text-[#1B5E20] focus:ring-[#1B5E20]"
                        />
                        <span className="text-sm text-gray-700">
                          Certifie par un organisme tiers independant
                        </span>
                      </label>

                      {!form.label_is_certified && (
                        <div className="rounded-lg border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-700">
                          <strong>Attention :</strong> Les labels auto-decernes sont interdits par la
                          Directive EmpCo (EU 2024/825). Ce label sera juge "Non conforme".
                        </div>
                      )}
                    </div>
                  )}

                  {!form.has_label && (
                    <p className="text-sm text-gray-500">
                      Si aucun label n'est utilise, ce critere sera marque "Non applicable".
                    </p>
                  )}
                </div>
              )}

              {/* Step 4 -- Engagements futurs */}
              {currentStep === 3 && (
                <div className="space-y-5">
                  <label className="flex items-center gap-3 cursor-pointer">
                    <input
                      type="checkbox"
                      checked={form.is_future_commitment}
                      onChange={(e) => updateField('is_future_commitment', e.target.checked)}
                      className="h-4 w-4 rounded border-gray-300 text-[#1B5E20] focus:ring-[#1B5E20]"
                    />
                    <span className="text-sm font-medium text-gray-700">
                      Cette allegation porte sur un engagement futur
                    </span>
                  </label>

                  {form.is_future_commitment && (
                    <div className="ml-7 space-y-5 border-l-2 border-[#2E7D32]/20 pl-5">
                      <div>
                        <label htmlFor="target_date" className="block text-sm font-medium text-gray-700 mb-1">
                          Date cible de realisation
                        </label>
                        <input
                          id="target_date"
                          type="date"
                          value={form.target_date}
                          onChange={(e) => updateField('target_date', e.target.value)}
                          className="block w-full rounded-lg border border-gray-300 px-3 py-2 text-sm shadow-sm focus:border-[#1B5E20] focus:ring-1 focus:ring-[#1B5E20] focus:outline-none"
                        />
                      </div>

                      <label className="flex items-center gap-3 cursor-pointer">
                        <input
                          type="checkbox"
                          checked={form.has_independent_verification}
                          onChange={(e) =>
                            updateField('has_independent_verification', e.target.checked)
                          }
                          className="h-4 w-4 rounded border-gray-300 text-[#1B5E20] focus:ring-[#1B5E20]"
                        />
                        <span className="text-sm text-gray-700">
                          Un plan de suivi independant est en place
                        </span>
                      </label>

                      {(!form.target_date || !form.has_independent_verification) && (
                        <div className="rounded-lg border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-700">
                          <strong>Attention :</strong> Un engagement futur sans date cible et sans
                          verification independante sera juge "Non conforme" (Regle 5 - Directive EmpCo).
                        </div>
                      )}
                    </div>
                  )}

                  {!form.is_future_commitment && (
                    <p className="text-sm text-gray-500">
                      Si l'allegation ne porte pas sur un engagement futur, ce critere sera marque "Non applicable".
                    </p>
                  )}
                </div>
              )}
            </div>

            {/* Form footer -- navigation & submit */}
            <div className="flex items-center justify-between border-t border-gray-200 bg-gray-50 px-6 py-4 rounded-b-xl">
              <button
                type="button"
                onClick={() => setCurrentStep((s) => s - 1)}
                disabled={!canGoPrev}
                className="inline-flex items-center rounded-lg border border-gray-300 bg-white px-4 py-2 text-sm font-medium text-gray-700 shadow-sm hover:bg-gray-50 transition-colors disabled:opacity-40 disabled:cursor-not-allowed"
              >
                <svg className="mr-1.5 h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
                </svg>
                Precedent
              </button>

              <span className="text-xs text-gray-500">
                Etape {currentStep + 1} / {STEPS.length}
              </span>

              {isLastStep ? (
                <button
                  type="button"
                  onClick={handleSubmit}
                  disabled={submitting}
                  className="inline-flex items-center rounded-lg bg-[#1B5E20] px-5 py-2 text-sm font-medium text-white shadow-sm hover:bg-[#2E7D32] transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {submitting ? (
                    <>
                      <div className="mr-2 h-4 w-4 animate-spin rounded-full border-2 border-white border-t-transparent" />
                      Enregistrement...
                    </>
                  ) : editingClaimId ? (
                    'Enregistrer les modifications'
                  ) : (
                    "Ajouter l'allegation"
                  )}
                </button>
              ) : (
                <button
                  type="button"
                  onClick={() => setCurrentStep((s) => s + 1)}
                  disabled={!canGoNext}
                  className="inline-flex items-center rounded-lg bg-[#1B5E20] px-4 py-2 text-sm font-medium text-white shadow-sm hover:bg-[#2E7D32] transition-colors disabled:opacity-40 disabled:cursor-not-allowed"
                >
                  Suivant
                  <svg className="ml-1.5 h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                  </svg>
                </button>
              )}
            </div>
          </div>
        )}

        {/* --------------------------------------------------------------- */}
        {/* Claims list                                                     */}
        {/* --------------------------------------------------------------- */}
        {claims.length === 0 && !showForm ? (
          <div className="rounded-xl border-2 border-dashed border-gray-300 bg-white py-16 text-center">
            <svg
              className="mx-auto h-12 w-12 text-gray-400"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={1.5}
                d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
              />
            </svg>
            <h3 className="mt-3 text-sm font-semibold text-gray-800">Aucune allegation</h3>
            <p className="mt-1 text-sm text-gray-500">
              Commencez par ajouter les allegations environnementales a auditer.
            </p>
            <button
              onClick={openNewForm}
              className="mt-6 inline-flex items-center rounded-lg bg-[#1B5E20] px-4 py-2.5 text-sm font-medium text-white shadow-sm hover:bg-[#2E7D32] transition-colors"
            >
              <svg className="mr-2 h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
              </svg>
              Ajouter une allegation
            </button>
          </div>
        ) : (
          <div className="space-y-4">
            {claims.map((claim, idx) => (
              <div
                key={claim.id}
                className="rounded-xl border border-gray-200 bg-white shadow-sm hover:shadow-md transition-shadow"
              >
                <div className="px-6 py-5">
                  {/* Claim header */}
                  <div className="flex items-start justify-between gap-4">
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-3 mb-2">
                        <span className="inline-flex h-6 w-6 flex-shrink-0 items-center justify-center rounded-full bg-[#1B5E20]/10 text-xs font-bold text-[#1B5E20]">
                          {idx + 1}
                        </span>
                        <div className="flex flex-wrap items-center gap-2">
                          <span className="inline-flex items-center rounded-full bg-gray-100 px-2.5 py-0.5 text-xs font-medium text-gray-600">
                            {supportLabel(claim.support_type)}
                          </span>
                          <span className="inline-flex items-center rounded-full bg-gray-100 px-2.5 py-0.5 text-xs font-medium text-gray-600">
                            {scopeLabel(claim.scope)}
                          </span>
                          {claim.product_name && (
                            <span className="inline-flex items-center rounded-full bg-[#2E7D32]/10 px-2.5 py-0.5 text-xs font-medium text-[#2E7D32]">
                              {claim.product_name}
                            </span>
                          )}
                          {claim.overall_verdict && (
                            <span
                              className={`inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-semibold ${
                                VERDICT_STYLES[claim.overall_verdict] || 'bg-gray-100 text-gray-600'
                              }`}
                            >
                              {VERDICT_LABELS[claim.overall_verdict] || claim.overall_verdict}
                            </span>
                          )}
                        </div>
                      </div>

                      <p className="text-sm text-gray-800 leading-relaxed">
                        &laquo; {claim.claim_text} &raquo;
                      </p>

                      {/* Metadata pills */}
                      <div className="mt-3 flex flex-wrap gap-2 text-xs text-gray-500">
                        {claim.has_proof && (
                          <span className="inline-flex items-center gap-1">
                            <svg className="h-3.5 w-3.5 text-[#2E7D32]" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4" />
                            </svg>
                            Preuve fournie
                          </span>
                        )}
                        {claim.has_label && (
                          <span className="inline-flex items-center gap-1">
                            <svg className="h-3.5 w-3.5 text-[#2E7D32]" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 7h.01M7 3h5a1.99 1.99 0 011.414.586l7 7a2 2 0 010 2.828l-7 7a2 2 0 01-2.828 0l-7-7A1.99 1.99 0 013 12V7a4 4 0 014-4z" />
                            </svg>
                            Label : {claim.label_name || 'N/A'}
                          </span>
                        )}
                        {claim.is_future_commitment && (
                          <span className="inline-flex items-center gap-1">
                            <svg className="h-3.5 w-3.5 text-[#2E7D32]" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
                            </svg>
                            Engagement futur{claim.target_date ? ` (${claim.target_date})` : ''}
                          </span>
                        )}
                      </div>
                    </div>

                    {/* Actions */}
                    <div className="flex flex-shrink-0 gap-1">
                      <button
                        onClick={() => openEditForm(claim)}
                        disabled={showForm}
                        title="Modifier"
                        className="rounded-lg p-2 text-gray-400 hover:bg-gray-100 hover:text-[#1B5E20] transition-colors disabled:opacity-40 disabled:cursor-not-allowed"
                      >
                        <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                          <path
                            strokeLinecap="round"
                            strokeLinejoin="round"
                            strokeWidth={2}
                            d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z"
                          />
                        </svg>
                      </button>
                      <button
                        onClick={() => handleDelete(claim.id)}
                        disabled={showForm}
                        title="Supprimer"
                        className="rounded-lg p-2 text-gray-400 hover:bg-red-50 hover:text-red-600 transition-colors disabled:opacity-40 disabled:cursor-not-allowed"
                      >
                        <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                          <path
                            strokeLinecap="round"
                            strokeLinejoin="round"
                            strokeWidth={2}
                            d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"
                          />
                        </svg>
                      </button>
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}

        {/* --------------------------------------------------------------- */}
        {/* Bottom analyze CTA (visible when claims exist)                  */}
        {/* --------------------------------------------------------------- */}
        {claims.length > 0 && !showForm && (
          <div className="mt-8 rounded-xl border border-[#2E7D32]/30 bg-[#1B5E20]/5 px-6 py-5 text-center">
            <p className="mb-3 text-sm text-gray-700">
              <strong>{claims.length}</strong> allegation{claims.length > 1 ? 's' : ''} prete
              {claims.length > 1 ? 's' : ''} a etre analysee{claims.length > 1 ? 's' : ''} selon
              les 6 criteres de la Directive EmpCo.
            </p>
            <button
              onClick={handleAnalyze}
              disabled={analyzing}
              className="inline-flex items-center rounded-lg bg-[#1B5E20] px-6 py-3 text-sm font-semibold text-white shadow-md hover:bg-[#2E7D32] transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {analyzing ? (
                <>
                  <div className="mr-2 h-4 w-4 animate-spin rounded-full border-2 border-white border-t-transparent" />
                  Analyse en cours...
                </>
              ) : (
                <>
                  <svg className="mr-2 h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M9 5l7 7-7 7"
                    />
                  </svg>
                  Lancer l'analyse
                </>
              )}
            </button>
          </div>
        )}
      </main>
    </div>
  );
}
