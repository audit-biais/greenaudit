import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../api/auth';
import api from '../api/client';

/* ─── Données ──────────────────────────────────────────────────────────────── */

const STEPS = [
  {
    step: '01',
    title: 'Saisissez ou scannez les allégations',
    desc: "Analysez les formulations environnementales telles qu'elles apparaissent sur un site, une page produit, un packaging ou une publicité. La saisie manuelle ou le scan automatique prennent 10 à 20 minutes.",
  },
  {
    step: '02',
    title: 'Classement automatique par niveau de risque',
    desc: "GreenAudit applique une grille de lecture EmpCo pour classer chaque allégation : risque élevé, risque modéré, à documenter ou apparemment conforme — avec la référence réglementaire associée.",
  },
  {
    step: '03',
    title: 'Rapport PDF prêt à présenter',
    desc: "Téléchargez un rapport à votre logo : synthèse, verdicts, références réglementaires, recommandations et dossier de preuves associé. Présentable à votre client sous votre marque.",
  },
];

const RULES = [
  {
    article: 'Annexe I, 4 bis',
    title: 'Allégations génériques',
    desc: '"Écologique", "durable", "respectueux de l\'environnement"… Ces termes peuvent devenir risqués lorsqu\'ils ne sont pas justifiés, contextualisés ou appuyés sur une performance environnementale excellente reconnue.',
    verdict: 'Risque élevé',
  },
  {
    article: 'Annexe I, 4 quater',
    title: 'Neutralité carbone et compensation',
    desc: 'Affirmer qu\'un produit a un impact neutre ou positif sur les émissions de GES sur la seule base de la compensation carbone est fortement encadré par la directive et constitue un point de vigilance prioritaire.',
    verdict: 'Risque élevé',
  },
  {
    article: 'Annexe I, 2 bis',
    title: 'Labels non certifiés',
    desc: 'Afficher un label de développement durable non fondé sur un système de certification par un tiers indépendant ou une autorité publique peut être qualifié de pratique commerciale trompeuse.',
    verdict: 'Risque élevé',
  },
  {
    article: 'Annexe I, 4 ter',
    title: 'Allégations trop larges',
    desc: 'Présenter une allégation concernant l\'ensemble du produit ou de l\'entreprise alors qu\'elle ne porte que sur un aspect spécifique peut nécessiter une vérification complémentaire et une reformulation.',
    verdict: 'Risque élevé',
  },
  {
    article: 'Art. 6 §2, Dir. 2005/29/CE',
    title: 'Engagements environnementaux futurs',
    desc: 'Les allégations de performance future doivent être étayées par des engagements clairs, un calendrier précis et un suivi indépendant vérifiable pour ne pas être qualifiées de trompeuses.',
    verdict: 'Encadré',
  },
  {
    article: 'Art. 6 §1, Dir. 2005/29/CE',
    title: 'Preuve, traçabilité et documentation',
    desc: 'Toute allégation environnementale doit pouvoir être documentée. Sans preuve vérifiable (certification tierce, données mesurables), l\'allégation peut être considérée comme insuffisamment justifiée.',
    verdict: 'Encadré',
  },
];

const WHY = [
  {
    title: '100 % white-label — votre marque, pas la nôtre',
    desc: 'Votre logo, vos couleurs, vos coordonnées sur chaque rapport. Le client final ne voit que votre cabinet. Vous restez l\'expert.',
  },
  {
    title: 'Références réglementaires identifiables',
    desc: 'Chaque verdict s\'appuie sur une référence réglementaire identifiable afin d\'aider votre cabinet à documenter l\'analyse, structurer les recommandations et préparer un dossier exploitable en cas de contrôle ou de discussion avec le client.',
  },
  {
    title: 'Première analyse structurée en moins d\'une heure',
    desc: 'La collecte et la préqualification manuelle peuvent prendre plusieurs jours. GreenAudit produit une première analyse structurée en moins d\'une heure, pour que vous puissiez vous concentrer sur le conseil à valeur ajoutée.',
  },
];

