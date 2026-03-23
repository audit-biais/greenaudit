import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../api/auth';

/* ─── Données ──────────────────────────────────────────────────────────────── */

const STEPS = [
  {
    step: '01',
    title: 'Saisissez les allégations',
    desc: "Entrez les allégations environnementales de votre client telles qu'elles apparaissent sur son site web, packaging ou publicité. Le formulaire guidé prend 10 à 20 minutes.",
  },
  {
    step: '02',
    title: 'Analyse automatique',
    desc: "Notre moteur vérifie chaque allégation contre les 6 interdictions de l'Annexe I de la directive (UE) 2024/825 : claims génériques, neutralité carbone, labels non certifiés, proportionnalité, engagements futurs, preuves.",
  },
  {
    step: '03',
    title: 'Rapport PDF à votre marque',
    desc: "Téléchargez un rapport professionnel avec votre logo et vos couleurs : verdict par allégation, articles violés, recommandations de correction et plan d'action priorisé.",
  },
];

const RULES = [
  {
    article: 'Annexe I, 4 bis',
    title: 'Allégations génériques',
    desc: '"Écologique", "durable", "respectueux de l\'environnement"… Sans preuve de performance environnementale excellente reconnue, ces termes sont interdits.',
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
    desc: 'Les allégations de performance future doivent être étayées par des engagements clairs, un calendrier précis et un suivi indépendant vérifiable.',
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
    title: '100% white-label',
    desc: 'Votre logo, vos couleurs, vos coordonnées sur chaque rapport. Le client final ne voit que votre cabinet.',
  },
  {
    title: 'Résultat en minutes',
    desc: 'Un audit manuel prend 2 à 4 semaines. GreenAudit produit le même niveau d\'analyse en moins d\'une heure.',
  },
  {
    title: 'Références réglementaires exactes',
    desc: 'Chaque verdict cite l\'article précis de la directive (UE) 2024/825 et de la directive 2005/29/CE modifiée. Défendable juridiquement.',
  },
  {
    title: 'Lien de partage client',
    desc: 'Partagez un lien sécurisé en lecture seule. Votre client consulte son rapport depuis son navigateur, sans créer de compte.',
  },
];

const FAQ = [
  {
    q: 'Qui peut utiliser GreenAudit ?',
    a: 'GreenAudit est destiné aux partenaires professionnels : agences de communication, cabinets RSE, avocats spécialisés. Vous achetez l\'outil en marque blanche et le revendez à vos clients.',
  },
  {
    q: 'Comment fonctionne le modèle white-label ?',
    a: 'Vous configurez votre logo, vos couleurs et vos coordonnées dans les paramètres. Chaque rapport PDF généré portera votre identité visuelle. Vos clients ne voient jamais la marque GreenAudit.',
  },
  {
    q: 'Les rapports sont-ils juridiquement opposables ?',
    a: 'Nos rapports sont des outils d\'aide à la conformité. Ils citent les articles exacts de la directive (UE) 2024/825 et constituent une base solide pour un conseil juridique. Ils ne remplacent pas l\'avis d\'un avocat.',
  },
  {
    q: 'Que couvre exactement la directive EmpCo ?',
    a: 'La directive (UE) 2024/825 modifie la directive 2005/29/CE. Elle interdit 4 pratiques via l\'Annexe I et renforce 2 exigences existantes. Elle s\'applique à toutes les allégations environnementales destinées aux consommateurs dans l\'UE.',
  },
];

/* ─── Composant accordion FAQ ───────────────────────────────────────────────── */
function FaqItem({ q, a }) {
  const [open, setOpen] = useState(false);
  return (
    <div className="border-t border-gray-200 py-5">
      <button
        onClick={() => setOpen(!open)}
        className="w-full flex items-center justify-between text-left gap-6"
      >
        <span className="text-base font-semibold text-gray-900">{q}</span>
        <span className="flex-shrink-0 text-xl text-gray-400 font-light">{open ? '−' : '+'}</span>
      </button>
      {open && (
        <p className="mt-3 text-sm text-gray-500 leading-relaxed pr-8">{a}</p>
      )}
    </div>
  );
}

