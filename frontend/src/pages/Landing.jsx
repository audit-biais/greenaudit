import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../api/auth';
import api from '../api/client';

/* ─── Données ──────────────────────────────────────────────────────────────── */

const STEPS = [
  {
    step: '01',
    title: 'Saisissez les allégations',
    desc: "Entrez les allégations environnementales de votre client : \"éco-responsable\", \"durable\", \"carbon neutral\"… telles qu'elles apparaissent sur son site, packaging ou publicité. 10 à 20 minutes suffisent.",
  },
  {
    step: '02',
    title: 'Analyse automatique en quelques secondes',
    desc: "Notre moteur applique les 6 interdictions de l'Annexe I de la directive (UE) 2024/825 sur chaque allégation. Résultat immédiat : conforme, à risque ou non conforme — avec l'article exact violé.",
  },
  {
    step: '03',
    title: 'Rapport PDF prêt à facturer',
    desc: "Téléchargez un rapport à votre logo et vos couleurs : verdict par allégation, références réglementaires, recommandations de correction. Revendez-le en marque blanche.",
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
    title: '100% white-label — votre marque, pas la nôtre',
    desc: 'Votre logo, vos couleurs, vos coordonnées sur chaque rapport. Le client final ne voit que votre cabinet. Vous restez l\'expert.',
  },
  {
    title: 'Références réglementaires exactes',
    desc: 'Chaque verdict cite l\'article précis de la directive (UE) 2024/825. Le rapport est défendable juridiquement face à un contrôle DGCCRF ou un contentieux client.',
  },
  {
    title: 'Premier rapport en moins d\'une heure',
    desc: 'Un audit manuel prend 2 à 4 semaines. GreenAudit produit le même niveau d\'analyse en moins d\'une heure. Vos clients attendent une réponse rapide — donnez-la leur.',
  },
];

