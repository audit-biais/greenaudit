import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../api/auth';

export default function Login() {
  const [isRegister, setIsRegister] = useState(false);
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [companyName, setCompanyName] = useState('');
  const [contactName, setContactName] = useState('');
  const [contactPhone, setContactPhone] = useState('');
  const [error, setError] = useState('');
  const [submitting, setSubmitting] = useState(false);

  const { login, register } = useAuth();
  const navigate = useNavigate();

  const resetForm = () => {
    setEmail('');
    setPassword('');
    setCompanyName('');
    setContactName('');
    setContactPhone('');
    setError('');
  };

  const toggleMode = () => {
    setIsRegister((prev) => !prev);
    resetForm();
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setSubmitting(true);

    try {
      if (isRegister) {
        const data = {
          email,
          password,
          company_name: companyName,
        };
        if (contactName.trim()) data.contact_name = contactName.trim();
        if (contactPhone.trim()) data.contact_phone = contactPhone.trim();
        await register(data);
      } else {
        await login(email, password);
      }
      navigate('/');
    } catch (err) {
      const detail = err.response?.data?.detail;
      if (typeof detail === 'string') {
        setError(detail);
      } else if (Array.isArray(detail)) {
        setError(detail.map((d) => d.msg || d.message || JSON.stringify(d)).join('. '));
      } else {
        setError(isRegister ? "Erreur lors de l'inscription." : 'Email ou mot de passe incorrect.');
      }
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-100 px-4">
      <div className="w-full max-w-md">
        {/* Logo / Brand header */}
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-16 h-16 rounded-full mb-4" style={{ backgroundColor: '#1B5E20' }}>
            <svg className="w-8 h-8 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
            </svg>
          </div>
          <h1 className="text-3xl font-bold" style={{ color: '#1B5E20' }}>
            GreenAudit
          </h1>
          <p className="text-gray-500 mt-1 text-sm">
            Plateforme d'audit anti-greenwashing
          </p>
        </div>

        {/* Card */}
        <div className="bg-white rounded-xl shadow-lg p-8">
          <h2 className="text-xl font-semibold text-gray-800 mb-6 text-center">
            {isRegister ? 'Créer un compte partenaire' : 'Connexion'}
          </h2>

          {error && (
            <div className="mb-4 rounded-lg bg-red-50 border border-red-200 px-4 py-3 text-sm text-red-700">
              {error}
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-4">
            {/* Email */}
            <div>
              <label htmlFor="email" className="block text-sm font-medium text-gray-700 mb-1">
                Email
              </label>
              <input
                id="email"
                type="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="vous@entreprise.com"
                className="w-full rounded-lg border border-gray-300 px-4 py-2.5 text-sm text-gray-900 placeholder-gray-400 focus:outline-none focus:ring-2 focus:border-transparent transition"
                style={{ focusRingColor: '#2E7D32' }}
                onFocus={(e) => { e.target.style.boxShadow = '0 0 0 2px #2E7D32'; e.target.style.borderColor = 'transparent'; }}
                onBlur={(e) => { e.target.style.boxShadow = 'none'; e.target.style.borderColor = '#d1d5db'; }}
              />
            </div>

            {/* Password */}
            <div>
              <label htmlFor="password" className="block text-sm font-medium text-gray-700 mb-1">
                Mot de passe
              </label>
              <input
                id="password"
                type="password"
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="Votre mot de passe"
                className="w-full rounded-lg border border-gray-300 px-4 py-2.5 text-sm text-gray-900 placeholder-gray-400 focus:outline-none focus:ring-2 focus:border-transparent transition"
                onFocus={(e) => { e.target.style.boxShadow = '0 0 0 2px #2E7D32'; e.target.style.borderColor = 'transparent'; }}
                onBlur={(e) => { e.target.style.boxShadow = 'none'; e.target.style.borderColor = '#d1d5db'; }}
              />
            </div>

            {/* Register-only fields */}
            {isRegister && (
              <>
                {/* Company name */}
                <div>
                  <label htmlFor="companyName" className="block text-sm font-medium text-gray-700 mb-1">
                    Nom de l'entreprise <span className="text-red-500">*</span>
                  </label>
                  <input
                    id="companyName"
                    type="text"
                    required
                    value={companyName}
                    onChange={(e) => setCompanyName(e.target.value)}
                    placeholder="Votre entreprise"
                    className="w-full rounded-lg border border-gray-300 px-4 py-2.5 text-sm text-gray-900 placeholder-gray-400 focus:outline-none focus:ring-2 focus:border-transparent transition"
                    onFocus={(e) => { e.target.style.boxShadow = '0 0 0 2px #2E7D32'; e.target.style.borderColor = 'transparent'; }}
                    onBlur={(e) => { e.target.style.boxShadow = 'none'; e.target.style.borderColor = '#d1d5db'; }}
                  />
                </div>

                {/* Contact name */}
                <div>
                  <label htmlFor="contactName" className="block text-sm font-medium text-gray-700 mb-1">
                    Nom du contact <span className="text-gray-400 text-xs font-normal">(optionnel)</span>
                  </label>
                  <input
                    id="contactName"
                    type="text"
                    value={contactName}
                    onChange={(e) => setContactName(e.target.value)}
                    placeholder="Prénom Nom"
                    className="w-full rounded-lg border border-gray-300 px-4 py-2.5 text-sm text-gray-900 placeholder-gray-400 focus:outline-none focus:ring-2 focus:border-transparent transition"
                    onFocus={(e) => { e.target.style.boxShadow = '0 0 0 2px #2E7D32'; e.target.style.borderColor = 'transparent'; }}
                    onBlur={(e) => { e.target.style.boxShadow = 'none'; e.target.style.borderColor = '#d1d5db'; }}
                  />
                </div>

                {/* Contact phone */}
                <div>
                  <label htmlFor="contactPhone" className="block text-sm font-medium text-gray-700 mb-1">
                    Téléphone <span className="text-gray-400 text-xs font-normal">(optionnel)</span>
                  </label>
                  <input
                    id="contactPhone"
                    type="tel"
                    value={contactPhone}
                    onChange={(e) => setContactPhone(e.target.value)}
                    placeholder="+33 6 12 34 56 78"
                    className="w-full rounded-lg border border-gray-300 px-4 py-2.5 text-sm text-gray-900 placeholder-gray-400 focus:outline-none focus:ring-2 focus:border-transparent transition"
                    onFocus={(e) => { e.target.style.boxShadow = '0 0 0 2px #2E7D32'; e.target.style.borderColor = 'transparent'; }}
                    onBlur={(e) => { e.target.style.boxShadow = 'none'; e.target.style.borderColor = '#d1d5db'; }}
                  />
                </div>
              </>
            )}

            {/* Submit button */}
            <button
              type="submit"
              disabled={submitting}
              className="w-full rounded-lg px-4 py-2.5 text-sm font-semibold text-white shadow-sm transition duration-150 ease-in-out disabled:opacity-50 disabled:cursor-not-allowed hover:opacity-90"
              style={{ backgroundColor: '#1B5E20' }}
            >
              {submitting
                ? (isRegister ? 'Inscription en cours...' : 'Connexion en cours...')
                : (isRegister ? "S'inscrire" : 'Se connecter')}
            </button>
          </form>

          {/* Toggle login / register */}
          <div className="mt-6 text-center">
            <p className="text-sm text-gray-500">
              {isRegister ? 'Déjà un compte ?' : 'Pas encore de compte ?'}{' '}
              <button
                type="button"
                onClick={toggleMode}
                className="font-semibold hover:underline transition"
                style={{ color: '#2E7D32' }}
              >
                {isRegister ? 'Se connecter' : "S'inscrire"}
              </button>
            </p>
          </div>
        </div>

        {/* Footer */}
        <p className="text-center text-xs text-gray-400 mt-6">
          GreenAudit &mdash; Conformité directive EmpCo (EU 2024/825)
        </p>
      </div>
    </div>
  );
}
