import { useNavigate } from 'react-router-dom';

const STEPS = [
  {
    number: '01',
    title: 'Configurez votre logo',
    desc: 'Ajoutez votre logo et vos couleurs pour que vos rapports PDF soient en marque blanche.',
    cta: 'Aller aux paramètres',
    path: '/settings',
  },
  {
    number: '02',
    title: 'Créez votre premier audit',
    desc: 'Saisissez les allégations environnementales de votre client et lancez l\'analyse en quelques minutes.',
    cta: 'Créer un audit',
    path: '/scan',
  },
  {
    number: '03',
    title: 'Générez votre premier rapport',
    desc: 'Téléchargez le PDF complet avec verdicts, recommandations et références réglementaires — prêt à facturer.',
    cta: 'Voir mes audits',
    path: '/',
  },
];

export default function PaymentSuccess() {
  const navigate = useNavigate();

  return (
    <div className="min-h-screen bg-[#eaf4ee] flex items-center justify-center px-4 py-12">
      <div className="w-full max-w-xl">

        {/* Logo + confirmation */}
        <div className="text-center mb-10">
          <img src="/logo.png" alt="GreenAudit" className="h-16 w-auto object-contain mx-auto mb-6" />
          <div className="inline-flex items-center justify-center w-14 h-14 rounded-full bg-[#1a5c3a] mb-4">
            <svg className="w-7 h-7 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M5 13l4 4L19 7" />
            </svg>
          </div>
          <h1 className="text-3xl font-black text-gray-900 mb-2">Bienvenue sur le plan Pro</h1>
          <p className="text-gray-500 text-sm">Votre abonnement est actif. Suivez ces 3 étapes pour démarrer.</p>
        </div>

        {/* Checklist */}
        <div className="space-y-4 mb-8">
          {STEPS.map((step) => (
            <div key={step.number} className="bg-white rounded-2xl p-6 flex items-start gap-5 shadow-sm">
              <span className="text-2xl font-black text-[#1a5c3a] leading-none mt-0.5">{step.number}</span>
              <div className="flex-1">
                <p className="font-bold text-gray-900 mb-1">{step.title}</p>
                <p className="text-sm text-gray-500 mb-3">{step.desc}</p>
                <button
                  onClick={() => navigate(step.path)}
                  className="text-sm font-semibold text-[#1a5c3a] hover:underline"
                >
                  {step.cta} →
                </button>
              </div>
            </div>
          ))}
        </div>

        <button
          onClick={() => navigate('/')}
          className="w-full rounded-full py-3 text-sm font-semibold text-white bg-[#1a5c3a] hover:bg-[#14472d] transition-colors"
        >
          Aller au dashboard
        </button>
      </div>
    </div>
  );
}
