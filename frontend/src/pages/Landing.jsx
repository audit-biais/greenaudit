import { useNavigate } from 'react-router-dom';

const STEPS = [
  {
    number: '01',
    title: 'Saisissez les allégations',
    desc: "Entrez les allégations environnementales de votre client telles qu'elles apparaissent sur son site web, packaging ou publicité. Le formulaire guidé prend 10 à 20 minutes.",
  },
  {
    number: '02',
    title: 'Analyse automatique',
    desc: "Notre moteur vérifie chaque allégation contre les 6 interdictions de l'Annexe I de la directive (UE) 2024/825 : claims génériques, neutralité carbone, labels non certifiés, proportionnalité, engagements futurs, preuves.",
  },
  {
    number: '03',
    title: 'Rapport PDF à votre marque',
    desc: "Téléchargez un rapport professionnel avec votre logo et vos couleurs : verdict par allégation, articles violés, recommandations de correction et plan d'action priorisé.",
  },
];

const RULES = [
  {
    article: 'Annexe I, 4 bis',
    title: 'Allégations génériques',
    desc: '"Écologique", "durable", "respectueux de l\'environnement"... Sans preuve de performance environnementale excellente reconnue, ces termes sont interdits.',
    verdict: 'Interdit',
  },
  {
    article: 'Annexe I, 4 quater',
    title: 'Neutralité carbone par compensation',
    desc: 'Affirmer qu\'un produit a un impact neutre, réduit ou positif sur les émissions de GES sur la base de la compensation carbone est interdit en toutes circonstances.',
    verdict: 'Interdit',
  },
  {
    article: 'Annexe I, 2 bis',
    title: 'Labels non certifiés',
    desc: 'Afficher un label de développement durable qui n\'est pas fondé sur un système de certification par un tiers indépendant ou établi par une autorité publique est interdit.',
    verdict: 'Interdit',
  },
  {
    article: 'Annexe I, 4 ter',
    title: 'Proportionnalité',
    desc: 'Présenter une allégation concernant l\'ensemble du produit ou de l\'entreprise alors qu\'elle ne concerne qu\'un aspect spécifique est interdit.',
    verdict: 'Interdit',
  },
  {
    article: 'Art. 6 §2, Dir. 2005/29/CE',
    title: 'Engagements futurs',
    desc: 'Les allégations de performance future (transition vers le "net zero", etc.) doivent être étayées par des engagements clairs, un calendrier précis et un suivi indépendant vérifiable.',
    verdict: 'Encadré',
  },
  {
    article: 'Art. 6 §1, Dir. 2005/29/CE',
    title: 'Preuve et traçabilité',
    desc: 'Toute allégation environnementale doit être vérifiable. Sans preuve documentée (certification tierce, données mesurables), l\'allégation est considérée trompeuse.',
    verdict: 'Encadré',
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
    title: 'Références réglementaires exactes',
    desc: "Chaque verdict cite l'article précis de la directive (UE) 2024/825 et de la directive 2005/29/CE modifiée. Défendable juridiquement.",
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
            Transposition obligatoire avant le 27 septembre 2026
          </div>
          <h1 className="text-4xl sm:text-5xl lg:text-6xl font-extrabold text-white leading-tight mb-6">
            Directive (UE) 2024/825<br />
            <span className="text-green-200">Vos clients sont-ils conformes ?</span>
          </h1>
          <p className="text-lg sm:text-xl text-green-100 max-w-2xl mx-auto mb-10 leading-relaxed">
            La directive EmpCo interdit les allégations environnementales trompeuses et
            les labels de développement durable non certifiés.{' '}
            <span translate="no">GreenAudit</span> analyse automatiquement chaque allégation
            contre les 6 interdictions de l'Annexe I et génère un rapport PDF conforme, à votre marque.
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
      {/* Stats urgence                                                       */}
      {/* ------------------------------------------------------------------ */}
      <section className="border-b border-gray-100">
        <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-8 text-center">
            <div>
              <p className="text-4xl font-extrabold" style={{ color: '#1B5E20' }}>27 sept. 2026</p>
              <p className="mt-1 text-sm text-gray-500">Transposition dans les droits nationaux des 27 États membres</p>
            </div>
            <div>
              <p className="text-4xl font-extrabold" style={{ color: '#1B5E20' }}>6</p>
              <p className="mt-1 text-sm text-gray-500">Interdictions de l'Annexe I vérifiées par allégation</p>
            </div>
            <div>
              <p className="text-4xl font-extrabold" style={{ color: '#1B5E20' }}>x10</p>
              <p className="mt-1 text-sm text-gray-500">Moins cher qu'un audit manuel (2 000€ vs 20 000€)</p>
            </div>
          </div>
        </div>
      </section>

      {/* ------------------------------------------------------------------ */}
      {/* Ce que la directive interdit                                        */}
      {/* ------------------------------------------------------------------ */}
      <section className="py-20 bg-gray-50">
        <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-14">
            <h2 className="text-3xl font-extrabold text-gray-900">Ce que la directive interdit</h2>
            <p className="mt-3 text-gray-500 max-w-2xl mx-auto">
              La directive (UE) 2024/825 modifie la directive 2005/29/CE sur les pratiques commerciales déloyales.
              Elle ajoute 4 interdictions absolues à l'Annexe I et renforce 2 exigences existantes.
            </p>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {RULES.map((rule) => (
              <div key={rule.article} className="bg-white rounded-2xl p-6 shadow-sm border border-gray-100">
                <div className="flex items-center justify-between mb-3">
                  <span className="text-xs font-mono text-gray-400">{rule.article}</span>
                  <span className={`text-xs font-bold px-2.5 py-1 rounded-full ${
                    rule.verdict === 'Interdit'
                      ? 'bg-red-50 text-red-700'
                      : 'bg-amber-50 text-amber-700'
                  }`}>
                    {rule.verdict}
                  </span>
                </div>
                <h3 className="text-base font-bold text-gray-900 mb-2">{rule.title}</h3>
                <p className="text-sm text-gray-500 leading-relaxed">{rule.desc}</p>
              </div>
            ))}
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
      {/* Contact / Devis                                                     */}
      {/* ------------------------------------------------------------------ */}
      <section className="py-20">
        <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="rounded-2xl p-10 text-center" style={{ background: 'linear-gradient(135deg, #1B5E20 0%, #2E7D32 100%)' }}>
            <h2 className="text-3xl font-extrabold text-white mb-4">Un tarif adapté à votre volume</h2>
            <p className="text-green-100 text-lg mb-10 max-w-xl mx-auto">
              Chaque partenaire a des besoins différents. Contactez-nous pour un devis personnalisé
              selon votre nombre de clients et votre secteur d'activité.
            </p>
            <a
              href="mailto:contact@greenaudit.app"
              className="inline-flex items-center gap-2 px-8 py-4 rounded-xl text-base font-bold text-[#1B5E20] bg-white shadow-lg hover:bg-gray-50 transition-colors"
            >
              <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
              </svg>
              Demander un devis
            </a>
            <p className="text-green-200 text-sm mt-6">
              Réponse sous 24h &mdash; contact@greenaudit.app
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
            La directive entre en vigueur dans quelques mois.
          </h2>
          <p className="text-gray-500 mb-8">
            Vos clients ne sont probablement pas conformes. Proposez-leur l'audit avant qu'il ne soit trop tard.
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
            Conformité Directive (UE) 2024/825 modifiant les directives 2005/29/CE et 2011/83/UE &mdash; Transposition avant le 27 septembre 2026
          </p>
        </div>
      </footer>
    </div>
  );
}
