import { useNavigate } from 'react-router-dom';

export default function CGV() {
  const navigate = useNavigate();

  return (
    <div className="min-h-screen bg-white">
      <nav className="sticky top-0 z-50 bg-white border-b border-gray-100">
        <div className="max-w-7xl mx-auto px-6 h-16 flex items-center justify-between">
          <button onClick={() => navigate('/landing')} className="flex items-center">
            <img src="/logo.png" alt="GreenAudit" className="h-32 w-auto object-contain" />
          </button>
          <button onClick={() => navigate('/login')}
            className="text-sm font-semibold text-white px-5 py-2 rounded-full bg-[#1a5c3a] hover:bg-[#14472d] transition-colors">
            Connexion →
          </button>
        </div>
      </nav>

      <div className="max-w-3xl mx-auto px-6 py-16">
        <h1 className="text-3xl font-black text-gray-900 mb-2">Conditions Générales de Vente</h1>
        <p className="text-sm text-gray-400 mb-12">Dernière mise à jour : avril 2026</p>

        <div className="space-y-10 text-sm text-gray-700 leading-relaxed">

          <section>
            <h2 className="text-lg font-bold text-gray-900 mb-3">1. Objet</h2>
            <p>Les présentes Conditions Générales de Vente (CGV) régissent l'ensemble des relations contractuelles entre GreenAudit (ci-après « le Prestataire ») et tout partenaire souscrivant à un abonnement ou utilisant la plateforme green-audit.fr (ci-après « le Partenaire »).</p>
            <p className="mt-2">GreenAudit est une plateforme SaaS d'audit automatisé de conformité anti-greenwashing, conforme à la Directive (UE) 2024/825 (EmpCo).</p>
          </section>

          <section>
            <h2 className="text-lg font-bold text-gray-900 mb-3">2. Plans et tarifs</h2>
            <div className="space-y-4">
              <div className="border border-gray-200 rounded-xl p-4">
                <p className="font-semibold text-gray-900 mb-1">Plan Starter — 0 €</p>
                <p className="text-gray-600">1 audit unique (non récurrent), limité à 3 pages scannées. Rapport PDF GreenAudit sans white-label. Aucun engagement.</p>
              </div>
              <div className="border border-[#1a5c3a] rounded-xl p-4">
                <p className="font-semibold text-gray-900 mb-1">Plan Pro — 2 990 € HT/mois</p>
                <p className="text-gray-600">15 audits complets par mois, pages illimitées, rapport PDF complet en marque blanche, rewrite engine, dossier de preuves, monitoring continu, jusqu'à 10 utilisateurs. Engagement 12 mois ferme. Facturation mensuelle. Audits supplémentaires : 400 € HT/audit.</p>
              </div>
              <div className="border border-gray-200 rounded-xl p-4">
                <p className="font-semibold text-gray-900 mb-1">Plan Enterprise — Sur devis (à partir de 50 000 € HT/an)</p>
                <p className="text-gray-600">Audits et utilisateurs illimités, branding full custom, support premium, facturation sur mesure. Engagement 12 mois ferme. Soumis à un contrat spécifique.</p>
              </div>
            </div>
            <p className="mt-3 text-gray-500">Tous les prix s'entendent hors taxes. La TVA applicable est celle en vigueur au jour de la facturation.</p>
          </section>

          <section>
            <h2 className="text-lg font-bold text-gray-900 mb-3">3. Souscription et activation</h2>
            <p>La souscription au plan Pro s'effectue en ligne via la plateforme Stripe. L'abonnement est activé dès réception du paiement. Le Partenaire reçoit un accès immédiat à l'ensemble des fonctionnalités Pro.</p>
            <p className="mt-2">Pour le plan Enterprise, la souscription fait l'objet d'un devis et d'un contrat spécifique signé entre les parties.</p>
          </section>

          <section>
            <h2 className="text-lg font-bold text-gray-900 mb-3">4. Engagement et résiliation</h2>
            <p>Les plans payants font l'objet d'un <strong>engagement ferme de 12 mois</strong>. Le Partenaire s'engage à régler l'intégralité des mensualités correspondant à la durée d'engagement, même en cas de résiliation anticipée.</p>
            <p className="mt-2">À l'issue de la période d'engagement, l'abonnement se renouvelle tacitement par période d'un mois, résiliable à tout moment avec un préavis de 30 jours via le portail de gestion Stripe ou par email à contact@green-audit.fr.</p>
            <p className="mt-2">Aucun remboursement ne sera effectué pour les périodes déjà facturées.</p>
          </section>

          <section>
            <h2 className="text-lg font-bold text-gray-900 mb-3">5. Audits supplémentaires</h2>
            <p>Au-delà du quota mensuel inclus dans le plan Pro (15 audits/mois), chaque audit supplémentaire est facturé <strong>400 € HT</strong> et prélevé automatiquement via le système de facturation Stripe. Le Partenaire est informé du dépassement de quota dans son tableau de bord.</p>
          </section>

          <section>
            <h2 className="text-lg font-bold text-gray-900 mb-3">6. Modèle de revente (B2B2B)</h2>
            <p>GreenAudit est une plateforme white-label destinée à la revente. Le Partenaire est seul responsable de ses relations commerciales avec ses propres clients (entreprises auditées). GreenAudit n'est pas partie aux contrats conclus entre le Partenaire et ses clients.</p>
            <p className="mt-2">Le Partenaire s'engage à utiliser la plateforme dans le respect des lois applicables, notamment la Directive (UE) 2024/825, et à ne pas présenter les rapports GreenAudit comme un avis juridique.</p>
          </section>

          <section>
            <h2 className="text-lg font-bold text-gray-900 mb-3">7. Disponibilité du service</h2>
            <p>GreenAudit s'engage à maintenir la plateforme disponible 24h/24, 7j/7, hors maintenance planifiée. En cas d'indisponibilité supérieure à 24h consécutives imputable à GreenAudit, un avoir proportionnel sera appliqué sur la facturation du mois concerné.</p>
          </section>

          <section>
            <h2 className="text-lg font-bold text-gray-900 mb-3">8. Données et confidentialité</h2>
            <p>GreenAudit s'engage à ne pas divulguer les données des clients du Partenaire à des tiers. Les données des entreprises auditées sont traitées dans le strict cadre de la prestation et supprimées à l'issue de la génération du rapport, conformément au RGPD.</p>
            <p className="mt-2">GreenAudit agit en qualité de sous-traitant au sens de l'article 28 du RGPD pour le traitement des données confiées par le Partenaire.</p>
          </section>

          <section>
            <h2 className="text-lg font-bold text-gray-900 mb-3">9. Limitation de responsabilité</h2>
            <p>La responsabilité de GreenAudit ne pourra être engagée qu'en cas de faute prouvée. En tout état de cause, la responsabilité de GreenAudit est limitée au montant des sommes effectivement perçues au titre des 3 derniers mois d'abonnement.</p>
            <p className="mt-2">GreenAudit ne saurait être tenu responsable des décisions prises par le Partenaire ou ses clients sur la base des rapports générés.</p>
          </section>

          <section>
            <h2 className="text-lg font-bold text-gray-900 mb-3">10. Droit applicable et litiges</h2>
            <p>Les présentes CGV sont soumises au droit français. En cas de litige, les parties s'engagent à rechercher une solution amiable avant tout recours judiciaire. À défaut, le litige sera soumis aux tribunaux compétents du ressort du siège social de GreenAudit.</p>
          </section>

          <section>
            <h2 className="text-lg font-bold text-gray-900 mb-3">11. Contact</h2>
            <p>Pour toute question relative aux présentes CGV : <strong>contact@green-audit.fr</strong></p>
          </section>

        </div>
      </div>

      <footer className="border-t border-gray-100 py-8 mt-16">
        <div className="max-w-3xl mx-auto px-6 flex flex-col sm:flex-row justify-between gap-4 text-xs text-gray-400">
          <span>© 2026 GreenAudit — Conformité directive EmpCo (EU 2024/825)</span>
          <div className="flex gap-4">
            <button onClick={() => navigate('/mentions-legales')} className="hover:text-gray-700 transition-colors">Mentions légales</button>
            <button onClick={() => navigate('/cgv')} className="hover:text-gray-700 transition-colors">CGV</button>
            <button onClick={() => navigate('/politique-de-confidentialite')} className="hover:text-gray-700 transition-colors">Confidentialité</button>
            <button onClick={() => navigate('/dpa')} className="hover:text-gray-700 transition-colors">DPA</button>
          </div>
        </div>
      </footer>
    </div>
  );
}
