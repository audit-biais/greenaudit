import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import api from '../api/client';

const SECTORS = [
  { value: 'e-commerce', label: 'E-commerce' },
  { value: 'cosmetiques', label: 'Cosmétiques' },
  { value: 'alimentaire', label: 'Alimentaire' },
  { value: 'textile', label: 'Textile' },
  { value: 'services', label: 'Services' },
  { value: 'autre', label: 'Autre' },
];

const inputCls = 'w-full rounded-lg border border-gray-200 px-4 py-3 text-sm text-gray-900 placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-[#1a5c3a] focus:border-transparent transition bg-white';

export default function NewAudit() {
  const navigate = useNavigate();
  const [form, setForm] = useState({ company_name: '', sector: '', website_url: '', contact_email: '' });
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState(null);

  function handleChange(e) {
    const { name, value } = e.target;
    setForm((prev) => ({ ...prev, [name]: value }));
  }

  async function handleSubmit(e) {
    e.preventDefault();
    setError(null);
    if (!form.company_name.trim()) { setError("Le nom de l'entreprise est obligatoire."); return; }
    if (!form.sector) { setError('Veuillez sélectionner un secteur.'); return; }
    try {
      setSubmitting(true);
      const res = await api.post('/audits', {
        company_name: form.company_name.trim(),
        sector: form.sector,
        website_url: form.website_url.trim() || undefined,
        contact_email: form.contact_email.trim() || undefined,
      });
      navigate(`/audits/${res.data.id}`);
    } catch (err) {
      setError(err.response?.data?.detail || "Impossible de créer l'audit. Veuillez réessayer.");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="max-w-xl mx-auto">
      <div className="mb-8">
        <p className="text-xs font-semibold uppercase tracking-widest text-[#1a5c3a] mb-1">Nouveau</p>
        <h1 className="text-2xl font-black text-gray-900">Créer un audit</h1>
        <p className="mt-1 text-sm text-gray-500">Renseignez les informations de l'entreprise à auditer</p>
      </div>

      {error && (
        <div className="mb-6 p-4 bg-red-50 border border-red-100 rounded-xl text-red-700 text-sm flex items-center justify-between">
          <span>{error}</span>
          <button onClick={() => setError(null)} className="text-red-400 hover:text-red-600 font-medium">Fermer</button>
        </div>
      )}

      <form onSubmit={handleSubmit} className="bg-white rounded-2xl border border-gray-100 p-8 space-y-5">
        <div>
          <label htmlFor="company_name" className="block text-sm font-medium text-gray-700 mb-1.5">
            Nom de l'entreprise <span className="text-red-500">*</span>
          </label>
          <input type="text" id="company_name" name="company_name" value={form.company_name}
            onChange={handleChange} placeholder="Ex : GreenCo SAS" required className={inputCls} />
        </div>

        <div>
          <label htmlFor="sector" className="block text-sm font-medium text-gray-700 mb-1.5">
            Secteur d'activité <span className="text-red-500">*</span>
          </label>
          <select id="sector" name="sector" value={form.sector} onChange={handleChange}
            required className={inputCls + ' cursor-pointer'}>
            <option value="" disabled>Sélectionnez un secteur</option>
            {SECTORS.map((s) => <option key={s.value} value={s.value}>{s.label}</option>)}
          </select>
        </div>

        <div>
          <label htmlFor="website_url" className="block text-sm font-medium text-gray-700 mb-1.5">
            Site web <span className="text-xs text-gray-400 font-normal">(optionnel)</span>
          </label>
          <input type="url" id="website_url" name="website_url" value={form.website_url}
            onChange={handleChange} placeholder="https://www.example.com" className={inputCls} />
        </div>

        <div>
          <label htmlFor="contact_email" className="block text-sm font-medium text-gray-700 mb-1.5">
            Email de contact <span className="text-xs text-gray-400 font-normal">(optionnel)</span>
          </label>
          <input type="email" id="contact_email" name="contact_email" value={form.contact_email}
            onChange={handleChange} placeholder="contact@example.com" className={inputCls} />
        </div>

        <div className="flex items-center justify-end gap-3 pt-2 border-t border-gray-50">
          <button type="button" onClick={() => navigate('/dashboard')} disabled={submitting}
            className="px-5 py-2.5 rounded-full text-sm font-medium text-gray-600 bg-white border border-gray-200 hover:bg-gray-50 transition-colors disabled:opacity-50">
            Annuler
          </button>
          <button type="submit" disabled={submitting}
            className="px-5 py-2.5 rounded-full text-sm font-semibold text-white bg-[#1a5c3a] hover:bg-[#14472d] transition-colors disabled:opacity-60">
            {submitting ? 'Création...' : "Créer l'audit →"}
          </button>
        </div>
      </form>
    </div>
  );
}
