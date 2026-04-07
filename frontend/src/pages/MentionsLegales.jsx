import { useNavigate } from 'react-router-dom';

export default function MentionsLegales() {
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
        <h1 className="text-3xl font-black text-gray-900 mb-2">Mentions légales</h1>
        <p className="text-sm text-gray-400 mb-12">Dernière mise à jour : avril 2026</p>

        <div className="space-y-10 text-sm text-gray-700 leading-relaxed">

          <section>
            <h2 className="text-lg font-bold text-gray-900 mb-3">1. Éditeur du site</h2>
            <p>Le site <strong>green-audit.fr</strong> est édité par :</p>
            <ul className="mt-3 space-y-1 text-gray-600">
              <li><strong>Raison sociale :</strong> Optimaflow</li>
              <li><strong>Forme juridique :</strong> Micro-entreprise</li>
              <li><strong>SIRET :</strong> 879 375 368 00039</li>
              <li><strong>Adresse du siège social :</strong> 6 rue d'Armaillé, 75017 Paris, France</li>
              <li><strong>Directeur de la publication :</strong> Anthony Edmond</li>
              <li><strong>Email :</strong> contact@green-audit.fr</li>
            </ul>
          </section>

          <section>
            <h2 className="text-lg font-bold text-gray-900 mb-3">2. Hébergement</h2>
            <ul className="space-y-1 text-gray-600">
              <li><strong>Backend :</strong> Railway Inc. — 340 S Lemon Ave #4133, Walnut, CA 91789, États-Unis</li>
              <li><strong>Frontend :</strong> Vercel Inc. — 440 N Barranca Ave #4133, Covina, CA 91723, États-Unis</li>
            </ul>
          </section>

          <section>
            <h2 className="text-lg font-bold text-gray-900 mb-3">3. Propriété intellectuelle</h2>
            <p>L'ensemble des contenus présents sur le site green-audit.fr (textes, graphismes, logo, base de données, logiciel d'analyse) sont la propriété exclusive de GreenAudit et sont protégés par les lois françaises et internationales relatives à la propriété intellectuelle.</p>
            <p className="mt-2">Toute reproduction, représentation, modification ou exploitation totale ou partielle des contenus est strictement interdite sans autorisation préalable écrite.</p>
          </section>

          <section>
            <h2 className="text-lg font-bold text-gray-900 mb-3">4. Données personnelles</h2>
            <p>GreenAudit collecte et traite des données personnelles dans le cadre de la fourniture de ses services. Conformément au Règlement Général sur la Protection des Données (RGPD — UE 2016/679), vous disposez d'un droit d'accès, de rectification, de suppression et de portabilité de vos données.</p>
            <p className="mt-2">Pour exercer ces droits ou pour toute question relative à vos données : <strong>contact@green-audit.fr</strong></p>
            <p className="mt-2">Les données des entreprises auditées ne sont pas conservées au-delà de la durée nécessaire à la génération du rapport.</p>
          </section>

          <section>
            <h2 className="text-lg font-bold text-gray-900 mb-3">5. Cookies</h2>
            <p>Le site green-audit.fr utilise uniquement des cookies strictement nécessaires au fonctionnement du service (authentification via JWT). Aucun cookie publicitaire ou de traçage tiers n'est utilisé.</p>
          </section>

          <section>
            <h2 className="text-lg font-bold text-gray-900 mb-3">6. Limitation de responsabilité</h2>
            <p>Les rapports générés par GreenAudit constituent un outil d'aide à la conformité. Ils ne constituent pas un avis juridique et ne sauraient engager la responsabilité de GreenAudit en cas de décision prise sur leur seule base. L'interprétation définitive des textes réglementaires relève de l'autorité judiciaire compétente.</p>
          </section>

          <section>
            <h2 className="text-lg font-bold text-gray-900 mb-3">7. Droit applicable</h2>
            <p>Les présentes mentions légales sont régies par le droit français. En cas de litige, et à défaut de résolution amiable, les tribunaux français seront seuls compétents.</p>
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
