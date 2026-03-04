import { useNavigate } from 'react-router-dom';

const STEPS = [
  {
    number: '01',
    title: 'Saisissez les allégations',
    desc: "Entrez les claims environnementales de votre client (site web, packaging, publicité). Le formulaire guidé prend 10 à 20 minutes.",
  },
  {
    number: '02',
    title: 'Analyse automatique',
    desc: "Notre moteur applique les 6 critères de la directive EmpCo sur chaque allégation : claims génériques, neutralité carbone, labels, preuves...",
  },
  {
    number: '03',
    title: 'Rapport PDF à votre marque',
    desc: "Téléchargez un rapport professionnel avec votre logo et vos couleurs. Partagez le lien client en lecture seule directement depuis la plateforme.",
  },
];

const WHY = [
  {
    icon: (
      <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 7h.01M7 3h5a1.99 1.99 0 011.414.586l7 7a2 2 0 010 2.828l-7 7a2 2 0 01-2.828 0l-7-7A1.99 1.99 0 013 12V7a4 4 0 014-4z" />
      </svg>
    ),
    title: '100% white-label',
    desc: 'Votre logo, vos couleurs, vos coordonnées sur chaque rapport. Le client final ne voit que votre cabinet.',
  },
  {
    icon: (
      <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
      </svg>
    ),
    title: 'Résultat en minutes',
    desc: <>Un audit manuel prend 2 à 4 semaines. <span translate="no">GreenAudit</span> produit le même niveau d'analyse en moins d'une heure.</>,
  },
  {
    icon: (
      <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
      </svg>
    ),
    title: 'Conformité EmpCo garantie',
    desc: "Chaque verdict s'appuie sur les articles exacts de la directive EU 2024/825 et les guidelines ADEME 2025.",
  },
  {
    icon: (
      <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8.684 13.342C8.886 12.938 9 12.482 9 12c0-.482-.114-.938-.316-1.342m0 2.684a3 3 0 110-2.684m0 2.684l6.632 3.316m-6.632-6l6.632-3.316m0 0a3 3 0 105.367-2.684 3 3 0 00-5.367 2.684zm0 9.316a3 3 0 105.368 2.684 3 3 0 00-5.368-2.684z" />
      </svg>
    ),
    title: 'Lien de partage client',
    desc: "Partagez un lien sécurisé en lecture seule. Votre client consulte son rapport depuis son navigateur, sans créer de compte.",
  },
];

