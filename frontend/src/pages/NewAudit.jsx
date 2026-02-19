import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import api from '../api/client';

const SECTORS = [
  { value: 'e-commerce', label: 'E-commerce' },
  { value: 'cosmetiques', label: 'Cosm\u00e9tiques' },
  { value: 'alimentaire', label: 'Alimentaire' },
  { value: 'textile', label: 'Textile' },
  { value: 'services', label: 'Services' },
  { value: 'autre', label: 'Autre' },
];

export default function NewAudit() {
  const navigate = useNavigate();

  const [form, setForm] = useState({
    company_name: '',
    sector: '',
    website_url: '',
    contact_email: '',
  });
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState(null);

  function handleChange(e) {
    const { name, value } = e.target;
    setForm((prev) => ({ ...prev, [name]: value }));
  }

  async function handleSubmit(e) {
    e.preventDefault();
    setError(null);

    if (!form.company_name.trim()) {
      setError("Le nom de l'entreprise est obligatoire.");
      return;
    }
    if (!form.sector) {
      setError('Veuillez s\u00e9lectionner un secteur.');
      return;
    }

    try {
      setSubmitting(true);
      const response = await api.post('/audits', {
        company_name: form.company_name.trim(),
        sector: form.sector,
        website_url: form.website_url.trim() || undefined,
        contact_email: form.contact_email.trim() || undefined,
      });
      navigate(`/audits/${response.data.id}`);
    } catch (err) {
      const message =
        err.response?.data?.detail || "Impossible de cr\u00e9er l'audit. Veuillez r\u00e9essayer.";
      setError(message);
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm border-b border-gray-200">
        <div className="max-w-3xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <h1 className="text-2xl font-bold" style={{ color: '#1B5E20' }}>
            Nouvel audit
          </h1>
          <p className="mt-1 text-sm text-gray-500">
            Renseignez les informations de l'entreprise \u00e0 auditer
          </p>
        </div>
      </header>

      {/* Form */}
      <main className="max-w-3xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
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

        <form
          onSubmit={handleSubmit}
          className="bg-white rounded-xl shadow-sm border border-gray-200 p-6 sm:p-8"
        >
          {/* Company name */}
          <div className="mb-6">
            <label
              htmlFor="company_name"
              className="block text-sm font-medium text-gray-700 mb-1.5"
            >
              Nom de l'entreprise <span className="text-red-500">*</span>
            </label>
            <input
              type="text"
              id="company_name"
              name="company_name"
              value={form.company_name}
              onChange={handleChange}
              placeholder="Ex : GreenCo SAS"
              required
              className="w-full rounded-lg border border-gray-300 px-4 py-2.5 text-sm text-gray-900 placeholder-gray-400 focus:outline-none focus:ring-2 focus:border-transparent"
              style={{ '--tw-ring-color': '#2E7D32' }}
              onFocus={(e) => (e.target.style.boxShadow = '0 0 0 2px #2E7D32')}
              onBlur={(e) => (e.target.style.boxShadow = 'none')}
            />
          </div>

          {/* Sector */}
          <div className="mb-6">
            <label
              htmlFor="sector"
              className="block text-sm font-medium text-gray-700 mb-1.5"
            >
              Secteur d'activit\u00e9 <span className="text-red-500">*</span>
            </label>
            <select
              id="sector"
              name="sector"
              value={form.sector}
              onChange={handleChange}
              required
              className="w-full rounded-lg border border-gray-300 px-4 py-2.5 text-sm text-gray-900 bg-white focus:outline-none focus:ring-2 focus:border-transparent cursor-pointer"
              onFocus={(e) => (e.target.style.boxShadow = '0 0 0 2px #2E7D32')}
              onBlur={(e) => (e.target.style.boxShadow = 'none')}
            >
              <option value="" disabled>
                S\u00e9lectionnez un secteur
              </option>
              {SECTORS.map((s) => (
                <option key={s.value} value={s.value}>
                  {s.label}
                </option>
              ))}
            </select>
          </div>

          {/* Website URL */}
          <div className="mb-6">
            <label
              htmlFor="website_url"
              className="block text-sm font-medium text-gray-700 mb-1.5"
            >
              Site web
            </label>
            <input
              type="url"
              id="website_url"
              name="website_url"
              value={form.website_url}
              onChange={handleChange}
              placeholder="https://www.example.com"
              className="w-full rounded-lg border border-gray-300 px-4 py-2.5 text-sm text-gray-900 placeholder-gray-400 focus:outline-none focus:ring-2 focus:border-transparent"
              onFocus={(e) => (e.target.style.boxShadow = '0 0 0 2px #2E7D32')}
              onBlur={(e) => (e.target.style.boxShadow = 'none')}
            />
          </div>

          {/* Contact email */}
          <div className="mb-8">
            <label
              htmlFor="contact_email"
              className="block text-sm font-medium text-gray-700 mb-1.5"
            >
              Email de contact
            </label>
            <input
              type="email"
              id="contact_email"
              name="contact_email"
              value={form.contact_email}
              onChange={handleChange}
              placeholder="contact@example.com"
              className="w-full rounded-lg border border-gray-300 px-4 py-2.5 text-sm text-gray-900 placeholder-gray-400 focus:outline-none focus:ring-2 focus:border-transparent"
              onFocus={(e) => (e.target.style.boxShadow = '0 0 0 2px #2E7D32')}
              onBlur={(e) => (e.target.style.boxShadow = 'none')}
            />
          </div>

          {/* Actions */}
          <div className="flex items-center justify-end gap-3 pt-4 border-t border-gray-100">
            <button
              type="button"
              onClick={() => navigate('/')}
              disabled={submitting}
              className="px-5 py-2.5 rounded-lg text-sm font-medium text-gray-700 bg-white border border-gray-300 hover:bg-gray-50 transition-colors duration-150 cursor-pointer disabled:opacity-50"
            >
              Annuler
            </button>
            <button
              type="submit"
              disabled={submitting}
              className="px-5 py-2.5 rounded-lg text-sm font-medium text-white transition-colors duration-150 cursor-pointer disabled:opacity-60"
              style={{ backgroundColor: '#1B5E20' }}
              onMouseEnter={(e) => {
                if (!submitting) e.currentTarget.style.backgroundColor = '#2E7D32';
              }}
              onMouseLeave={(e) => {
                if (!submitting) e.currentTarget.style.backgroundColor = '#1B5E20';
              }}
            >
              {submitting ? 'Cr\u00e9ation en cours...' : "Cr\u00e9er l'audit"}
            </button>
          </div>
        </form>
      </main>
    </div>
  );
}
