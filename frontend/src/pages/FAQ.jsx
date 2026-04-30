import { useState } from 'react';
import { Link } from 'react-router-dom';

const FAQS = [
  {
    q: "Qu'est-ce que la directive EmpCo ?",
    a: "La directive EmpCo (EU 2024/825) entre en vigueur le 27 septembre 2026. Elle interdit les allégations environnementales vagues (\"écologique\", \"vert\", \"durable\") sans preuve mesurable, les labels auto-décernés sans certification tierce, et les revendications de neutralité carbone basées uniquement sur la compensation. Les entreprises contrevenantes s'exposent à des amendes.",
  },
  {
    q: "Comment fonctionne l'analyse automatique (scan) ?",
    a: "Entrez l'URL d'une page web (idéalement la page RSE ou développement durable). GreenAudit extrait automatiquement les allégations environnementales, les classe selon la directive EmpCo, et génère un rapport de conformité PDF. Le scan prend 30 à 60 secondes.",
  },
  {
    q: "Le scan ne trouve pas mon site — que faire ?",
    a: "Vérifiez que l'URL est accessible publiquement sans connexion. Essayez une URL plus spécifique : la page RSE, engagements, développement durable ou impact de l'entreprise (ex: https://exemple.fr/rse). Évitez les pages avec connexion obligatoire ou les PDFs.",
  },
  {
    q: "Quelle est la différence entre \"liste noire\" et \"cas par cas\" ?",
    a: "Liste noire : l'allégation est interdite par la directive EmpCo, quelle que soit la preuve fournie (ex: neutralité carbone par compensation, label auto-décerné, terme générique sans qualification). Cas par cas : l'allégation est autorisée si elle est justifiée et documentée — le rapport indique ce qu'il faut prouver.",
  },
  {
    q: "Qu'est-ce qu'un label auto-décerné ?",
    a: "Un label créé par l'entreprise elle-même, sans vérification par un organisme indépendant. Exemple : \"Label GreenMark\" inventé par la marque. C'est interdit par EmpCo. Seuls les labels certifiés par un tiers accrédité (Ecolabel EU, NF Environnement, FSC, etc.) sont acceptés.",
  },
  {
    q: "Comment utiliser l'audit manuel ?",
    a: "Cliquez sur \"Nouvel audit\", renseignez les informations de l'entreprise, puis ajoutez chaque allégation une par une avec son contexte (type de support, portée, preuves disponibles, labels). Lancez l'analyse pour obtenir le verdict et le rapport PDF.",
  },
  {
    q: "Le rapport PDF est-il utilisable directement chez un client ?",
    a: "Oui. Il est structuré pour être remis à un client final : synthèse du score, détail claim par claim avec les articles EmpCo cités, plan de correction priorisé, et références réglementaires. En plan Pro vous pouvez personnaliser le branding avec votre logo.",
  },
  {
    q: "Combien d'audits puis-je faire ?",
    a: "Plan Starter : 1 audit complet. Plan Pro : 15 audits par mois, audits d'équipe, branding white-label. Pour passer au Pro, allez dans Paramètres > Abonnement.",
  },
  {
    q: "Les données de mes clients sont-elles conservées ?",
    a: "Les données saisies (allégations, preuves) sont stockées pour générer le rapport et restent accessibles dans votre dashboard. Aucune donnée n'est partagée avec des tiers. Consultez notre politique de confidentialité pour le détail.",
  },
  {
    q: "Ce rapport remplace-t-il un conseil juridique ?",
    a: "Non. GreenAudit est un outil d'aide à la conformité qui automatise l'analyse réglementaire. Il ne constitue pas un avis juridique. Pour des situations contentieuses ou à fort enjeu, consultez un avocat spécialisé en droit de la consommation.",
  },
];

export default function FAQ() {
  const [open, setOpen] = useState(null);

  return (
    <div className="max-w-3xl mx-auto">
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-gray-900 mb-2">Questions fréquentes</h1>
        <p className="text-gray-500">
          Tout ce qu'il faut savoir pour utiliser GreenAudit efficacement.
          Une question manque ?{' '}
          <Link to="/contact" className="text-green-700 hover:underline">
            Contactez-nous
          </Link>
          .
        </p>
      </div>

      <div className="space-y-2">
        {FAQS.map((item, i) => (
          <div key={i} className="bg-white rounded-xl border border-gray-100 shadow-sm overflow-hidden">
            <button
              className="w-full text-left px-6 py-4 flex items-center justify-between gap-4 hover:bg-gray-50 transition-colors"
              onClick={() => setOpen(open === i ? null : i)}
            >
              <span className="font-medium text-gray-800">{item.q}</span>
              <span className="text-gray-400 flex-shrink-0 text-lg">
                {open === i ? '−' : '+'}
              </span>
            </button>
            {open === i && (
              <div className="px-6 pb-5 text-gray-600 text-sm leading-relaxed border-t border-gray-50">
                <p className="pt-4">{item.a}</p>
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