export default function Landing() {
  const navigate = useNavigate();

  return (
    <div className="min-h-screen bg-white">
      {/* ------------------------------------------------------------------ */}
      {/* Nav                                                                 */}
      {/* ------------------------------------------------------------------ */}
      <nav className="sticky top-0 z-50 bg-white border-b border-gray-100 shadow-sm">
        <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className="h-8 w-8 rounded-lg flex items-center justify-center" style={{ backgroundColor: '#1B5E20' }}>
              <svg className="h-5 w-5 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
              </svg>
            </div>
            <span className="text-lg font-bold" style={{ color: '#1B5E20' }} translate="no">GreenAudit</span>
          </div>
          <div className="flex items-center gap-3">
            <button
              onClick={() => navigate('/login')}
              className="text-sm font-medium text-gray-600 hover:text-gray-900 transition-colors"
            >
              Se connecter
            </button>
            <button
              onClick={() => navigate('/login')}
              className="text-sm font-semibold text-white px-4 py-2 rounded-lg transition-colors"
              style={{ backgroundColor: '#1B5E20' }}
              onMouseEnter={(e) => (e.currentTarget.style.backgroundColor = '#2E7D32')}
              onMouseLeave={(e) => (e.currentTarget.style.backgroundColor = '#1B5E20')}
            >
              Créer un compte
            </button>
          </div>
        </div>
      </nav>

      {/* ------------------------------------------------------------------ */}
      {/* Hero                                                                */}
      {/* ------------------------------------------------------------------ */}
      <section className="relative overflow-hidden" style={{ background: 'linear-gradient(135deg, #1B5E20 0%, #2E7D32 60%, #388E3C 100%)' }}>
        <div className="absolute inset-0 opacity-10">
          <svg width="100%" height="100%" viewBox="0 0 800 400" preserveAspectRatio="xMidYMid slice">
            <circle cx="700" cy="50" r="200" fill="white" />
            <circle cx="100" cy="350" r="150" fill="white" />
          </svg>
        </div>
        <div className="relative max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-20 text-center">
          <div className="inline-flex items-center gap-2 bg-white/20 text-white text-xs font-semibold px-4 py-1.5 rounded-full mb-6 backdrop-blur-sm">
            <svg className="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            Deadline réglementaire : 27 septembre 2026
          </div>
          <h1 className="text-4xl sm:text-5xl lg:text-6xl font-extrabold text-white leading-tight mb-6">
            Auditez la conformité<br />
            anti-greenwashing<br />
            <span className="text-green-200">de vos clients.</span>
          </h1>
          <p className="text-lg sm:text-xl text-green-100 max-w-2xl mx-auto mb-10 leading-relaxed">
            La directive EmpCo (EU 2024/825) entre en vigueur le 27 septembre 2026.{' '}
            <span translate="no">GreenAudit</span> analyse automatiquement les allégations environnementales et génère
            un rapport PDF professionnel, à votre marque, en quelques minutes.
          </p>
          <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
            <button
              onClick={() => navigate('/login')}
              className="w-full sm:w-auto px-8 py-4 rounded-xl text-base font-bold text-[#1B5E20] bg-white shadow-lg hover:bg-gray-50 transition-colors"
            >
              Créer un compte partenaire
            </button>
            <button
              onClick={() => navigate('/login')}
              className="w-full sm:w-auto px-8 py-4 rounded-xl text-base font-semibold text-white border-2 border-white/50 hover:border-white hover:bg-white/10 transition-colors"
            >
              Se connecter
            </button>
          </div>
        </div>
      </section>

      {/* ------------------------------------------------------------------ */}
      {/* Stats urgence                                                        */}
      {/* ------------------------------------------------------------------ */}
      <section className="border-b border-gray-100">
        <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-8 text-center">
            <div>
              <p className="text-4xl font-extrabold" style={{ color: '#1B5E20' }}>27 sept.</p>
              <p className="mt-1 text-sm text-gray-500">Deadline réglementaire 2026</p>
            </div>
            <div>
              <p className="text-4xl font-extrabold" style={{ color: '#1B5E20' }}>6</p>
              <p className="mt-1 text-sm text-gray-500">Critères EmpCo analysés par allégation</p>
            </div>
            <div>
              <p className="text-4xl font-extrabold" style={{ color: '#1B5E20' }}>x10</p>
              <p className="mt-1 text-sm text-gray-500">Moins cher qu'un audit manuel (2 000€ vs 20 000€)</p>
            </div>
          </div>
        </div>
      </section>

      {/* ------------------------------------------------------------------ */}
      {/* Comment ça marche                                                   */}
      {/* ------------------------------------------------------------------ */}
      <section className="py-20">
        <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-14">
            <h2 className="text-3xl font-extrabold text-gray-900">Comment ça marche</h2>
            <p className="mt-3 text-gray-500">Un audit complet en 3 étapes, sans expertise juridique requise.</p>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-10">
            {STEPS.map((step) => (
              <div key={step.number} className="relative">
                <div className="flex items-center gap-4 mb-4">
                  <span className="text-5xl font-extrabold" style={{ color: '#E8F5E9' }}>{step.number}</span>
                  <div className="h-px flex-1 bg-gray-100" />
                </div>
                <h3 className="text-lg font-bold text-gray-900 mb-2">{step.title}</h3>
                <p className="text-sm text-gray-500 leading-relaxed">{step.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ------------------------------------------------------------------ */}
      {/* Pourquoi GreenAudit                                                 */}
      {/* ------------------------------------------------------------------ */}
      <section className="py-20 bg-gray-50">
        <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-14">
            <h2 className="text-3xl font-extrabold text-gray-900">Conçu pour les partenaires</h2>
            <p className="mt-3 text-gray-500">Agences de communication, cabinets RSE, avocats spécialisés.</p>
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-8">
            {WHY.map((item) => (
              <div key={item.title} className="bg-white rounded-2xl p-6 shadow-sm border border-gray-100 flex gap-5">
                <div className="flex-shrink-0 h-12 w-12 rounded-xl flex items-center justify-center text-white" style={{ backgroundColor: '#1B5E20' }}>
                  {item.icon}
                </div>
                <div>
                  <h3 className="text-base font-bold text-gray-900 mb-1">{item.title}</h3>
                  <p className="text-sm text-gray-500 leading-relaxed">{item.desc}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ------------------------------------------------------------------ */}
      {/* ROI                                                                 */}
      {/* ------------------------------------------------------------------ */}
      <section className="py-20">
        <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="rounded-2xl p-10 text-center" style={{ background: 'linear-gradient(135deg, #1B5E20 0%, #2E7D32 100%)' }}>
            <h2 className="text-3xl font-extrabold text-white mb-4">Un modèle économique simple</h2>
            <p className="text-green-100 text-lg mb-10 max-w-xl mx-auto">
              Achetez l'accès à <span translate="no">GreenAudit</span>. Revendez l'audit à votre marque.
            </p>
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-6 max-w-2xl mx-auto">
              <div className="bg-white/15 rounded-xl p-5 backdrop-blur-sm">
                <p className="text-3xl font-extrabold text-white">250-500€</p>
                <p className="text-green-200 text-sm mt-1">Votre coût d'accès</p>
              </div>
              <div className="flex items-center justify-center">
                <svg className="h-8 w-8 text-green-300" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7l5 5m0 0l-5 5m5-5H6" />
                </svg>
              </div>
              <div className="bg-white/15 rounded-xl p-5 backdrop-blur-sm">
                <p className="text-3xl font-extrabold text-white">2 000-5 000€</p>
                <p className="text-green-200 text-sm mt-1">Votre prix de revente</p>
              </div>
            </div>
            <p className="text-green-200 text-xs mt-8">
              Un audit manuel facturé par un cabinet juridique coûte entre 10 000 et 20 000€.
            </p>
          </div>
        </div>
      </section>

      {/* ------------------------------------------------------------------ */}
      {/* CTA final                                                           */}
      {/* ------------------------------------------------------------------ */}
      <section className="py-20 bg-gray-50 border-t border-gray-100">
        <div className="max-w-2xl mx-auto px-4 text-center">
          <h2 className="text-3xl font-extrabold text-gray-900 mb-4">
            Prêt à proposer l'audit à vos clients ?
          </h2>
          <p className="text-gray-500 mb-8">
            Créez votre compte partenaire gratuitement et lancez votre premier audit aujourd'hui.
          </p>
          <button
            onClick={() => navigate('/login')}
            className="inline-flex items-center gap-2 px-8 py-4 rounded-xl text-base font-bold text-white shadow-md transition-colors"
            style={{ backgroundColor: '#1B5E20' }}
            onMouseEnter={(e) => (e.currentTarget.style.backgroundColor = '#2E7D32')}
            onMouseLeave={(e) => (e.currentTarget.style.backgroundColor = '#1B5E20')}
          >
            <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M18 9v3m0 0v3m0-3h3m-3 0h-3m-2-5a4 4 0 11-8 0 4 4 0 018 0zM3 20a6 6 0 0112 0v1H3v-1z" />
            </svg>
            Créer un compte partenaire
          </button>
          <p className="mt-4 text-xs text-gray-400">
            Déjà partenaire ?{' '}
            <button onClick={() => navigate('/login')} className="underline hover:text-gray-600 transition-colors">
              Se connecter
            </button>
          </p>
        </div>
      </section>

      {/* ------------------------------------------------------------------ */}
      {/* Footer                                                              */}
      {/* ------------------------------------------------------------------ */}
      <footer className="border-t border-gray-100 py-8">
        <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 flex flex-col sm:flex-row items-center justify-between gap-4">
          <div className="flex items-center gap-2">
            <div className="h-6 w-6 rounded flex items-center justify-center" style={{ backgroundColor: '#1B5E20' }}>
              <svg className="h-3.5 w-3.5 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
              </svg>
            </div>
            <span className="text-sm font-semibold" style={{ color: '#1B5E20' }} translate="no">GreenAudit</span>
          </div>
          <p className="text-xs text-gray-400 text-center">
            Conformité Directive EmpCo (EU 2024/825) &mdash; Deadline 27 septembre 2026
          </p>
        </div>
      </footer>
    </div>
  );
}