const FAQ = [
  {
    q: 'Combien puis-je facturer un audit à mon client ?',
    a: 'Les partenaires facturent généralement entre 1 500 € et 3 000 € par audit selon leur positionnement, la taille du client et le périmètre d\'accompagnement inclus. Un cabinet RSE ou un avocat peut justifier 2 000 € pour un rapport structuré avec références réglementaires et plan de correction. Ces chiffres sont indicatifs et dépendent de votre marché.',
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
    a: 'Les rapports GreenAudit ne constituent pas une garantie de conformité ni un avis juridique. Ils permettent de structurer l\'analyse, de conserver les éléments de preuve, d\'identifier les points de vigilance et de préparer un dossier exploitable en cas de contrôle, d\'échange avec un client ou de revue interne.',
  },
  {
    q: 'GreenAudit remplace-t-il un avocat ou un expert conformité ?',
    a: 'Non. GreenAudit est un outil d\'aide à l\'audit et à la documentation. Il permet de gagner du temps sur la détection, la préqualification et la génération de rapports, mais la validation finale doit rester entre les mains du professionnel.',
  },
  {
    q: 'Quelles allégations sont concernées ?',
    a: 'GreenAudit analyse notamment les allégations génériques, les promesses environnementales futures, les allégations de neutralité carbone, les mentions liées à la compensation, les labels, les comparaisons environnementales et les formulations portant sur tout un produit ou toute une entreprise.',
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
  const pt = d => [
    parseFloat((cx + r * Math.cos(toRad(d))).toFixed(2)),
    parseFloat((cy - r * Math.sin(toRad(d))).toFixed(2)),
  ];
  const arcSeg = (d1, d2, color, i) => {
    const [x1, y1] = pt(d1);
    const [x2, y2] = pt(d2);
    return (
      <path key={i} d={`M ${x1} ${y1} A ${r} ${r} 0 0 1 ${x2} ${y2}`}
        fill="none" stroke={color} strokeWidth={thick} strokeLinecap="butt" />
    );
  };
  const segments = [
    [180, 144, '#dc2626'],
    [144, 108, '#ea580c'],
    [108,  72, '#f97316'],
    [ 72,  36, '#a3e635'],
    [ 36,   0, '#22c55e'],
  ];
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
        {segments.map(([d1, d2, c], i) => arcSeg(d1, d2, c, i))}
        <line x1={cx} y1={cy} x2={nx} y2={ny} stroke="#1f2937" strokeWidth="4" strokeLinecap="round" />
        <circle cx={cx} cy={cy} r="9" fill="#1f2937" />
        <text x={cx} y={cy - 18} textAnchor="middle" fontSize="38" fontWeight="900" fill="#f97316">{score}</text>
        <text x={cx} y={cy} textAnchor="middle" fontSize="13" fill="#9ca3af">/100</text>
        <text x={pt(180)[0] + 4} y={pt(180)[1] + 18} textAnchor="middle" fontSize="11" fill="#9ca3af">0</text>
        <text x={pt(0)[0] - 4}   y={pt(0)[1] + 18}   textAnchor="middle" fontSize="11" fill="#9ca3af">100</text>
      </svg>

      <p style={{ color: '#f97316', fontWeight: 700, fontSize: '1rem', marginBottom: '0.75rem' }}>Risque élevé</p>
      <div style={{ display: 'flex', justifyContent: 'center', gap: '1.5rem', flexWrap: 'wrap' }}>
        {[['#dc2626','3 risque élevé'],['#f97316','0 à vérifier'],['#22c55e','2 documentés']].map(([color, label]) => (
          <span key={label} style={{ display: 'flex', alignItems: 'center', gap: '0.35rem', fontSize: '0.72rem', color: '#6b7280' }}>
            <span style={{ width: 10, height: 10, borderRadius: '50%', background: color, flexShrink: 0, display: 'inline-block' }} />
            {label}
          </span>
        ))}
      </div>
    </div>
  );
}

