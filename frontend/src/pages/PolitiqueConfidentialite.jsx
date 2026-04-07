import { useNavigate } from 'react-router-dom';

export default function PolitiqueConfidentialite() {
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
        <h1 className="text-3xl font-black text-gray-900 mb-2">Politique de confidentialité</h1>
        <p className="text-sm text-gray-400 mb-12">Dernière mise à jour : avril 2026</p>

        <div className="space-y-10 text-sm text-gray-700 leading-relaxed">

          <section>
            <h2 className="text-lg font-bold text-gray-900 mb-3">1. Responsable du traitement</h2>
            <p>Le responsable du traitement des données personnelles collectées via la plateforme green-audit.fr est :</p>
            <ul className="mt-3 space-y-1 text-gray-600">
              <li><strong>Raison sociale :</strong> Optimaflow (GreenAudit)</li>
              <li><strong>Forme juridique :</strong> Micro-entreprise</li>
              <li><strong>SIRET :</strong> 879 375 368 00039</li>
              <li><strong>Adresse :</strong> 6 rue d'Armaillé, 75017 Paris, France</li>
              <li><strong>Contact DPO :</strong> contact@green-audit.fr</li>
            </ul>
          </section>

          <section>
            <h2 className="text-lg font-bold text-gray-900 mb-3">2. Données collectées</h2>
            <div className="space-y-4">
              <div>
                <p className="font-semibold text-gray-900 mb-1">2.1 Données des partenaires (utilisateurs de la plateforme)</p>
                <ul className="list-disc list-inside space-y-1 text-gray-600 ml-2">
                  <li>Email et mot de passe (hashé, jamais stocké en clair)</li>
                  <li>Nom de l'entreprise, nom du contact, téléphone</li>
                  <li>Logo et couleurs de marque (branding white-label)</li>
                  <li>Données de facturation via Stripe (traitées directement par Stripe)</li>
                </ul>
              </div>
              <div>
                <p className="font-semibold text-gray-900 mb-1">2.2 Données des entreprises auditées</p>
                <p className="text-gray-600">Les allégations environnementales saisies dans la plateforme aux fins d'audit sont traitées uniquement le temps nécessaire à la génération du rapport. Elles ne sont pas conservées au-delà et ne sont pas utilisées à d'autres fins.</p>
              </div>
            </div>
          </section>

          <section>
            <h2 className="text-lg font-bold text-gray-900 mb-3">3. Finalités et bases légales</h2>
            <div className="overflow-x-auto">
              <table className="w-full text-xs border-collapse">
                <thead>
                  <tr className="bg-gray-50">
                    <th className="text-left p-3 border border-gray-200 font-semibold text-gray-700">Finalité</th>
                    <th className="text-left p-3 border border-gray-200 font-semibold text-gray-700">Base légale</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-100">
                  <tr>
                    <td className="p-3 border border-gray-200">Création et gestion du compte partenaire</td>
                    <td className="p-3 border border-gray-200">Exécution du contrat (Art. 6.1.b RGPD)</td>
                  </tr>
                  <tr>
                    <td className="p-3 border border-gray-200">Fourniture du service d'audit</td>
                    <td className="p-3 border border-gray-200">Exécution du contrat (Art. 6.1.b RGPD)</td>
                  </tr>
                  <tr>
                    <td className="p-3 border border-gray-200">Facturation et gestion des abonnements</td>
                    <td className="p-3 border border-gray-200">Obligation légale + exécution du contrat</td>
                  </tr>
                  <tr>
                    <td className="p-3 border border-gray-200">Communications relatives au service</td>
                    <td className="p-3 border border-gray-200">Intérêt légitime (Art. 6.1.f RGPD)</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </section>

          <section>
            <h2 className="text-lg font-bold text-gray-900 mb-3">4. Durées de conservation</h2>
            <ul className="space-y-2 text-gray-600">
              <li><strong>Données du compte partenaire :</strong> Durée de l'abonnement + 3 ans après résiliation (obligations comptables)</li>
              <li><strong>Données des entreprises auditées :</strong> Supprimées immédiatement après génération du rapport PDF</li>
              <li><strong>Données de facturation :</strong> 10 ans (obligation légale française)</li>
              <li><strong>Logs techniques :</strong> 12 mois maximum</li>
            </ul>
          </section>

          <section>
            <h2 className="text-lg font-bold text-gray-900 mb-3">5. Destinataires des données</h2>
            <p>Vos données peuvent être transmises aux sous-traitants suivants, dans le strict cadre de la prestation :</p>
            <ul className="mt-3 space-y-2 text-gray-600">
              <li><strong>Railway Inc.</strong> (hébergement backend) — 340 S Lemon Ave #4133, Walnut, CA 91789, USA</li>
              <li><strong>Vercel Inc.</strong> (hébergement frontend) — 440 N Barranca Ave #4133, Covina, CA 91723, USA</li>
              <li><strong>Stripe Inc.</strong> (paiement) — 510 Townsend Street, San Francisco, CA 94103, USA</li>
            </ul>
            <p className="mt-3">Ces sous-traitants sont soumis à des garanties contractuelles conformes au RGPD (clauses contractuelles types ou équivalences adéquates). Aucune donnée n'est vendue à des tiers.</p>
          </section>

          <section>
            <h2 className="text-lg font-bold text-gray-900 mb-3">6. Cookies</h2>
            <p>La plateforme green-audit.fr utilise uniquement des cookies strictement nécessaires au fonctionnement du service (jeton d'authentification JWT stocké en mémoire du navigateur). Aucun cookie publicitaire, de tracking ou de profilage n'est utilisé. Aucun bandeau de consentement n'est donc requis.</p>
          </section>

          <section>
            <h2 className="text-lg font-bold text-gray-900 mb-3">7. Vos droits</h2>
            <p>Conformément au RGPD (UE 2016/679) et à la loi Informatique et Libertés, vous disposez des droits suivants :</p>
            <ul className="mt-3 space-y-1.5 text-gray-600 list-disc list-inside ml-2">
              <li><strong>Droit d'accès</strong> (Art. 15) : obtenir une copie de vos données</li>
              <li><strong>Droit de rectification</strong> (Art. 16) : corriger des données inexactes</li>
              <li><strong>Droit à l'effacement</strong> (Art. 17) : demander la suppression de votre compte et de vos données</li>
              <li><strong>Droit à la portabilité</strong> (Art. 20) : recevoir vos données dans un format structuré</li>
              <li><strong>Droit d'opposition</strong> (Art. 21) : vous opposer à certains traitements</li>
              <li><strong>Droit à la limitation</strong> (Art. 18) : limiter le traitement de vos données</li>
            </ul>
            <p className="mt-4">Pour exercer ces droits : <strong>contact@green-audit.fr</strong></p>
            <p className="mt-2">Vous disposez également du droit de déposer une réclamation auprès de la <strong>CNIL</strong> (Commission Nationale de l'Informatique et des Libertés) — cnil.fr</p>
          </section>

          <section>
            <h2 className="text-lg font-bold text-gray-900 mb-3">8. Sécurité</h2>
            <p>GreenAudit met en œuvre les mesures techniques et organisationnelles appropriées pour protéger vos données : chiffrement HTTPS, mots de passe hashés (bcrypt), accès aux données restreint aux personnes habilitées, isolation multi-tenant des données partenaires.</p>
          </section>

          <section>
            <h2 className="text-lg font-bold text-gray-900 mb-3">9. Transferts hors UE</h2>
            <p>Certains sous-traitants (Railway, Vercel, Stripe) sont établis aux États-Unis. Ces transferts sont encadrés par des clauses contractuelles types approuvées par la Commission européenne, conformément à l'Art. 46 du RGPD.</p>
          </section>

          <section>
            <h2 className="text-lg font-bold text-gray-900 mb-3">10. Modifications</h2>
            <p>La présente politique peut être mise à jour. En cas de modification substantielle, les partenaires en seront informés par email. La version en vigueur est celle publiée sur cette page.</p>
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
