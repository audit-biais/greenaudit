import { useNavigate } from 'react-router-dom';

export default function DPA() {
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
        <h1 className="text-3xl font-black text-gray-900 mb-2">Accord de traitement des données</h1>
        <p className="text-sm text-gray-500 mb-1">Data Processing Agreement (DPA) — Article 28 RGPD</p>
        <p className="text-sm text-gray-400 mb-12">Version en vigueur : avril 2026</p>

        <div className="mb-8 p-4 bg-[#eaf4ee] border border-[#1a5c3a]/20 rounded-xl text-sm text-[#1a5c3a]">
          <p>Le présent DPA est automatiquement accepté lors de la souscription à la plateforme GreenAudit. Il constitue l'accord de sous-traitance au sens de l'article 28 du RGPD entre le Partenaire (responsable du traitement) et GreenAudit (sous-traitant).</p>
        </div>

        <div className="space-y-10 text-sm text-gray-700 leading-relaxed">

          <section>
            <h2 className="text-lg font-bold text-gray-900 mb-3">1. Parties</h2>
            <div className="space-y-4">
              <div className="border border-gray-200 rounded-xl p-4">
                <p className="font-semibold text-gray-900 mb-2">Sous-traitant (GreenAudit)</p>
                <ul className="space-y-1 text-gray-600">
                  <li><strong>Raison sociale :</strong> Optimaflow</li>
                  <li><strong>Forme juridique :</strong> Micro-entreprise</li>
                  <li><strong>SIRET :</strong> 879 375 368 00039</li>
                  <li><strong>Adresse :</strong> 6 rue d'Armaillé, 75017 Paris, France</li>
                  <li><strong>Contact :</strong> contact@green-audit.fr</li>
                </ul>
              </div>
              <div className="border border-gray-200 rounded-xl p-4">
                <p className="font-semibold text-gray-900 mb-2">Responsable du traitement (le Partenaire)</p>
                <p className="text-gray-600">Toute personne morale ou physique souscrivant à la plateforme GreenAudit via green-audit.fr et agissant en qualité de responsable du traitement vis-à-vis de ses propres clients.</p>
              </div>
            </div>
          </section>

          <section>
            <h2 className="text-lg font-bold text-gray-900 mb-3">2. Objet et nature du traitement</h2>
            <p>GreenAudit traite, pour le compte du Partenaire, les données nécessaires à la fourniture du service d'audit automatisé de conformité anti-greenwashing, à savoir :</p>
            <ul className="mt-3 space-y-1.5 text-gray-600 list-disc list-inside ml-2">
              <li>Les allégations environnementales saisies dans la plateforme aux fins d'analyse</li>
              <li>Les données d'identification des entreprises auditées (nom, secteur, URL)</li>
              <li>Les éléments de preuve et métadonnées associées aux allégations</li>
              <li>Les données de contact du partenaire nécessaires à la génération des rapports</li>
            </ul>
          </section>

          <section>
            <h2 className="text-lg font-bold text-gray-900 mb-3">3. Finalité du traitement</h2>
            <p>Les données sont traitées exclusivement aux fins suivantes :</p>
            <ul className="mt-3 space-y-1.5 text-gray-600 list-disc list-inside ml-2">
              <li>Analyse des allégations environnementales selon les règles de la Directive EmpCo (UE 2024/825)</li>
              <li>Génération automatique du rapport d'audit PDF</li>
              <li>Stockage des audits et rapports dans l'espace du Partenaire</li>
              <li>Fourniture des fonctionnalités de monitoring et d'Evidence Vault</li>
            </ul>
            <p className="mt-3">GreenAudit s'interdit formellement d'utiliser les données à des fins autres que celles listées ci-dessus, notamment à des fins commerciales, de profilage ou d'entraînement de modèles d'IA.</p>
          </section>

          <section>
            <h2 className="text-lg font-bold text-gray-900 mb-3">4. Durée du traitement</h2>
            <p>Le traitement des données est effectué pendant la durée de l'abonnement du Partenaire. Les données des entreprises auditées sont supprimées dès génération du rapport. Les données du compte Partenaire sont conservées 3 ans après résiliation de l'abonnement, puis supprimées (sauf obligation légale de conservation).</p>
          </section>

          <section>
            <h2 className="text-lg font-bold text-gray-900 mb-3">5. Obligations de GreenAudit (sous-traitant)</h2>
            <p>Conformément à l'article 28 RGPD, GreenAudit s'engage à :</p>
            <ul className="mt-3 space-y-2 text-gray-600">
              <li className="flex gap-2">
                <span className="text-[#1a5c3a] font-bold flex-shrink-0">a)</span>
                <span>Ne traiter les données que sur instruction documentée du Partenaire, sauf obligation légale contraire</span>
              </li>
              <li className="flex gap-2">
                <span className="text-[#1a5c3a] font-bold flex-shrink-0">b)</span>
                <span>Garantir la confidentialité des données (engagement de confidentialité des personnes autorisées à traiter les données)</span>
              </li>
              <li className="flex gap-2">
                <span className="text-[#1a5c3a] font-bold flex-shrink-0">c)</span>
                <span>Mettre en œuvre les mesures de sécurité appropriées (Art. 32 RGPD) : chiffrement HTTPS/TLS, hashage des mots de passe, isolation des données par tenant</span>
              </li>
              <li className="flex gap-2">
                <span className="text-[#1a5c3a] font-bold flex-shrink-0">d)</span>
                <span>Respecter les conditions de recours à un sous-traitant ultérieur (Art. 28§4 RGPD)</span>
              </li>
              <li className="flex gap-2">
                <span className="text-[#1a5c3a] font-bold flex-shrink-0">e)</span>
                <span>Aider le Partenaire à garantir le respect des droits des personnes concernées (accès, rectification, effacement, portabilité)</span>
              </li>
              <li className="flex gap-2">
                <span className="text-[#1a5c3a] font-bold flex-shrink-0">f)</span>
                <span>Notifier tout violation de données dans un délai de 72h au Partenaire, conformément à l'Art. 33 RGPD</span>
              </li>
              <li className="flex gap-2">
                <span className="text-[#1a5c3a] font-bold flex-shrink-0">g)</span>
                <span>Supprimer ou restituer toutes les données au terme du service selon le choix du Partenaire</span>
              </li>
              <li className="flex gap-2">
                <span className="text-[#1a5c3a] font-bold flex-shrink-0">h)</span>
                <span>Mettre à disposition toute information nécessaire pour démontrer le respect des obligations du présent accord</span>
              </li>
            </ul>
          </section>

          <section>
            <h2 className="text-lg font-bold text-gray-900 mb-3">6. Obligations du Partenaire (responsable du traitement)</h2>
            <p>Le Partenaire s'engage à :</p>
            <ul className="mt-3 space-y-1.5 text-gray-600 list-disc list-inside ml-2">
              <li>Fournir à GreenAudit uniquement les données nécessaires aux finalités définies</li>
              <li>S'assurer que les entreprises auditées ont été informées du traitement de leurs données</li>
              <li>Ne pas confier à GreenAudit de données à caractère personnel sensibles au sens de l'Art. 9 RGPD sans accord préalable</li>
              <li>Respecter ses propres obligations de responsable du traitement vis-à-vis de ses clients</li>
            </ul>
          </section>

          <section>
            <h2 className="text-lg font-bold text-gray-900 mb-3">7. Sous-traitants ultérieurs</h2>
            <p>Le Partenaire autorise GreenAudit à faire appel aux sous-traitants ultérieurs suivants :</p>
            <div className="mt-3 overflow-x-auto">
              <table className="w-full text-xs border-collapse">
                <thead>
                  <tr className="bg-gray-50">
                    <th className="text-left p-3 border border-gray-200 font-semibold text-gray-700">Sous-traitant</th>
                    <th className="text-left p-3 border border-gray-200 font-semibold text-gray-700">Pays</th>
                    <th className="text-left p-3 border border-gray-200 font-semibold text-gray-700">Rôle</th>
                    <th className="text-left p-3 border border-gray-200 font-semibold text-gray-700">Garanties</th>
                  </tr>
                </thead>
                <tbody>
                  <tr>
                    <td className="p-3 border border-gray-200">Railway Inc.</td>
                    <td className="p-3 border border-gray-200">États-Unis</td>
                    <td className="p-3 border border-gray-200">Hébergement backend & base de données</td>
                    <td className="p-3 border border-gray-200">CCT (clauses contractuelles types UE)</td>
                  </tr>
                  <tr>
                    <td className="p-3 border border-gray-200">Vercel Inc.</td>
                    <td className="p-3 border border-gray-200">États-Unis</td>
                    <td className="p-3 border border-gray-200">Hébergement frontend</td>
                    <td className="p-3 border border-gray-200">CCT (clauses contractuelles types UE)</td>
                  </tr>
                  <tr>
                    <td className="p-3 border border-gray-200">Stripe Inc.</td>
                    <td className="p-3 border border-gray-200">États-Unis</td>
                    <td className="p-3 border border-gray-200">Paiement (données de facturation uniquement)</td>
                    <td className="p-3 border border-gray-200">CCT + certifié PCI-DSS</td>
                  </tr>
                </tbody>
              </table>
            </div>
            <p className="mt-3 text-gray-500">GreenAudit informera le Partenaire de tout ajout ou remplacement d'un sous-traitant ultérieur, lui donnant la possibilité de s'y opposer.</p>
          </section>

          <section>
            <h2 className="text-lg font-bold text-gray-900 mb-3">8. Transferts hors UE</h2>
            <p>Les transferts de données vers les États-Unis (Railway, Vercel, Stripe) sont encadrés par des clauses contractuelles types (CCT) adoptées par la Commission européenne, conformément à l'article 46 du RGPD.</p>
          </section>

          <section>
            <h2 className="text-lg font-bold text-gray-900 mb-3">9. Sécurité des données</h2>
            <p>GreenAudit met en œuvre les mesures suivantes :</p>
            <ul className="mt-3 space-y-1.5 text-gray-600 list-disc list-inside ml-2">
              <li>Chiffrement des communications (TLS/HTTPS)</li>
              <li>Hashage des mots de passe (bcrypt)</li>
              <li>Isolation des données par organisation (multi-tenant)</li>
              <li>Accès aux données de production restreint aux personnes habilitées</li>
              <li>Journalisation des accès et des opérations sensibles</li>
            </ul>
          </section>

          <section>
            <h2 className="text-lg font-bold text-gray-900 mb-3">10. Droit applicable et litiges</h2>
            <p>Le présent DPA est soumis au droit français et au RGPD (UE 2016/679). Tout litige relatif à son interprétation ou son exécution sera soumis aux juridictions compétentes du ressort du siège social de GreenAudit (Paris, France).</p>
          </section>

          <section>
            <h2 className="text-lg font-bold text-gray-900 mb-3">11. Contact</h2>
            <p>Pour toute question relative au présent DPA ou pour exercer vos droits : <strong>contact@green-audit.fr</strong></p>
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
