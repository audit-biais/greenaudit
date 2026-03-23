import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import emailjs from '@emailjs/browser';

const EMAILJS_SERVICE_ID = 'service_a20f76h';
const EMAILJS_TEMPLATE_ID = 'template_rk1zxyq';
const EMAILJS_PUBLIC_KEY = 'SpdUZkbJUFL3sdP0b';

const inputCls = 'w-full rounded-lg border border-gray-200 px-4 py-3 text-sm text-gray-900 placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-[#1a5c3a] focus:border-transparent transition bg-white';

export default function Contact() {
  const navigate = useNavigate();
  const [form, setForm] = useState({ name: '', email: '', company: '', message: '' });
  const [loading, setLoading] = useState(false);
  const [sent, setSent] = useState(false);
  const [error, setError] = useState('');

  const handleChange = (e) => setForm({ ...form, [e.target.name]: e.target.value });

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    try {
      await emailjs.send(EMAILJS_SERVICE_ID, EMAILJS_TEMPLATE_ID, {
        title: 'GreenAudit - Demande de devis',
        from_name: form.name,
        from_email: form.email,
        entreprise: form.company,
        message: form.message,
      }, EMAILJS_PUBLIC_KEY);
      setSent(true);
    } catch {
      setError("Une erreur est survenue. Réessayez ou envoyez un email à optimaflow.pro@gmail.com");
    } finally {
      setLoading(false);
    }
  };

  if (sent) {
    return (
      <div className="min-h-screen bg-[#eaf4ee] flex items-center justify-center px-4">
        <div className="bg-white rounded-2xl border border-gray-100 p-10 max-w-md w-full text-center">
          <div className="h-16 w-16 rounded-full flex items-center justify-center mx-auto mb-6 bg-[#eaf4ee]">
            <svg className="h-8 w-8 text-[#1a5c3a]" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
            </svg>
          </div>
          <h2 className="text-2xl font-black text-gray-900 mb-2">Message envoyé</h2>
          <p className="text-gray-400 mb-8">Nous revenons vers vous sous 24h.</p>
          <button onClick={() => navigate('/landing')}
            className="text-sm font-semibold text-white px-6 py-3 rounded-full bg-[#1a5c3a] hover:bg-[#14472d] transition-colors">
            Retour à l'accueil →
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-white">
      {/* Nav */}
      <nav className="sticky top-0 z-50 bg-white border-b border-gray-100">
        <div className="max-w-7xl mx-auto px-6 h-16 flex items-center justify-between">
          <button onClick={() => navigate('/landing')} className="flex items-center gap-2">
            <div className="h-8 w-8 rounded-lg flex items-center justify-center bg-[#1a5c3a]">
              <svg className="h-4 w-4 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                  d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
              </svg>
            </div>
            <span className="text-base font-bold text-[#1a5c3a]" translate="no">GreenAudit</span>
          </button>
          <button onClick={() => navigate('/login')}
            className="text-sm font-semibold text-white px-5 py-2 rounded-full bg-[#1a5c3a] hover:bg-[#14472d] transition-colors">
            Connexion →
          </button>
        </div>
      </nav>

      {/* Formulaire */}
      <div className="max-w-lg mx-auto px-6 py-16">
        <p className="text-xs font-semibold uppercase tracking-widest text-[#1a5c3a] mb-3">Contact</p>
        <h1 className="text-3xl font-black text-gray-900 mb-2">Demander un devis</h1>
        <p className="text-gray-400 text-sm mb-10">
          Décrivez votre besoin et nous vous recontactons sous 24h avec une offre adaptée.
        </p>

        <form onSubmit={handleSubmit} className="space-y-5">
          <div>
            <label htmlFor="name" className="block text-sm font-medium text-gray-700 mb-1.5">Nom complet</label>
            <input id="name" name="name" type="text" required value={form.name}
              onChange={handleChange} className={inputCls} placeholder="Jean Dupont" />
          </div>
          <div>
            <label htmlFor="email" className="block text-sm font-medium text-gray-700 mb-1.5">Email professionnel</label>
            <input id="email" name="email" type="email" required value={form.email}
              onChange={handleChange} className={inputCls} placeholder="jean.dupont@entreprise.com" />
          </div>
          <div>
            <label htmlFor="company" className="block text-sm font-medium text-gray-700 mb-1.5">Entreprise</label>
            <input id="company" name="company" type="text" required value={form.company}
              onChange={handleChange} className={inputCls} placeholder="Cabinet RSE / Agence" />
          </div>
          <div>
            <label htmlFor="message" className="block text-sm font-medium text-gray-700 mb-1.5">Message</label>
            <textarea id="message" name="message" required rows={5} value={form.message}
              onChange={handleChange} className={inputCls + ' resize-none'}
              placeholder="Décrivez votre besoin : nombre de clients à auditer, secteur, délai souhaité..." />
          </div>

          {error && <p className="text-sm text-red-600 bg-red-50 rounded-xl px-4 py-3">{error}</p>}

          <button type="submit" disabled={loading}
            className="w-full py-3.5 rounded-full text-white font-semibold text-sm bg-[#1a5c3a] hover:bg-[#14472d] transition-colors disabled:opacity-50">
            {loading ? 'Envoi en cours...' : 'Envoyer ma demande →'}
          </button>
        </form>
      </div>
    </div>
  );
}
