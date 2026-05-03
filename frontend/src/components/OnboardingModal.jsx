import { useState } from 'react';
import { useNavigate } from 'react-router-dom';

const STEPS = [
  {
    icon: (
      <svg className="w-10 h-10 text-[#1a5c3a]" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
      </svg>
    ),
    title: 'Scannez un site',
    desc: "Entrez l'URL d'un site web. GreenAudit extrait automatiquement toutes les allégations environnementales en 30 à 60 secondes.",
  },
  {
    icon: (
      <svg className="w-10 h-10 text-[#1a5c3a]" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
      </svg>
    ),
    title: 'Voyez les allégations à risque',
    desc: "Chaque allégation est classée selon les 7 critères de la directive EmpCo : spécificité, preuves, labels, proportionnalité… avec un score global de risque.",
  },
  {
    icon: (
      <svg className="w-10 h-10 text-[#1a5c3a]" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
      </svg>
    ),
    title: 'Générez le rapport PDF',
    desc: "Avec le plan Partner, complétez l'analyse, ajoutez vos preuves et générez un rapport PDF white-label prêt à présenter à votre client.",
  },
];

export default function OnboardingModal({ onClose }) {
  const [step, setStep] = useState(0);
  const navigate = useNavigate();

  const isLast = step === STEPS.length - 1;

  const handleNext = () => {
    if (isLast) {
      onClose();
      navigate('/scan');
    } else {
      setStep((s) => s + 1);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 px-4">
      <div className="bg-white rounded-2xl shadow-xl w-full max-w-md p-8 relative">

        <button
          onClick={onClose}
          className="absolute top-4 right-4 text-gray-300 hover:text-gray-500 transition-colors"
        >
          <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>

        <p className="text-xs font-semibold uppercase tracking-widest text-[#1a5c3a] mb-6">
          Bienvenue sur GreenAudit
        </p>

        {/* Indicateur d'étapes */}
        <div className="flex gap-2 mb-8">
          {STEPS.map((_, i) => (
            <div
              key={i}
              className={`h-1 flex-1 rounded-full transition-all ${i <= step ? 'bg-[#1a5c3a]' : 'bg-gray-100'}`}
            />
          ))}
        </div>

        {/* Contenu de l'étape */}
        <div className="flex flex-col items-center text-center gap-4 mb-8">
          <div className="w-16 h-16 rounded-2xl bg-[#eaf4ee] flex items-center justify-center">
            {STEPS[step].icon}
          </div>
          <div>
            <p className="text-xs text-gray-400 mb-1">Étape {step + 1} sur {STEPS.length}</p>
            <h2 className="text-xl font-bold text-gray-900 mb-2">{STEPS[step].title}</h2>
            <p className="text-sm text-gray-500 leading-relaxed">{STEPS[step].desc}</p>
          </div>
        </div>

        {/* Actions */}
        <div className="flex gap-3">
          {step > 0 && (
            <button
              onClick={() => setStep((s) => s - 1)}
              className="flex-1 py-2.5 rounded-full text-sm font-medium border border-gray-200 text-gray-600 hover:bg-gray-50 transition-colors"
            >
              Retour
            </button>
          )}
          <button
            onClick={handleNext}
            className="flex-1 py-2.5 rounded-full text-sm font-semibold text-white bg-[#1a5c3a] hover:bg-[#14472d] transition-colors"
          >
            {isLast ? 'Lancer mon premier scan →' : 'Suivant →'}
          </button>
        </div>
      </div>
    </div>
  );
}