/* ─── Mockup UI ─────────────────────────────────────────────────────────────── */
function AppMockup() {
  return (
    <div className="bg-white rounded-2xl border border-gray-200 shadow-sm overflow-hidden text-xs font-mono">
      <div className="flex items-center gap-1.5 px-3 py-2 border-b border-gray-100">
        <span className="h-2.5 w-2.5 rounded-full bg-red-400" />
        <span className="h-2.5 w-2.5 rounded-full bg-yellow-400" />
        <span className="h-2.5 w-2.5 rounded-full bg-green-400" />
        <span className="ml-2 text-gray-400 text-[10px]">GreenAudit — Audit #042</span>
      </div>
      <div className="p-4 space-y-3">
        <div className="flex items-center justify-between">
          <span className="text-gray-500 text-[10px] uppercase tracking-wide">Allégation</span>
          <span className="text-gray-500 text-[10px] uppercase tracking-wide">Niveau de risque</span>
        </div>
        {[
          { claim: '"Produit écologique"',    verdict: 'RISQUE ÉLEVÉ',   color: 'text-red-600 bg-red-50' },
          { claim: '"Carbon neutral 2030"',   verdict: 'À VÉRIFIER',     color: 'text-amber-600 bg-amber-50' },
          { claim: '"30% plastique recyclé"', verdict: 'RISQUE MODÉRÉ',  color: 'text-orange-600 bg-orange-50' },
          { claim: '"Label Ecocert certifié"',verdict: 'DOCUMENTÉ',      color: 'text-green-700 bg-green-50' },
        ].map((item) => (
          <div key={item.claim} className="flex items-center justify-between py-1.5 border-b border-gray-50">
            <span className="text-gray-700 text-[11px]">{item.claim}</span>
            <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full ${item.color}`}>
              {item.verdict}
            </span>
          </div>
        ))}
        <div className="pt-2 flex items-center justify-between">
          <span className="text-gray-400 text-[10px]">Score de risque</span>
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
    if (!user) { navigate('/login?checkout=1'); return; }
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

          <div className="flex items-center gap-2 flex-shrink-0">
            <img src="/logo.png" alt="GreenAudit" className="h-32 w-auto object-contain" />
          </div>

          <div className="hidden md:flex items-center gap-8 text-sm text-gray-600">
            <a href="#fonctionnalites" className="hover:text-gray-900 transition-colors">Fonctionnalités</a>
            <a href="#regles" className="hover:text-gray-900 transition-colors">Règles EmpCo</a>
            <a href="#partenaires" className="hover:text-gray-900 transition-colors">Partenaires</a>
            <button onClick={() => document.getElementById('pricing').scrollIntoView({ behavior: 'smooth' })} className="hover:text-gray-900 transition-colors">Tarifs</button>
          </div>

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

          <div className="order-2 lg:order-1">
            <div className="bg-[#d4ecdb] rounded-3xl p-8">
              <GaugeMockup />
            </div>
          </div>

          <div className="order-1 lg:order-2">
            <p className="text-xs font-semibold uppercase tracking-widest text-[#1a5c3a] mb-4">
              Directive (UE) 2024/825 · Application prévue septembre 2026
            </p>
            <h1 className="text-4xl sm:text-5xl font-black text-gray-900 leading-tight mb-6">
              La réglementation se durcit sur les allégations environnementales. Transformez EmpCo en offre d'audit premium pour vos clients.
            </h1>
            <p className="text-base text-gray-500 leading-relaxed mb-4 max-w-lg">
              La directive EmpCo encadre fortement les allégations comme "éco-responsable", "durable", "vert" ou "neutre en carbone" lorsqu'elles ne sont pas clairement justifiées, vérifiables ou correctement contextualisées.
            </p>
            <p className="text-base text-gray-500 leading-relaxed mb-8 max-w-lg">
              GreenAudit aide les cabinets RSE et agences de communication à détecter les allégations environnementales à risque, générer des rapports white-label et centraliser les preuves dans un dossier sécurisé.
            </p>
            <div className="flex flex-wrap gap-3">
              <button
                onClick={() => navigate('/login')}
                className="px-6 py-3 rounded-full text-sm font-semibold text-white bg-[#1a5c3a] hover:bg-[#14472d] transition-colors"
              >
                Lancer un audit test →
              </button>
              <button
                onClick={() => navigate('/contact')}
                className="px-6 py-3 rounded-full text-sm font-semibold text-[#1a5c3a] border-2 border-[#1a5c3a] hover:bg-[#eaf4ee] transition-colors"
              >
                Voir une démo partenaire →
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
            <p className="mt-2 text-sm text-gray-500">Date d'application prévue des mesures issues de la directive EmpCo dans les États membres.</p>
          </div>
          <div>
            <p className="text-4xl font-black text-[#1a5c3a]">2 000–5 000 €</p>
            <p className="mt-2 text-sm text-gray-500">Fourchette indicative de revente possible par audit selon le périmètre, le secteur et l'accompagnement inclus.</p>
          </div>
          <div>
            <p className="text-4xl font-black text-[#1a5c3a]">10×</p>
            <p className="mt-2 text-sm text-gray-500">Préqualification plus rapide qu'un audit entièrement manuel — une première analyse structurée en moins d'une heure.</p>
          </div>
        </div>
      </section>

      {/* ══════════════════════════════════════════ FONCTIONNALITÉS ══ */}
      <section id="fonctionnalites" className="py-24">
        <div className="max-w-7xl mx-auto px-6">

          {/* Bloc 1 */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-16 items-center mb-28">
            <div>
              <p className="text-xs font-semibold uppercase tracking-widest text-[#1a5c3a] mb-4">
                Détection automatisée des allégations à risque
              </p>
              <h2 className="text-4xl font-black text-gray-900 leading-tight mb-6">
                "Éco-responsable", "durable", "vert" — chaque allégation classée par niveau de risque
              </h2>
              <p className="text-gray-500 leading-relaxed mb-4">
                De nombreuses entreprises utilisent des formulations environnementales générales ou insuffisamment documentées sans mesurer leur niveau de risque.
                GreenAudit identifie les allégations sensibles, les classe par niveau de priorité et les associe aux principaux points de vigilance issus de la directive (UE) 2024/825.
              </p>
              <p className="text-gray-500 leading-relaxed mb-8">
                En quelques secondes, vous visualisez ce qui semble conforme, ce qui est à risque et ce qui nécessite une vérification complémentaire — avec la référence réglementaire associée.
              </p>
              <button
                onClick={() => navigate('/login')}
                className="px-6 py-3 rounded-full text-sm font-semibold text-white bg-[#1a5c3a] hover:bg-[#14472d] transition-colors"
              >
                Lancer un audit test →
              </button>
            </div>
            <div className="bg-[#eaf4ee] rounded-3xl p-8">
              <AppMockup />
            </div>
          </div>

          {/* Bloc 2 — white-label */}
          <div id="partenaires" className="grid grid-cols-1 lg:grid-cols-2 gap-16 items-center">
            <div className="bg-[#eaf4ee] rounded-3xl p-8 order-2 lg:order-1">
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
                  {['Documentés', 'À risque', 'À corriger'].map((label, i) => (
                    <div key={label} className="rounded-lg p-2 text-center" style={{ backgroundColor: ['#d4ecdb', '#fef3c7', '#fee2e2'][i] }}>
                      <p className="text-base font-black" style={{ color: ['#166534', '#92400e', '#991b1b'][i] }}>
                        {[4, 2, 3][i]}
                      </p>
                      <p className="text-[9px] text-gray-500 mt-0.5">{label}</p>
                    </div>
                  ))}
                </div>
                <div className="pt-1 space-y-1.5">
                  {['Reformuler "écologique"', 'Documenter neutralité carbone', 'Conserver label Ecocert'].map((action, i) => (
                    <div key={action} className="flex items-center gap-2">
                      <span className={`h-1.5 w-1.5 rounded-full flex-shrink-0 ${['bg-red-500', 'bg-amber-500', 'bg-green-500'][i]}`} />
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
                Votre marque sur chaque rapport. Votre expertise au centre de la relation client.
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
              <p className="mt-6 text-sm text-gray-500 leading-relaxed">
                GreenAudit vous permet de créer une offre d'audit EmpCo sous votre propre marque : rapport PDF personnalisé, recommandations structurées, dossier de preuves et suivi des corrections.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* ══════════════════════════════════════════ RÈGLES EMPCO ══ */}
      <section id="regles" className="py-24 bg-[#eaf4ee]">
        <div className="max-w-7xl mx-auto px-6">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-16 items-start">

            <div className="lg:sticky lg:top-24">
              <p className="text-xs font-semibold uppercase tracking-widest text-[#1a5c3a] mb-4">
                Les principaux risques EmpCo à surveiller
              </p>
              <h2 className="text-4xl font-black text-gray-900 leading-tight mb-6">
                6 familles de risques. Vos clients en utilisent peut-être déjà sans le savoir.
              </h2>
              <p className="text-gray-500 leading-relaxed">
                Allégations génériques, promesses futures, labels, compensation carbone : GreenAudit vous aide à prioriser les points de vigilance.
                La directive (UE) 2024/825 ajoute 4 familles de risques à l'Annexe I et renforce 2 exigences existantes.
                GreenAudit vérifie chacune de ces dimensions automatiquement.
              </p>
            </div>

            <div className="space-y-4">
              {RULES.map((rule) => (
                <div key={rule.article} className="bg-white rounded-2xl p-5 border-l-4"
                  style={{ borderLeftColor: rule.verdict === 'Risque élevé' ? '#dc2626' : '#d97706' }}>
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-xs font-mono text-gray-400">{rule.article}</span>
                    <span className={`text-xs font-bold px-2.5 py-1 rounded-full ${
                      rule.verdict === 'Risque élevé' ? 'bg-red-50 text-red-700' : 'bg-amber-50 text-amber-700'
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

      {/* ══════════════════════════════════════ CE QUE GREENAUDIT N'EST PAS ══ */}
      <section className="py-24 border-t border-gray-100">
        <div className="max-w-7xl mx-auto px-6">
          <div className="text-center mb-12">
            <p className="text-xs font-semibold uppercase tracking-widest text-[#1a5c3a] mb-4">
              Positionnement
            </p>
            <h2 className="text-4xl font-black text-gray-900 leading-tight mb-6">
              Ce que GreenAudit n'est pas
            </h2>
            <p className="text-gray-500 leading-relaxed max-w-2xl mx-auto">
              GreenAudit ne remplace pas un avocat, une autorité administrative ou un audit juridique complet.
              La plateforme fournit une analyse automatisée, structurée et documentée pour aider les professionnels
              à identifier les risques, prioriser les corrections et constituer un dossier de preuves.
            </p>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8 max-w-4xl mx-auto">
            {[
              {
                title: 'Pas une certification officielle',
                desc: 'GreenAudit ne délivre pas de label de conformité. Les résultats sont des éléments d\'analyse, pas une attestation réglementaire.',
              },
              {
                title: 'Pas un avis juridique',
                desc: 'Les rapports servent de base d\'analyse et de documentation. Ils ne remplacent pas le conseil d\'un avocat spécialisé.',
              },
              {
                title: 'Un outil pour professionnels',
                desc: 'Le jugement final reste entre les mains du cabinet, du conseil ou de l\'équipe conformité. GreenAudit structure et accélère le travail d\'analyse.',
              },
            ].map((card) => (
              <div key={card.title} className="bg-gray-50 rounded-2xl p-6 border border-gray-200">
                <p className="text-sm font-bold text-gray-900 mb-2">{card.title}</p>
                <p className="text-sm text-gray-500 leading-relaxed">{card.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ════════════════════════════════════════ COMMENT ÇA MARCHE ══ */}
      <section className="py-24 bg-[#eaf4ee]">
        <div className="max-w-7xl mx-auto px-6">
          <div className="text-center mb-16">
            <p className="text-xs font-semibold uppercase tracking-widest text-[#1a5c3a] mb-4">
              Simple à utiliser
            </p>
            <h2 className="text-4xl font-black text-gray-900 leading-tight">
              De la détection au rapport client en 3 étapes
            </h2>
          </div>

          <div className="flex flex-col md:flex-row items-start md:items-center gap-4 mb-16 justify-center">
            {['Saisie', 'Analyse', 'Rapport PDF'].map((label, i) => (
              <div key={label} className="flex items-center gap-4">
                <div className={`rounded-xl px-5 py-2.5 text-sm font-semibold ${
                  i === 2 ? 'bg-[#1a5c3a] text-white' :
                  i === 1 ? 'bg-white text-[#1a5c3a] border border-[#1a5c3a]' :
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
                <p className="text-6xl font-black text-gray-200 mb-4">{s.step}</p>
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

            <div>
              <p className="text-xs font-semibold uppercase tracking-widest text-[#1a5c3a] mb-4">
                Questions fréquentes
              </p>
              <h2 className="text-4xl font-black text-gray-900 leading-tight">
                Vos questions avant de commencer
              </h2>
            </div>

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
      <section id="pricing" className="py-24 border-t border-gray-100 bg-white">
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

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6 max-w-6xl mx-auto">

            {/* Starter */}
            <div className="rounded-2xl border border-gray-200 p-7 flex flex-col">
              <div className="mb-6">
                <p className="text-sm font-semibold text-gray-500 uppercase tracking-widest mb-2">Starter</p>
                <div className="text-3xl font-black text-gray-900 mb-1">Gratuit</div>
                <p className="text-sm text-gray-400">1 audit test — sans CB</p>
              </div>
              <ul className="space-y-2.5 mb-8 flex-1">
                {[
                  '1 audit one-shot',
                  'Score global + verdicts',
                  'Rapport PDF GreenAudit',
                  'Analyse des 6 critères EmpCo',
                ].map(f => (
                  <li key={f} className="flex items-start gap-2 text-sm text-gray-600">
                    <span className="text-[#1a5c3a] font-bold mt-0.5">✓</span>{f}
                  </li>
                ))}
                {[
                  'White-label',
                  'Recommandations',
                  'Dossier de preuves',
                  'Monitoring',
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
                Scanner gratuitement
              </button>
            </div>

            {/* Partner */}
            <div className="rounded-2xl border border-gray-200 p-7 flex flex-col">
              <div className="mb-6">
                <p className="text-sm font-semibold text-gray-500 uppercase tracking-widest mb-2">Partner</p>
                <div className="text-3xl font-black text-gray-900 mb-1">990 €<span className="text-base font-normal text-gray-400">/mois</span></div>
                <p className="text-sm text-gray-400">5 audits/mois · Pour lancer l'offre EmpCo</p>
              </div>
              <ul className="space-y-2.5 mb-8 flex-1">
                {[
                  '5 audits complets par mois',
                  'Rapport PDF complet',
                  'White-label (logo + couleurs)',
                  'Recommandations de correction',
                  'Dossier de preuves',
                  "Jusqu'à 3 utilisateurs",
                ].map(f => (
                  <li key={f} className="flex items-start gap-2 text-sm text-gray-600">
                    <span className="text-[#1a5c3a] font-bold mt-0.5">✓</span>{f}
                  </li>
                ))}
                {[
                  'Monitoring continu',
                  'Suivi des corrections',
                ].map(f => (
                  <li key={f} className="flex items-start gap-2 text-sm text-gray-400">
                    <span className="mt-0.5">–</span>{f}
                  </li>
                ))}
              </ul>
              <button
                onClick={() => navigate('/contact')}
                className="w-full rounded-full py-3 text-sm font-semibold border border-[#1a5c3a] text-[#1a5c3a] hover:bg-[#eaf4ee] transition-colors"
              >
                Nous contacter
              </button>
            </div>

            {/* Pro Partner — mis en avant */}
            <div className="rounded-2xl border-2 border-[#1a5c3a] p-7 flex flex-col relative shadow-lg">
              <div className="absolute -top-3 left-1/2 -translate-x-1/2">
                <span className="bg-[#1a5c3a] text-white text-xs font-semibold px-4 py-1 rounded-full">Le plus choisi</span>
              </div>
              <div className="mb-6">
                <p className="text-sm font-semibold text-[#1a5c3a] uppercase tracking-widest mb-2">Pro Partner</p>
                <div className="text-3xl font-black text-gray-900 mb-1">2 990 €<span className="text-base font-normal text-gray-400">/mois</span></div>
                <p className="text-sm text-gray-400">15 audits/mois · Engagement 12 mois</p>
              </div>
              <ul className="space-y-2.5 mb-8 flex-1">
                {[
                  '15 audits complets par mois',
                  'Pages illimitées par audit',
                  'Rapport PDF complet',
                  'White-label complet',
                  'Corrections suggérées EmpCo',
                  'Dossier de preuves (SHA-256)',
                  'Monitoring continu du site',
                  'Suivi des corrections',
                  "Jusqu'à 10 utilisateurs",
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
                {checkoutLoading ? 'Redirection...' : 'Souscrire au plan Pro Partner'}
              </button>
            </div>

            {/* Enterprise */}
            <div className="rounded-2xl border border-gray-200 p-7 flex flex-col bg-gray-50">
              <div className="mb-6">
                <p className="text-sm font-semibold text-gray-500 uppercase tracking-widest mb-2">Enterprise</p>
                <div className="text-3xl font-black text-gray-900 mb-1">Sur devis</div>
                <p className="text-sm text-gray-400">À partir de 50 000 €/an</p>
              </div>
              <ul className="space-y-2.5 mb-8 flex-1">
                {[
                  'Audits sur mesure ou volume élevé',
                  'Multi-tenant avancé',
                  'Utilisateurs illimités',
                  'White-label complet',
                  'Support premium dédié',
                  'Onboarding partenaire',
                  'Facturation et conditions personnalisées',
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
              Exemple indicatif : 10 audits/mois revendus 2 000 € chacun.<br/>
              <span className="font-bold text-gray-900">Revenu annuel potentiel : 240 000 €</span> — Coût GreenAudit Pro Partner : 35 880 €/an.<br/>
              Marge brute logicielle estimée : <span className="font-bold text-[#1a5c3a]">environ 85 %</span>, hors temps de conseil, acquisition client et accompagnement.
            </p>
            <p className="mt-3 text-xs text-gray-400 italic">
              Exemple non garanti, dépendant du positionnement, du portefeuille client, du périmètre d'audit et de l'accompagnement vendu.
            </p>
          </div>
        </div>
      </section>

      {/* ═══════════════════════════════════════════════ CTA FINAL ══ */}
      <section className="bg-[#eaf4ee] py-24">
        <div className="max-w-7xl mx-auto px-6 grid grid-cols-1 lg:grid-cols-2 gap-12 items-center">

          <div className="bg-white rounded-3xl p-10 shadow-sm">
            <div className="text-center space-y-4">
              <p className="text-xs font-semibold uppercase tracking-widest text-[#1a5c3a]">Échéance réglementaire</p>
              <p className="text-5xl font-black text-gray-900">27 sept.</p>
              <p className="text-5xl font-black text-gray-900">2026</p>
              <p className="text-sm text-gray-500 max-w-xs mx-auto">
                À partir de cette échéance, les entreprises devront être prêtes à justifier, contextualiser et documenter leurs allégations environnementales selon les mesures de transposition applicables.
                Chaque semaine perdue réduit votre avance.
              </p>
            </div>
          </div>

          <div>
            <h2 className="text-4xl font-black text-gray-900 leading-tight mb-4">
              Ceux qui commencent maintenant auront 12 mois d'avance sur leurs concurrents
            </h2>
            <p className="text-gray-500 leading-relaxed mb-8">
              Beaucoup d'entreprises utilisent déjà des formulations environnementales qui méritent d'être revues, précisées ou documentées.
              Positionnez-vous comme l'expert EmpCo de référence avant septembre 2026.
              Première analyse structurée en moins d'une heure, configuration en 10 minutes.
            </p>
            <div className="flex flex-wrap gap-3">
              <button
                onClick={() => navigate('/login')}
                className="px-6 py-3 rounded-full text-sm font-semibold text-white bg-[#1a5c3a] hover:bg-[#14472d] transition-colors"
              >
                Lancer un audit test →
              </button>
              <button
                onClick={() => navigate('/contact')}
                className="px-6 py-3 rounded-full text-sm font-semibold text-[#1a5c3a] border-2 border-[#1a5c3a] hover:bg-white transition-colors"
              >
                Voir une démo partenaire →
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
                <li><a href="#regles" className="hover:text-white transition-colors">Risques EmpCo</a></li>
                <li><a href="#partenaires" className="hover:text-white transition-colors">White-label</a></li>
                <li><button onClick={() => document.getElementById('pricing').scrollIntoView({ behavior: 'smooth' })} className="hover:text-white transition-colors">Tarifs</button></li>
              </ul>
            </div>

            <div>
              <p className="text-xs font-semibold uppercase tracking-widest text-gray-500 mb-5">Réglementation</p>
              <ul className="space-y-3 text-sm text-gray-300">
                <li><span>Directive (UE) 2024/825</span></li>
                <li><span>Annexe I — 6 familles de risques</span></li>
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

        <div className="border-t border-gray-800">
          <div className="max-w-7xl mx-auto px-6 py-5 flex flex-col sm:flex-row items-center justify-between gap-3">
            <div className="flex items-center gap-2">
              <img src="/logo.png" alt="GreenAudit" className="h-24 w-auto object-contain" />
            </div>
            <p className="text-xs text-gray-500 text-center">
              Copyright © 2026 GreenAudit · Pré-audit et documentation des allégations environnementales · Directive (UE) 2024/825 · Application prévue à partir du 27 septembre 2026
            </p>
            <div className="flex gap-4 text-xs text-gray-500">
              <button onClick={() => navigate('/mentions-legales')} className="hover:text-white transition-colors">Mentions légales</button>
              <button onClick={() => navigate('/cgv')} className="hover:text-white transition-colors">CGV</button>
              <button onClick={() => navigate('/politique-de-confidentialite')} className="hover:text-white transition-colors">Confidentialité</button>
              <button onClick={() => navigate('/dpa')} className="hover:text-white transition-colors">DPA</button>
            </div>
          </div>
        </div>
      </footer>

    </div>
  );
}