/* ─── Mockup UI (remplace la photo de l'équipe / screenshot) ──────────────── */
function AppMockup() {
  return (
    <div className="bg-white rounded-2xl border border-gray-200 shadow-sm overflow-hidden text-xs font-mono">
      {/* Barre titre */}
      <div className="flex items-center gap-1.5 px-3 py-2 border-b border-gray-100">
        <span className="h-2.5 w-2.5 rounded-full bg-red-400" />
        <span className="h-2.5 w-2.5 rounded-full bg-yellow-400" />
        <span className="h-2.5 w-2.5 rounded-full bg-green-400" />
        <span className="ml-2 text-gray-400 text-[10px]">GreenAudit — Audit #042</span>
      </div>
      {/* Contenu mockup */}
      <div className="p-4 space-y-3">
        <div className="flex items-center justify-between">
          <span className="text-gray-500 text-[10px] uppercase tracking-wide">Allégation</span>
          <span className="text-gray-500 text-[10px] uppercase tracking-wide">Verdict</span>
        </div>
        {[
          { claim: '"Produit écologique"', verdict: 'NON CONFORME', color: 'text-red-600 bg-red-50' },
          { claim: '"Carbon neutral 2030"', verdict: 'NON CONFORME', color: 'text-red-600 bg-red-50' },
          { claim: '"30% plastique recyclé"', verdict: 'RISQUE', color: 'text-amber-600 bg-amber-50' },
          { claim: '"Label Ecocert certifié"', verdict: 'CONFORME', color: 'text-green-700 bg-green-50' },
        ].map((item) => (
          <div key={item.claim} className="flex items-center justify-between py-1.5 border-b border-gray-50">
            <span className="text-gray-700 text-[11px]">{item.claim}</span>
            <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full ${item.color}`}>
              {item.verdict}
            </span>
          </div>
        ))}
        <div className="pt-2 flex items-center justify-between">
          <span className="text-gray-400 text-[10px]">Score global</span>
          <span className="text-[#1a5c3a] font-bold text-sm">38 / 100</span>
        </div>
        <div className="h-2 rounded-full bg-gray-100 overflow-hidden">
          <div className="h-full rounded-full bg-[#1a5c3a]" style={{ width: '38%' }} />
        </div>
      </div>
    </div>
  );
}

/* ─── Landing principal ─────────────────────────────────────────────────────── */
export default function Landing() {
  const navigate = useNavigate();
  const { partner } = useAuth();

  return (
    <div className="min-h-screen bg-white font-sans">

      {/* ═══════════════════════════════════════════════════════ NAVBAR ══ */}
      <nav className="sticky top-0 z-50 bg-white border-b border-gray-100">
        <div className="max-w-7xl mx-auto px-6 h-16 flex items-center justify-between">

          {/* Logo */}
          <div className="flex items-center gap-2 flex-shrink-0">
            <div className="h-8 w-8 rounded-lg flex items-center justify-center bg-[#1a5c3a]">
              <svg className="h-4 w-4 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                  d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
              </svg>
            </div>
            <span className="text-base font-bold text-[#1a5c3a]" translate="no">GreenAudit</span>
          </div>

          {/* Nav links centre */}
          <div className="hidden md:flex items-center gap-8 text-sm text-gray-600">
            <a href="#fonctionnalites" className="hover:text-gray-900 transition-colors">Fonctionnalités</a>
            <a href="#regles" className="hover:text-gray-900 transition-colors">Règles EmpCo</a>
            <a href="#partenaires" className="hover:text-gray-900 transition-colors">Partenaires</a>
            <button onClick={() => navigate('/contact')} className="hover:text-gray-900 transition-colors">Tarifs</button>
          </div>

          {/* CTA droite */}
          <div className="flex items-center gap-4">
            {partner ? (
              <button
                onClick={() => navigate('/dashboard')}
                className="text-sm font-semibold text-white px-5 py-2 rounded-full bg-[#1a5c3a] hover:bg-[#14472d] transition-colors"
              >
                Tableau de bord →
              </button>
            ) : (
              <>
                <button
                  onClick={() => navigate('/login')}
                  className="hidden sm:block text-sm text-gray-600 hover:text-gray-900 transition-colors"
                >
                  Connexion
                </button>
                <button
                  onClick={() => navigate('/login')}
                  className="text-sm font-semibold text-white px-5 py-2 rounded-full bg-[#1a5c3a] hover:bg-[#14472d] transition-colors"
                >
                  Démo →
                </button>
              </>
            )}
          </div>
        </div>
      </nav>

      {/* ═══════════════════════════════════════════════════════ HERO ══ */}
      <section className="bg-[#eaf4ee]">
        <div className="max-w-7xl mx-auto px-6 py-20 grid grid-cols-1 lg:grid-cols-2 gap-12 items-center">

          {/* Visuel gauche */}
          <div className="order-2 lg:order-1">
            <div className="bg-[#d4ecdb] rounded-3xl p-8">
              <AppMockup />
            </div>
          </div>

          {/* Texte droite */}
          <div className="order-1 lg:order-2">
            <p className="text-xs font-semibold uppercase tracking-widest text-[#1a5c3a] mb-4">
              Directive EmpCo
            </p>
            <h1 className="text-4xl sm:text-5xl font-black text-gray-900 leading-tight mb-6">
              Auditez et sécurisez les allégations environnementales de vos clients
            </h1>
            <p className="text-base text-gray-500 leading-relaxed mb-8 max-w-lg">
              La directive (UE) 2024/825 entre en vigueur le 27 septembre 2026.
              GreenAudit analyse automatiquement chaque allégation contre les 6 interdictions
              de l'Annexe I et génère un rapport PDF conforme, à votre marque.
            </p>
            <div className="flex flex-wrap gap-3">
              <button
                onClick={() => navigate('/login')}
                className="px-6 py-3 rounded-full text-sm font-semibold text-white bg-[#1a5c3a] hover:bg-[#14472d] transition-colors"
              >
                Créer un compte partenaire →
              </button>
              <button
                onClick={() => navigate('/contact')}
                className="px-6 py-3 rounded-full text-sm font-semibold text-[#1a5c3a] border-2 border-[#1a5c3a] hover:bg-[#eaf4ee] transition-colors"
              >
                Contactez-nous →
              </button>
            </div>
          </div>
        </div>
      </section>

      {/* ═══════════════════════════════════════════════════ STATS BAR ══ */}
      <section className="border-b border-gray-100">
        <div className="max-w-7xl mx-auto px-6 py-14 grid grid-cols-1 sm:grid-cols-3 gap-8 text-center">
          <div>
            <p className="text-4xl font-black text-[#1a5c3a]">27 sept. 2026</p>
            <p className="mt-2 text-sm text-gray-500">Transposition obligatoire dans les 27 États membres</p>
          </div>
          <div>
            <p className="text-4xl font-black text-[#1a5c3a]">6</p>
            <p className="mt-2 text-sm text-gray-500">Interdictions de l'Annexe I vérifiées par allégation</p>
          </div>
          <div>
            <p className="text-4xl font-black text-[#1a5c3a]">10×</p>
            <p className="mt-2 text-sm text-gray-500">Moins cher qu'un audit manuel (2 000 € vs 20 000 €)</p>
          </div>
        </div>
      </section>

      {/* ══════════════════════════════════════════ FONCTIONNALITÉS ══ */}
      <section id="fonctionnalites" className="py-24">
        <div className="max-w-7xl mx-auto px-6">

          {/* Bloc 1 — texte gauche, visuel droite */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-16 items-center mb-28">
            <div>
              <p className="text-xs font-semibold uppercase tracking-widest text-[#1a5c3a] mb-4">
                Analyse automatique
              </p>
              <h2 className="text-4xl font-black text-gray-900 leading-tight mb-6">
                Identifier et corriger les allégations non conformes
              </h2>
              <p className="text-gray-500 leading-relaxed mb-4">
                Notre moteur applique automatiquement les 6 règles de la directive EmpCo sur chaque allégation
                saisie. Résultat immédiat : conforme, à risque ou non conforme, avec la référence réglementaire exacte.
              </p>
              <p className="text-gray-500 leading-relaxed mb-8">
                Fini les 3 semaines d'analyse manuelle. En moins d'une heure, votre client dispose d'un
                rapport complet avec plan de correction priorisé.
              </p>
              <button
                onClick={() => navigate('/login')}
                className="px-6 py-3 rounded-full text-sm font-semibold text-white bg-[#1a5c3a] hover:bg-[#14472d] transition-colors"
              >
                Voir une démo →
              </button>
            </div>
            <div className="bg-[#eaf4ee] rounded-3xl p-8">
              <AppMockup />
            </div>
          </div>

          {/* Bloc 2 — visuel gauche, texte droite */}
          <div id="partenaires" className="grid grid-cols-1 lg:grid-cols-2 gap-16 items-center">
            <div className="bg-[#eaf4ee] rounded-3xl p-8 order-2 lg:order-1">
              {/* Mockup rapport PDF */}
              <div className="bg-white rounded-2xl border border-gray-200 shadow-sm p-5 text-xs space-y-3">
                <div className="flex items-center gap-2 border-b border-gray-100 pb-3">
                  <div className="h-6 w-6 rounded bg-[#1a5c3a]" />
                  <span className="font-bold text-gray-700 text-[11px]">Votre Cabinet — Rapport de conformité EmpCo</span>
                </div>
                <div className="space-y-2">
                  <div className="h-2 bg-gray-100 rounded w-3/4" />
                  <div className="h-2 bg-gray-100 rounded w-1/2" />
                </div>
                <div className="grid grid-cols-3 gap-2 pt-1">
                  {['Conformes', 'À risque', 'Non conformes'].map((label, i) => (
                    <div key={label} className="rounded-lg p-2 text-center" style={{ backgroundColor: ['#d4ecdb', '#fef3c7', '#fee2e2'][i] }}>
                      <p className="text-base font-black" style={{ color: ['#166534', '#92400e', '#991b1b'][i] }}>
                        {[4, 2, 3][i]}
                      </p>
                      <p className="text-[9px] text-gray-500 mt-0.5">{label}</p>
                    </div>
                  ))}
                </div>
                <div className="pt-1 space-y-1.5">
                  {['Supprimer "écologique"', 'Remplacer "carbon neutral"', 'Documenter label Ecocert'].map((action, i) => (
                    <div key={action} className="flex items-center gap-2">
                      <span className={`h-1.5 w-1.5 rounded-full flex-shrink-0 ${['bg-red-500', 'bg-red-500', 'bg-green-500'][i]}`} />
                      <span className="text-[10px] text-gray-600">{action}</span>
                    </div>
                  ))}
                </div>
              </div>
            </div>

            <div className="order-1 lg:order-2">
              <p className="text-xs font-semibold uppercase tracking-widest text-[#1a5c3a] mb-4">
                White-label
              </p>
              <h2 className="text-4xl font-black text-gray-900 leading-tight mb-6">
                Votre marque sur chaque rapport
              </h2>
              <div className="space-y-6">
                {WHY.map((item) => (
                  <div key={item.title} className="flex gap-4">
                    <div className="flex-shrink-0 mt-1 h-2 w-2 rounded-full bg-[#1a5c3a]" />
                    <div>
                      <p className="text-sm font-bold text-gray-900 mb-1">{item.title}</p>
                      <p className="text-sm text-gray-500 leading-relaxed">{item.desc}</p>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* ══════════════════════════════════════════ RÈGLES EMPCO ══ */}
      <section id="regles" className="py-24 bg-[#eaf4ee]">
        <div className="max-w-7xl mx-auto px-6">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-16 items-start">

            {/* Titre gauche */}
            <div className="lg:sticky lg:top-24">
              <p className="text-xs font-semibold uppercase tracking-widest text-[#1a5c3a] mb-4">
                Ce que la directive interdit
              </p>
              <h2 className="text-4xl font-black text-gray-900 leading-tight mb-6">
                6 règles vérifiées sur chaque allégation
              </h2>
              <p className="text-gray-500 leading-relaxed">
                La directive (UE) 2024/825 ajoute 4 interdictions absolues à l'Annexe I et renforce 2 exigences
                existantes de la directive 2005/29/CE sur les pratiques commerciales déloyales.
              </p>
            </div>

            {/* Cards droite */}
            <div className="space-y-4">
              {RULES.map((rule) => (
                <div key={rule.article} className="bg-white rounded-2xl p-5 border-l-4"
                  style={{ borderLeftColor: rule.verdict === 'Interdit' ? '#dc2626' : '#d97706' }}>
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-xs font-mono text-gray-400">{rule.article}</span>
                    <span className={`text-xs font-bold px-2.5 py-1 rounded-full ${
                      rule.verdict === 'Interdit' ? 'bg-red-50 text-red-700' : 'bg-amber-50 text-amber-700'
                    }`}>
                      {rule.verdict}
                    </span>
                  </div>
                  <p className="text-sm font-bold text-gray-900 mb-1">{rule.title}</p>
                  <p className="text-xs text-gray-500 leading-relaxed">{rule.desc}</p>
                </div>
              ))}
            </div>
          </div>
        </div>
      </section>

      {/* ════════════════════════════════════════ COMMENT ÇA MARCHE ══ */}
      <section className="py-24">
        <div className="max-w-7xl mx-auto px-6">
          <div className="text-center mb-16">
            <p className="text-xs font-semibold uppercase tracking-widest text-[#1a5c3a] mb-4">
              Process
            </p>
            <h2 className="text-4xl font-black text-gray-900 leading-tight">
              Un audit complet en 3 étapes
            </h2>
          </div>

          {/* Flow visuel */}
          <div className="flex flex-col md:flex-row items-start md:items-center gap-4 mb-16 justify-center">
            {['Saisie', 'Analyse', 'Rapport PDF'].map((label, i) => (
              <div key={label} className="flex items-center gap-4">
                <div className={`rounded-xl px-5 py-2.5 text-sm font-semibold ${
                  i === 2 ? 'bg-[#1a5c3a] text-white' :
                  i === 1 ? 'bg-[#eaf4ee] text-[#1a5c3a] border border-[#1a5c3a]' :
                  'bg-gray-100 text-gray-600 border border-gray-200'
                }`}>
                  {label}
                </div>
                {i < 2 && <span className="text-gray-300 text-xl hidden md:block">→</span>}
              </div>
            ))}
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-10">
            {STEPS.map((s) => (
              <div key={s.step}>
                <p className="text-6xl font-black text-gray-100 mb-4">{s.step}</p>
                <h3 className="text-lg font-bold text-gray-900 mb-3">{s.title}</h3>
                <p className="text-sm text-gray-500 leading-relaxed">{s.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ══════════════════════════════════════════════════ FAQ ══ */}
      <section className="py-24 border-t border-gray-100">
        <div className="max-w-7xl mx-auto px-6">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-16">

            {/* Titre gauche */}
            <div>
              <p className="text-xs font-semibold uppercase tracking-widest text-[#1a5c3a] mb-4">
                Questions fréquentes
              </p>
              <h2 className="text-4xl font-black text-gray-900 leading-tight">
                Audit anti-greenwashing (EmpCo)
              </h2>
            </div>

            {/* Accordion droite */}
            <div>
              {FAQ.map((item) => (
                <FaqItem key={item.q} q={item.q} a={item.a} />
              ))}
              <div className="border-t border-gray-200" />
            </div>
          </div>
        </div>
      </section>

      {/* ═══════════════════════════════════════════════ CTA FINAL ══ */}
      <section className="bg-[#eaf4ee] py-24">
        <div className="max-w-7xl mx-auto px-6 grid grid-cols-1 lg:grid-cols-2 gap-12 items-center">

          {/* Visuel gauche — bloc urgence */}
          <div className="bg-white rounded-3xl p-10 shadow-sm">
            <div className="text-center space-y-4">
              <p className="text-xs font-semibold uppercase tracking-widest text-[#1a5c3a]">Deadline réglementaire</p>
              <p className="text-5xl font-black text-gray-900">27 sept.</p>
              <p className="text-5xl font-black text-gray-900">2026</p>
              <p className="text-sm text-gray-500 max-w-xs mx-auto">
                Transposition de la directive EmpCo dans les droits nationaux des 27 États membres.
                Vos clients ne sont probablement pas conformes.
              </p>
            </div>
          </div>

          {/* Texte droite */}
          <div>
            <h2 className="text-4xl font-black text-gray-900 leading-tight mb-4">
              Proposez l'audit avant qu'il ne soit trop tard
            </h2>
            <p className="text-gray-500 leading-relaxed mb-8">
              Planifiez une démonstration personnalisée et commencez à proposer l'audit EmpCo
              à vos clients. Configuration en 10 minutes, premier rapport en moins d'une heure.
            </p>
            <div className="flex flex-wrap gap-3">
              <button
                onClick={() => navigate('/login')}
                className="px-6 py-3 rounded-full text-sm font-semibold text-white bg-[#1a5c3a] hover:bg-[#14472d] transition-colors"
              >
                Créer un compte partenaire →
              </button>
              <button
                onClick={() => navigate('/contact')}
                className="px-6 py-3 rounded-full text-sm font-semibold text-[#1a5c3a] border-2 border-[#1a5c3a] hover:bg-white transition-colors"
              >
                Contactez-nous →
              </button>
            </div>
            <p className="mt-4 text-xs text-gray-400">
              Déjà partenaire ?{' '}
              <button onClick={() => navigate('/login')} className="underline hover:text-gray-600 transition-colors">
                Se connecter
              </button>
            </p>
          </div>
        </div>
      </section>

      {/* ═══════════════════════════════════════════════════ FOOTER ══ */}
      <footer className="bg-black text-white">
        <div className="max-w-7xl mx-auto px-6 py-16">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-10 mb-14">

            <div>
              <p className="text-xs font-semibold uppercase tracking-widest text-gray-500 mb-5">Logiciel</p>
              <ul className="space-y-3 text-sm text-gray-300">
                <li><a href="#fonctionnalites" className="hover:text-white transition-colors">Fonctionnalités</a></li>
                <li><a href="#regles" className="hover:text-white transition-colors">Règles EmpCo</a></li>
                <li><a href="#partenaires" className="hover:text-white transition-colors">White-label</a></li>
                <li><button onClick={() => navigate('/contact')} className="hover:text-white transition-colors">Tarifs</button></li>
              </ul>
            </div>

            <div>
              <p className="text-xs font-semibold uppercase tracking-widest text-gray-500 mb-5">Réglementation</p>
              <ul className="space-y-3 text-sm text-gray-300">
                <li><span>Directive (UE) 2024/825</span></li>
                <li><span>Annexe I — 6 interdictions</span></li>
                <li><span>Dir. 2005/29/CE modifiée</span></li>
                <li><span>Guide ADEME 2025</span></li>
              </ul>
            </div>

            <div>
              <p className="text-xs font-semibold uppercase tracking-widest text-gray-500 mb-5">Partenaires</p>
              <ul className="space-y-3 text-sm text-gray-300">
                <li><span>Agences de communication</span></li>
                <li><span>Cabinets RSE</span></li>
                <li><span>Avocats spécialisés</span></li>
                <li><button onClick={() => navigate('/contact')} className="hover:text-white transition-colors">Devenir partenaire</button></li>
              </ul>
            </div>

            <div>
              <p className="text-xs font-semibold uppercase tracking-widest text-gray-500 mb-5">Entreprise</p>
              <ul className="space-y-3 text-sm text-gray-300">
                <li><button onClick={() => navigate('/contact')} className="hover:text-white transition-colors">Contact</button></li>
                <li><button onClick={() => navigate('/login')} className="hover:text-white transition-colors">Connexion</button></li>
                <li><button onClick={() => navigate('/login')} className="hover:text-white transition-colors">Créer un compte</button></li>
              </ul>
            </div>
          </div>
        </div>

        {/* Copyright bar */}
        <div className="border-t border-gray-800">
          <div className="max-w-7xl mx-auto px-6 py-5 flex flex-col sm:flex-row items-center justify-between gap-3">
            <div className="flex items-center gap-2">
              <div className="h-6 w-6 rounded bg-[#1a5c3a] flex items-center justify-center">
                <svg className="h-3.5 w-3.5 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                    d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
                </svg>
              </div>
              <span className="text-sm font-semibold" translate="no">GreenAudit</span>
            </div>
            <p className="text-xs text-gray-500 text-center">
              Copyright © 2026 GreenAudit · Conformité Directive (UE) 2024/825 · Transposition avant le 27 septembre 2026
            </p>
          </div>
        </div>
      </footer>

    </div>
  );
}
