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
    setEmail(''); setPassword(''); setCompanyName('');
    setContactName(''); setContactPhone(''); setError('');
  };

  const toggleMode = () => { setIsRegister((p) => !p); resetForm(); };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setSubmitting(true);
    try {
      if (isRegister) {
        const data = { email, password, company_name: companyName };
        if (contactName.trim()) data.contact_name = contactName.trim();
        if (contactPhone.trim()) data.contact_phone = contactPhone.trim();
        await register(data);
      } else {
        await login(email, password);
      }
      navigate('/dashboard');
    } catch (err) {
      const detail = err.response?.data?.detail;
      if (typeof detail === 'string') setError(detail);
      else if (Array.isArray(detail)) setError(detail.map((d) => d.msg || JSON.stringify(d)).join('. '));
      else setError(isRegister ? "Erreur lors de l'inscription." : 'Email ou mot de passe incorrect.');
    } finally {
      setSubmitting(false);
    }
  };

  const inputCls = 'w-full rounded-lg border border-gray-200 px-4 py-3 text-sm text-gray-900 placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-[#1a5c3a] focus:border-transparent transition';

  return (
    <div className="min-h-screen bg-[#eaf4ee] flex items-center justify-center px-4">
      <div className="w-full max-w-md">

        {/* Logo */}
        <div className="text-center mb-8">
          <div className="inline-flex items-center gap-2 mb-2">
            <img src="/logo.jpg" alt="GreenAudit" className="h-16 w-auto object-contain" style={{mixBlendMode: 'multiply'}} />
          </div>
          <p className="text-sm text-gray-500">Plateforme d'audit anti-greenwashing</p>
        </div>

        {/* Card */}
        <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-8">
          <h2 className="text-xl font-black text-gray-900 mb-6 text-center">
            {isRegister ? 'Créer un compte partenaire' : 'Connexion'}
          </h2>

          {error && (
            <div className="mb-4 rounded-xl bg-red-50 border border-red-100 px-4 py-3 text-sm text-red-700">
              {error}
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label htmlFor="email" className="block text-sm font-medium text-gray-700 mb-1.5">Email</label>
              <input id="email" type="email" required value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="vous@entreprise.com" className={inputCls} />
            </div>

            <div>
              <label htmlFor="password" className="block text-sm font-medium text-gray-700 mb-1.5">Mot de passe</label>
              <input id="password" type="password" required value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="Votre mot de passe" className={inputCls} />
            </div>

            {isRegister && (
              <>
                <div>
                  <label htmlFor="companyName" className="block text-sm font-medium text-gray-700 mb-1.5">
                    Nom de l'entreprise <span className="text-red-500">*</span>
                  </label>
                  <input id="companyName" type="text" required value={companyName}
                    onChange={(e) => setCompanyName(e.target.value)}
                    placeholder="Votre entreprise" className={inputCls} />
                </div>
                <div>
                  <label htmlFor="contactName" className="block text-sm font-medium text-gray-700 mb-1.5">
                    Nom du contact <span className="text-xs text-gray-400 font-normal">(optionnel)</span>
                  </label>
                  <input id="contactName" type="text" value={contactName}
                    onChange={(e) => setContactName(e.target.value)}
                    placeholder="Prénom Nom" className={inputCls} />
                </div>
                <div>
                  <label htmlFor="contactPhone" className="block text-sm font-medium text-gray-700 mb-1.5">
                    Téléphone <span className="text-xs text-gray-400 font-normal">(optionnel)</span>
                  </label>
                  <input id="contactPhone" type="tel" value={contactPhone}
                    onChange={(e) => setContactPhone(e.target.value)}
                    placeholder="+33 6 12 34 56 78" className={inputCls} />
                </div>
              </>
            )}

            <button
              type="submit"
              disabled={submitting}
              className="w-full rounded-full py-3 text-sm font-semibold text-white bg-[#1a5c3a] hover:bg-[#14472d] transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {submitting
                ? (isRegister ? 'Inscription...' : 'Connexion...')
                : (isRegister ? "S'inscrire" : 'Se connecter')}
            </button>
          </form>

          <div className="mt-6 text-center">
            <p className="text-sm text-gray-500">
              {isRegister ? 'Déjà un compte ?' : 'Pas encore de compte ?'}{' '}
              <button type="button" onClick={toggleMode}
                className="font-semibold text-[#1a5c3a] hover:underline transition">
                {isRegister ? 'Se connecter' : "S'inscrire"}
              </button>
            </p>
          </div>
        </div>

        <p className="text-center text-xs text-gray-400 mt-6">
          GreenAudit — Conformité directive EmpCo (EU 2024/825)
        </p>
      </div>
    </div>
  );
}