const FAQ = [
  {
    q: 'Combien puis-je facturer un audit à mon client ?',
    a: 'Les partenaires facturent généralement entre 300 € et 1 500 € par audit selon leur positionnement, la taille du client et le nombre d\'allégations analysées. Un cabinet RSE ou un avocat peut justifier facilement 1 000 € pour un rapport complet avec références réglementaires et plan de correction.',
  },
  {
    q: 'À qui s\'adresse GreenAudit ?',
    a: 'GreenAudit est exclusivement destiné aux professionnels revendeurs : agences de communication, cabinets RSE/ESG, avocats spécialisés, consultants indépendants. Vous achetez l\'outil en marque blanche et le revendez à vos clients sous votre identité.',
  },
  {
    q: 'Comment fonctionne le white-label ?',
    a: 'Vous configurez votre logo, vos couleurs et vos coordonnées dans les paramètres en 5 minutes. Chaque rapport PDF généré portera uniquement votre identité visuelle. Vos clients ne voient jamais la marque GreenAudit.',
  },
  {
    q: 'Les rapports sont-ils utilisables en cas de contrôle ?',
    a: 'Oui. Chaque rapport cite les articles exacts de la directive (UE) 2024/825 et de la directive 2005/29/CE modifiée. Il constitue une base documentaire solide pour un contrôle DGCCRF ou un contentieux. Il ne remplace pas le conseil d\'un avocat mais le complète utilement.',
  },
  {
    q: 'Quelles allégations sont concernées par EmpCo ?',
    a: 'Toute allégation environnementale destinée aux consommateurs dans l\'UE : "éco-responsable", "durable", "respectueux de l\'environnement", "carbon neutral", "zéro émission"… La directive interdit 4 pratiques via l\'Annexe I et renforce 2 exigences existantes. La majorité des marques utilisant ce type de formulations ne sont pas conformes.',
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

/* ─── Gauge Mockup ──────────────────────────────────────────────────────────── */
function GaugeMockup() {
  const cx = 200, cy = 210, r = 150, thick = 34;
  const score = 40;
  const toRad = d => d * Math.PI / 180;
  // pt(d) : coordonnée sur le cercle à l'angle d (convention math standard, Y inversé SVG)
  const pt = d => [
    parseFloat((cx + r * Math.cos(toRad(d))).toFixed(2)),
    parseFloat((cy - r * Math.sin(toRad(d))).toFixed(2)),
  ];
  // sweep=1 = sens horaire SVG = monte vers le haut depuis la gauche (correct pour jauge)
  const arcSeg = (d1, d2, color, i) => {
    const [x1, y1] = pt(d1);
    const [x2, y2] = pt(d2);
    return (
      <path key={i} d={`M ${x1} ${y1} A ${r} ${r} 0 0 1 ${x2} ${y2}`}
        fill="none" stroke={color} strokeWidth={thick} strokeLinecap="butt" />
    );
  };
  // 5 zones de 36° : rouge (score bas = risque élevé) → vert (score haut = conforme)
  const segments = [
    [180, 144, '#dc2626'],
    [144, 108, '#ea580c'],
    [108,  72, '#f97316'],
    [ 72,  36, '#a3e635'],
    [ 36,   0, '#22c55e'],
  ];
  // Aiguille à 40% : angle = 180 - 40%*180 = 108°
  const needleDeg = 180 - (score / 100) * 180;
  const nr = r - 25;
  const [nx, ny] = [
    parseFloat((cx + nr * Math.cos(toRad(needleDeg))).toFixed(2)),
    parseFloat((cy - nr * Math.sin(toRad(needleDeg))).toFixed(2)),
  ];

  return (
    <div className="bg-white rounded-2xl border border-gray-200 shadow-sm p-5 text-center">
      <p style={{ fontSize: '1rem', fontWeight: 800, color: '#166534', marginBottom: '0.15rem' }}>
        Rapport d'audit anti-greenwashing
      </p>
      <p style={{ fontSize: '0.7rem', color: '#6b7280', marginBottom: '0.6rem' }}>
        Directive EmpCo (EU 2024/825)
      </p>
      <p style={{ fontSize: '0.82rem', fontWeight: 700, color: '#111', marginBottom: '0.1rem' }}>BioMarket France</p>
      <p style={{ fontSize: '0.7rem', color: '#6b7280', marginBottom: '0.5rem' }}>Secteur : alimentaire</p>

      <svg viewBox="30 40 340 195" style={{ width: '100%', display: 'block' }}>
        {/* Arcs colorés : sweep=1 monte vers le haut */}
        {segments.map(([d1, d2, c], i) => arcSeg(d1, d2, c, i))}
        {/* Aiguille */}
        <line x1={cx} y1={cy} x2={nx} y2={ny} stroke="#1f2937" strokeWidth="4" strokeLinecap="round" />
        <circle cx={cx} cy={cy} r="9" fill="#1f2937" />
        {/* Score */}
        <text x={cx} y={cy - 18} textAnchor="middle" fontSize="38" fontWeight="900" fill="#f97316">{score}</text>
        <text x={cx} y={cy} textAnchor="middle" fontSize="13" fill="#9ca3af">/100</text>
        {/* Labels 0 / 100 */}
        <text x={pt(180)[0] + 4} y={pt(180)[1] + 18} textAnchor="middle" fontSize="11" fill="#9ca3af">0</text>
        <text x={pt(0)[0] - 4}   y={pt(0)[1] + 18}   textAnchor="middle" fontSize="11" fill="#9ca3af">100</text>
      </svg>

      <p style={{ color: '#f97316', fontWeight: 700, fontSize: '1rem', marginBottom: '0.75rem' }}>Risque élevé</p>
      <div style={{ display: 'flex', justifyContent: 'center', gap: '1.5rem', flexWrap: 'wrap' }}>
        {[['#dc2626','3 non conformes'],['#f97316','0 à risque'],['#22c55e','2 conformes']].map(([color, label]) => (
          <span key={label} style={{ display: 'flex', alignItems: 'center', gap: '0.35rem', fontSize: '0.72rem', color: '#6b7280' }}>
            <span style={{ width: 10, height: 10, borderRadius: '50%', background: color, flexShrink: 0, display: 'inline-block' }} />
            {label}
          </span>
        ))}
      </div>
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
  const { user } = useAuth();
  const [checkoutLoading, setCheckoutLoading] = useState(false);

  const handleProCheckout = async () => {
    if (!user) { navigate('/login'); return; }
    setCheckoutLoading(true);
    try {
      const res = await api.post('/payment/create-checkout');
      window.location.href = res.data.checkout_url;
    } catch {
      alert('Erreur lors de la redirection vers le paiement. Réessayez.');
      setCheckoutLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-white font-sans">

      {/* ═══════════════════════════════════════════════════════ NAVBAR ══ */}
      <nav className="sticky top-0 z-50 bg-white border-b border-gray-100">
        <div className="max-w-7xl mx-auto px-6 h-16 flex items-center justify-between">

          {/* Logo */}
          <div className="flex items-center gap-2 flex-shrink-0">
            <img src="/logo.png" alt="GreenAudit" className="h-32 w-auto object-contain" />
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
            {user ? (
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
                  Commencer maintenant →
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
              <GaugeMockup />
            </div>
          </div>

          {/* Texte droite */}
          <div className="order-1 lg:order-2">
            <p className="text-xs font-semibold uppercase tracking-widest text-[#1a5c3a] mb-4">
              Directive (UE) 2024/825 · Sanctions dès septembre 2026
            </p>
            <h1 className="text-4xl sm:text-5xl font-black text-gray-900 leading-tight mb-6">
              La réglementation se durcit sur le greenwashing. Transformez-la en opportunité de conseil premium.
            </h1>
            <p className="text-base text-gray-500 leading-relaxed mb-8 max-w-lg">
              La directive EmpCo interdit "éco-responsable", "durable", "carbon neutral" sans preuve.
              GreenAudit analyse automatiquement chaque allégation, génère un rapport PDF conforme
              à votre marque et vous permet de le revendre en marque blanche.
            </p>
            <div className="flex flex-wrap gap-3">
              <button
                onClick={() => navigate('/login')}
                className="px-6 py-3 rounded-full text-sm font-semibold text-white bg-[#1a5c3a] hover:bg-[#14472d] transition-colors"
              >
                Lancer un audit gratuit →
              </button>
              <button
                onClick={() => navigate('/contact')}
                className="px-6 py-3 rounded-full text-sm font-semibold text-[#1a5c3a] border-2 border-[#1a5c3a] hover:bg-[#eaf4ee] transition-colors"
              >
                Voir une démo →
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
            <p className="mt-2 text-sm text-gray-500">Deadline réglementaire — vos clients doivent être conformes avant cette date</p>
          </div>
          <div>
            <p className="text-4xl font-black text-[#1a5c3a]">2 000–5 000 €</p>
            <p className="mt-2 text-sm text-gray-500">Fourchette de revente par audit — nouvelle source de revenus récurrents</p>
          </div>
          <div>
            <p className="text-4xl font-black text-[#1a5c3a]">10×</p>
            <p className="mt-2 text-sm text-gray-500">Plus rapide qu'un audit manuel — résultat en moins d'une heure, pas en 3 semaines</p>
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
                Détection automatique
              </p>
              <h2 className="text-4xl font-black text-gray-900 leading-tight mb-6">
                "Éco-responsable", "durable", "vert" — chaque allégation analysée en secondes
              </h2>
              <p className="text-gray-500 leading-relaxed mb-4">
                La majorité des entreprises utilisent des allégations environnementales non conformes sans le savoir.
                GreenAudit détecte immédiatement ce qui est interdit, ce qui est à risque et ce qui est conforme —
                avec l'article exact de la directive (UE) 2024/825.
              </p>
              <p className="text-gray-500 leading-relaxed mb-8">
                En moins d'une heure, votre client reçoit un rapport complet avec plan de correction priorisé.
              </p>
              <button
                onClick={() => navigate('/login')}
                className="px-6 py-3 rounded-full text-sm font-semibold text-white bg-[#1a5c3a] hover:bg-[#14472d] transition-colors"
              >
                Lancer un audit gratuit →
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
                White-label + monétisation
              </p>
              <h2 className="text-4xl font-black text-gray-900 leading-tight mb-6">
                Votre marque sur chaque rapport. Vos revenus sur chaque audit.
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
                6 règles. Vos clients en enfreignent probablement plusieurs.
              </h2>
              <p className="text-gray-500 leading-relaxed">
                La directive (UE) 2024/825 ajoute 4 interdictions absolues à l'Annexe I et renforce 2 exigences
                existantes. "Éco-responsable", "durable", "carbon neutral" sans preuve sont désormais illégaux.
                GreenAudit vérifie chacune de ces règles automatiquement.
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
              Simple à utiliser
            </p>
            <h2 className="text-4xl font-black text-gray-900 leading-tight">
              De zéro à rapport factu­rable en 3 étapes
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
                Vos questions avant de commencer
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

      {/* ══════════════════════════════════════════════ PRICING ══ */}
      <section className="py-24 border-t border-gray-100 bg-white">
        <div className="max-w-7xl mx-auto px-6">
          <div className="text-center mb-16">
            <p className="text-xs font-semibold uppercase tracking-widest text-[#1a5c3a] mb-4">Tarifs</p>
            <h2 className="text-4xl font-black text-gray-900 leading-tight mb-4">
              Un modèle pensé pour les revendeurs
            </h2>
            <p className="text-lg text-gray-500 max-w-2xl mx-auto">
              Vous achetez les audits, vous les revendez à vos clients sous votre marque. Engagement 12 mois sur les plans payants.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-8 max-w-5xl mx-auto">

            {/* Starter */}
            <div className="rounded-2xl border border-gray-200 p-8 flex flex-col">
              <div className="mb-6">
                <p className="text-sm font-semibold text-gray-500 uppercase tracking-widest mb-2">Starter</p>
                <div className="text-4xl font-black text-gray-900 mb-1">Gratuit</div>
                <p className="text-sm text-gray-400">1 audit unique — sans CB</p>
              </div>
              <ul className="space-y-3 mb-8 flex-1">
                {[
                  '1 audit one-shot (non récurrent)',
                  '3 pages scannées maximum',
                  'Score global + verdicts par allégation',
                  'Rapport PDF GreenAudit',
                  'Analyse des 6 critères EmpCo',
                ].map(f => (
                  <li key={f} className="flex items-start gap-2 text-sm text-gray-600">
                    <span className="text-[#1a5c3a] font-bold mt-0.5">✓</span>{f}
                  </li>
                ))}
                {[
                  'White-label',
                  'Recommandations de correction',
                  'Evidence Vault',
                  'Monitoring continu',
                ].map(f => (
                  <li key={f} className="flex items-start gap-2 text-sm text-gray-400">
                    <span className="mt-0.5">–</span>{f}
                  </li>
                ))}
              </ul>
              <button
                onClick={() => navigate('/login')}
                className="w-full rounded-full py-3 text-sm font-semibold border border-gray-300 text-gray-700 hover:border-gray-400 transition-colors"
              >
                Scanner un site gratuitement
              </button>
            </div>

            {/* Pro — mis en avant */}
            <div className="rounded-2xl border-2 border-[#1a5c3a] p-8 flex flex-col relative shadow-lg">
              <div className="absolute -top-3 left-1/2 -translate-x-1/2">
                <span className="bg-[#1a5c3a] text-white text-xs font-semibold px-4 py-1 rounded-full">Le plus choisi</span>
              </div>
              <div className="mb-6">
                <p className="text-sm font-semibold text-[#1a5c3a] uppercase tracking-widest mb-2">Pro</p>
                <div className="text-4xl font-black text-gray-900 mb-1">2 990 €<span className="text-lg font-normal text-gray-400">/mois</span></div>
                <p className="text-sm text-gray-400">15 audits/mois · Engagement 12 mois</p>
              </div>
              <ul className="space-y-3 mb-8 flex-1">
                {[
                  '15 audits complets par mois',
                  'Pages illimitées par audit',
                  'Rapport PDF complet',
                  'White-label (logo + couleurs + coordonnées)',
                  'Corrections suggérées conformes EmpCo',
                  'Dossier de preuves (ZIP DGCCRF)',
                  'Monitoring continu du site',
                  'Suivi des corrections par allégation',
                  'Jusqu\'à 10 utilisateurs',
                ].map(f => (
                  <li key={f} className="flex items-start gap-2 text-sm text-gray-600">
                    <span className="text-[#1a5c3a] font-bold mt-0.5">✓</span>{f}
                  </li>
                ))}
              </ul>
              <button
                onClick={handleProCheckout}
                disabled={checkoutLoading}
                className="w-full rounded-full py-3 text-sm font-semibold text-white bg-[#1a5c3a] hover:bg-[#14472d] transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {checkoutLoading ? 'Redirection...' : 'Souscrire au plan Pro'}
              </button>
            </div>

            {/* Entreprise */}
            <div className="rounded-2xl border border-gray-200 p-8 flex flex-col bg-gray-50">
              <div className="mb-6">
                <p className="text-sm font-semibold text-gray-500 uppercase tracking-widest mb-2">Entreprise</p>
                <div className="text-4xl font-black text-gray-900 mb-1">Sur devis</div>
                <p className="text-sm text-gray-400">À partir de 50 000 €/an</p>
              </div>
              <ul className="space-y-3 mb-8 flex-1">
                {[
                  'Audits illimités',
                  'Utilisateurs illimités',
                  'White-label (logo + couleurs + coordonnées)',
                  'Toutes les features du plan Pro',
                  'Support premium',
                  'Facturation sur mesure',
                ].map(f => (
                  <li key={f} className="flex items-start gap-2 text-sm text-gray-600">
                    <span className="text-[#1a5c3a] font-bold mt-0.5">✓</span>{f}
                  </li>
                ))}
              </ul>
              <button
                onClick={() => navigate('/contact')}
                className="w-full rounded-full py-3 text-sm font-semibold border border-gray-300 text-gray-700 hover:border-gray-400 transition-colors"
              >
                Nous contacter
              </button>
            </div>

          </div>

          {/* ROI partenaire */}
          <div className="mt-16 max-w-2xl mx-auto bg-[#eaf4ee] rounded-2xl p-8 text-center">
            <p className="text-sm font-semibold uppercase tracking-widest text-[#1a5c3a] mb-3">Économie partenaire</p>
            <p className="text-gray-700 text-sm leading-relaxed">
              Scénario : 10 audits/mois revendus à 2 000 € chacun.<br/>
              <span className="font-bold text-gray-900">240 000 € de revenu annuel</span> — coût GreenAudit : 35 880 €.<br/>
              Marge partenaire : <span className="font-bold text-[#1a5c3a]">85% — ROI ×6,7</span>.
            </p>
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
                Mise en application de la directive EmpCo. Sanctions pour toute allégation environnementale non conforme.
                Chaque semaine perdue réduit votre avance.
              </p>
            </div>
          </div>

          {/* Texte droite */}
          <div>
            <h2 className="text-4xl font-black text-gray-900 leading-tight mb-4">
              Ceux qui commencent maintenant auront 12 mois d'avance sur leurs concurrents
            </h2>
            <p className="text-gray-500 leading-relaxed mb-8">
              Vos clients ne sont probablement pas conformes. Ils ne le savent pas encore.
              Positionnez-vous comme l'expert EmpCo de référence avant septembre 2026.
              Premier rapport en moins d'une heure, configuration en 10 minutes.
            </p>
            <div className="flex flex-wrap gap-3">
              <button
                onClick={() => navigate('/login')}
                className="px-6 py-3 rounded-full text-sm font-semibold text-white bg-[#1a5c3a] hover:bg-[#14472d] transition-colors"
              >
                Lancer un audit gratuit →
              </button>
              <button
                onClick={() => navigate('/contact')}
                className="px-6 py-3 rounded-full text-sm font-semibold text-[#1a5c3a] border-2 border-[#1a5c3a] hover:bg-white transition-colors"
              >
                Voir une démo →
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
              <img src="/logo.png" alt="GreenAudit" className="h-24 w-auto object-contain" />
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
