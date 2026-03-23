import { useState, useEffect } from 'react';
import { useAuth } from '../api/auth';
import api from '../api/client';

const inputCls = 'w-full rounded-lg border border-gray-200 px-4 py-3 text-sm text-gray-900 placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-[#1a5c3a] focus:border-transparent transition bg-white';

function MessageBanner({ message }) {
  if (!message) return null;
  const ok = message.type === 'success';
  return (
    <div className={`rounded-xl px-4 py-3 text-sm mb-4 flex items-center gap-2 ${ok ? 'bg-[#eaf4ee] border border-[#1a5c3a]/20 text-[#1a5c3a]' : 'bg-red-50 border border-red-100 text-red-700'}`}>
      {ok
        ? <svg className="w-4 h-4 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" /></svg>
        : <svg className="w-4 h-4 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>
      }
      {message.text}
    </div>
  );
}

export default function Settings() {
  const { partner } = useAuth();

  const [companyName, setCompanyName] = useState('');
  const [contactName, setContactName] = useState('');
  const [contactPhone, setContactPhone] = useState('');
  const [profileSaving, setProfileSaving] = useState(false);
  const [profileMessage, setProfileMessage] = useState(null);

  const [logoUrl, setLogoUrl] = useState('');
  const [primaryColor, setPrimaryColor] = useState('#1a5c3a');
  const [secondaryColor, setSecondaryColor] = useState('#2E7D32');
  const [brandingSaving, setBrandingSaving] = useState(false);
  const [brandingMessage, setBrandingMessage] = useState(null);

  useEffect(() => {
    if (partner) {
      setCompanyName(partner.company_name || '');
      setContactName(partner.contact_name || '');
      setContactPhone(partner.contact_phone || '');
      setLogoUrl(partner.logo_url || '');
      setPrimaryColor(partner.brand_primary_color || '#1a5c3a');
      setSecondaryColor(partner.brand_secondary_color || '#2E7D32');
    }
  }, [partner]);

  useEffect(() => {
    if (profileMessage) { const t = setTimeout(() => setProfileMessage(null), 4000); return () => clearTimeout(t); }
  }, [profileMessage]);

  useEffect(() => {
    if (brandingMessage) { const t = setTimeout(() => setBrandingMessage(null), 4000); return () => clearTimeout(t); }
  }, [brandingMessage]);

  const handleProfileSave = async (e) => {
    e.preventDefault();
    setProfileSaving(true);
    setProfileMessage(null);
    try {
      await api.put('/partners/me', { company_name: companyName, contact_name: contactName || null, contact_phone: contactPhone || null });
      setProfileMessage({ type: 'success', text: 'Profil mis à jour avec succès.' });
    } catch (err) {
      const detail = err.response?.data?.detail;
      setProfileMessage({ type: 'error', text: typeof detail === 'string' ? detail : 'Erreur lors de la mise à jour.' });
    } finally {
      setProfileSaving(false);
    }
  };

  const handleBrandingSave = async (e) => {
    e.preventDefault();
    setBrandingSaving(true);
    setBrandingMessage(null);
    try {
      await api.put('/partners/me/branding', { logo_url: logoUrl || null, brand_primary_color: primaryColor, brand_secondary_color: secondaryColor });
      setBrandingMessage({ type: 'success', text: 'Branding mis à jour avec succès.' });
    } catch (err) {
      const detail = err.response?.data?.detail;
      setBrandingMessage({ type: 'error', text: typeof detail === 'string' ? detail : 'Erreur lors de la mise à jour.' });
    } finally {
      setBrandingSaving(false);
    }
  };

  return (
    <div className="max-w-2xl mx-auto space-y-6">
      <div className="mb-8">
        <p className="text-xs font-semibold uppercase tracking-widest text-[#1a5c3a] mb-1">Compte</p>
        <h1 className="text-2xl font-black text-gray-900">Paramètres</h1>
        <p className="mt-1 text-sm text-gray-500">Gérez votre profil et votre branding white-label.</p>
      </div>

      {/* Section Profil */}
      <div className="bg-white rounded-2xl border border-gray-100 overflow-hidden">
        <div className="px-6 py-4 border-b border-gray-50 bg-[#eaf4ee]">
          <h2 className="text-sm font-bold text-[#1a5c3a]">Profil partenaire</h2>
          <p className="text-xs text-gray-500 mt-0.5">Informations de votre entreprise et contact principal.</p>
        </div>
        <form onSubmit={handleProfileSave} className="p-6 space-y-4">
          <MessageBanner message={profileMessage} />
          <div>
            <label htmlFor="companyName" className="block text-sm font-medium text-gray-700 mb-1.5">
              Nom de l'entreprise <span className="text-red-500">*</span>
            </label>
            <input id="companyName" type="text" required value={companyName}
              onChange={(e) => setCompanyName(e.target.value)} placeholder="Votre entreprise" className={inputCls} />
          </div>
          <div>
            <label htmlFor="contactName" className="block text-sm font-medium text-gray-700 mb-1.5">Nom du contact</label>
            <input id="contactName" type="text" value={contactName}
              onChange={(e) => setContactName(e.target.value)} placeholder="Prénom Nom" className={inputCls} />
          </div>
          <div>
            <label htmlFor="contactPhone" className="block text-sm font-medium text-gray-700 mb-1.5">Téléphone</label>
            <input id="contactPhone" type="tel" value={contactPhone}
              onChange={(e) => setContactPhone(e.target.value)} placeholder="+33 6 12 34 56 78" className={inputCls} />
          </div>
          <div className="pt-2">
            <button type="submit" disabled={profileSaving}
              className="px-5 py-2.5 rounded-full text-sm font-semibold text-white bg-[#1a5c3a] hover:bg-[#14472d] transition-colors disabled:opacity-50">
              {profileSaving ? 'Enregistrement...' : 'Enregistrer →'}
            </button>
          </div>
        </form>
      </div>

      {/* Section Branding */}
      <div className="bg-white rounded-2xl border border-gray-100 overflow-hidden">
        <div className="px-6 py-4 border-b border-gray-50 bg-[#eaf4ee]">
          <h2 className="text-sm font-bold text-[#1a5c3a]">Branding white-label</h2>
          <p className="text-xs text-gray-500 mt-0.5">Personnalisez l'apparence de vos rapports d'audit.</p>
        </div>
        <form onSubmit={handleBrandingSave} className="p-6 space-y-5">
          <MessageBanner message={brandingMessage} />

          {/* Logo */}
          <div>
            <label htmlFor="logoUrl" className="block text-sm font-medium text-gray-700 mb-1.5">URL du logo</label>
            <input id="logoUrl" type="url" value={logoUrl}
              onChange={(e) => setLogoUrl(e.target.value)}
              placeholder="https://example.com/logo.png" className={inputCls} />
            {logoUrl && (
              <div className="mt-3 p-3 bg-gray-50 rounded-xl border border-gray-100 inline-block">
                <p className="text-xs text-gray-400 mb-2">Aperçu :</p>
                <img src={logoUrl} alt="Logo preview" className="max-h-16 max-w-48 object-contain"
                  onError={(e) => { e.target.style.display = 'none'; }} />
              </div>
            )}
          </div>

          {/* Couleurs */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-5">
            {[
              { id: 'primaryColor', label: 'Couleur primaire', value: primaryColor, setter: setPrimaryColor },
              { id: 'secondaryColor', label: 'Couleur secondaire', value: secondaryColor, setter: setSecondaryColor },
            ].map(({ id, label, value, setter }) => (
              <div key={id}>
                <label htmlFor={id} className="block text-sm font-medium text-gray-700 mb-1.5">{label}</label>
                <div className="flex items-center gap-3">
                  <input id={id} type="color" value={value} onChange={(e) => setter(e.target.value)}
                    className="w-12 h-10 rounded-lg border border-gray-200 cursor-pointer p-0.5" />
                  <input type="text" value={value}
                    onChange={(e) => { if (/^#[0-9A-Fa-f]{0,6}$/.test(e.target.value)) setter(e.target.value); }}
                    maxLength={7}
                    className="flex-1 rounded-lg border border-gray-200 px-3 py-2.5 text-sm font-mono focus:outline-none focus:ring-2 focus:ring-[#1a5c3a] focus:border-transparent transition" />
                </div>
              </div>
            ))}
          </div>

          {/* Aperçu */}
          <div className="rounded-xl border border-gray-100 overflow-hidden">
            <div className="px-4 py-2.5 text-sm font-semibold text-white" style={{ backgroundColor: primaryColor }}>
              Aperçu des couleurs
            </div>
            <div className="p-4 bg-white">
              <div className="flex items-center gap-3 mb-3">
                {logoUrl && (
                  <img src={logoUrl} alt="Logo" className="h-8 object-contain"
                    onError={(e) => { e.target.style.display = 'none'; }} />
                )}
                <span className="text-sm font-bold" style={{ color: primaryColor }}>
                  {companyName || 'Votre entreprise'}
                </span>
              </div>
              <div className="h-2 rounded-full mb-2" style={{ backgroundColor: primaryColor, width: '75%' }} />
              <div className="h-2 rounded-full" style={{ backgroundColor: secondaryColor, width: '50%' }} />
              <p className="text-xs text-gray-400 mt-3">Aperçu de vos couleurs dans les rapports PDF.</p>
            </div>
          </div>

          <div className="pt-2">
            <button type="submit" disabled={brandingSaving}
              className="px-5 py-2.5 rounded-full text-sm font-semibold text-white bg-[#1a5c3a] hover:bg-[#14472d] transition-colors disabled:opacity-50">
              {brandingSaving ? 'Enregistrement...' : 'Enregistrer le branding →'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
