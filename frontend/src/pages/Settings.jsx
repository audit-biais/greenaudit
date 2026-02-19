import { useState, useEffect } from 'react';
import { useAuth } from '../api/auth';
import api from '../api/client';

export default function Settings() {
  const { partner } = useAuth();

  // Profile state
  const [companyName, setCompanyName] = useState('');
  const [contactName, setContactName] = useState('');
  const [contactPhone, setContactPhone] = useState('');
  const [profileSaving, setProfileSaving] = useState(false);

  // Branding state
  const [logoUrl, setLogoUrl] = useState('');
  const [primaryColor, setPrimaryColor] = useState('#1B5E20');
  const [secondaryColor, setSecondaryColor] = useState('#2E7D32');
  const [brandingSaving, setBrandingSaving] = useState(false);

  // Messages
  const [profileMessage, setProfileMessage] = useState(null);
  const [brandingMessage, setBrandingMessage] = useState(null);

  // Populate form from partner data
  useEffect(() => {
    if (partner) {
      setCompanyName(partner.company_name || '');
      setContactName(partner.contact_name || '');
      setContactPhone(partner.contact_phone || '');
      setLogoUrl(partner.logo_url || '');
      setPrimaryColor(partner.brand_primary_color || '#1B5E20');
      setSecondaryColor(partner.brand_secondary_color || '#2E7D32');
    }
  }, [partner]);

  // Auto-dismiss messages after 4 seconds
  useEffect(() => {
    if (profileMessage) {
      const t = setTimeout(() => setProfileMessage(null), 4000);
      return () => clearTimeout(t);
    }
  }, [profileMessage]);

  useEffect(() => {
    if (brandingMessage) {
      const t = setTimeout(() => setBrandingMessage(null), 4000);
      return () => clearTimeout(t);
    }
  }, [brandingMessage]);

  const handleProfileSave = async (e) => {
    e.preventDefault();
    setProfileSaving(true);
    setProfileMessage(null);
    try {
      await api.put('/partners/me', {
        company_name: companyName,
        contact_name: contactName || null,
        contact_phone: contactPhone || null,
      });
      setProfileMessage({ type: 'success', text: 'Profil mis à jour avec succès.' });
    } catch (err) {
      const detail = err.response?.data?.detail;
      setProfileMessage({
        type: 'error',
        text: typeof detail === 'string' ? detail : 'Erreur lors de la mise à jour du profil.',
      });
    } finally {
      setProfileSaving(false);
    }
  };

  const handleBrandingSave = async (e) => {
    e.preventDefault();
    setBrandingSaving(true);
    setBrandingMessage(null);
    try {
      await api.put('/partners/me/branding', {
        logo_url: logoUrl || null,
        brand_primary_color: primaryColor,
        brand_secondary_color: secondaryColor,
      });
      setBrandingMessage({ type: 'success', text: 'Branding mis à jour avec succès.' });
    } catch (err) {
      const detail = err.response?.data?.detail;
      setBrandingMessage({
        type: 'error',
        text: typeof detail === 'string' ? detail : 'Erreur lors de la mise à jour du branding.',
      });
    } finally {
      setBrandingSaving(false);
    }
  };

  const MessageBanner = ({ message }) => {
    if (!message) return null;
    const isSuccess = message.type === 'success';
    return (
      <div
        className={`rounded-lg px-4 py-3 text-sm mb-4 transition-all ${
          isSuccess
            ? 'bg-green-50 border border-green-200 text-green-800'
            : 'bg-red-50 border border-red-200 text-red-700'
        }`}
      >
        <div className="flex items-center gap-2">
          {isSuccess ? (
            <svg className="w-4 h-4 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
            </svg>
          ) : (
            <svg className="w-4 h-4 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          )}
          {message.text}
        </div>
      </div>
    );
  };

  const inputClasses =
    'w-full rounded-lg border border-gray-300 px-4 py-2.5 text-sm text-gray-900 placeholder-gray-400 focus:outline-none focus:ring-2 focus:border-transparent transition';

  const inputFocusHandlers = {
    onFocus: (e) => {
      e.target.style.boxShadow = '0 0 0 2px #2E7D32';
      e.target.style.borderColor = 'transparent';
    },
    onBlur: (e) => {
      e.target.style.boxShadow = 'none';
      e.target.style.borderColor = '#d1d5db';
    },
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="border-b border-gray-200 bg-white">
        <div className="max-w-3xl mx-auto px-4 py-6 sm:px-6">
          <h1 className="text-2xl font-bold text-gray-900">Paramètres</h1>
          <p className="text-sm text-gray-500 mt-1">
            Gérez votre profil et votre branding white-label.
          </p>
        </div>
      </div>

      <div className="max-w-3xl mx-auto px-4 py-8 sm:px-6 space-y-8">
        {/* Section 1: Profile */}
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
          <div className="px-6 py-4 border-b border-gray-100" style={{ backgroundColor: '#f0fdf4' }}>
            <h2 className="text-lg font-semibold" style={{ color: '#1B5E20' }}>
              Profil partenaire
            </h2>
            <p className="text-sm text-gray-500 mt-0.5">
              Informations de votre entreprise et contact principal.
            </p>
          </div>

          <form onSubmit={handleProfileSave} className="p-6 space-y-4">
            <MessageBanner message={profileMessage} />

            {/* Company name */}
            <div>
              <label htmlFor="companyName" className="block text-sm font-medium text-gray-700 mb-1">
                Nom de l'entreprise <span className="text-red-500">*</span>
              </label>
              <input
                id="companyName"
                type="text"
                required
                value={companyName}
                onChange={(e) => setCompanyName(e.target.value)}
                placeholder="Votre entreprise"
                className={inputClasses}
                {...inputFocusHandlers}
              />
            </div>

            {/* Contact name */}
            <div>
              <label htmlFor="contactName" className="block text-sm font-medium text-gray-700 mb-1">
                Nom du contact
              </label>
              <input
                id="contactName"
                type="text"
                value={contactName}
                onChange={(e) => setContactName(e.target.value)}
                placeholder="Prénom Nom"
                className={inputClasses}
                {...inputFocusHandlers}
              />
            </div>

            {/* Contact phone */}
            <div>
              <label htmlFor="contactPhone" className="block text-sm font-medium text-gray-700 mb-1">
                Téléphone
              </label>
              <input
                id="contactPhone"
                type="tel"
                value={contactPhone}
                onChange={(e) => setContactPhone(e.target.value)}
                placeholder="+33 6 12 34 56 78"
                className={inputClasses}
                {...inputFocusHandlers}
              />
            </div>

            {/* Save button */}
            <div className="pt-2">
              <button
                type="submit"
                disabled={profileSaving}
                className="rounded-lg px-5 py-2.5 text-sm font-semibold text-white shadow-sm transition duration-150 ease-in-out disabled:opacity-50 disabled:cursor-not-allowed hover:opacity-90"
                style={{ backgroundColor: '#1B5E20' }}
              >
                {profileSaving ? 'Enregistrement...' : 'Enregistrer le profil'}
              </button>
            </div>
          </form>
        </div>

        {/* Section 2: Branding */}
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
          <div className="px-6 py-4 border-b border-gray-100" style={{ backgroundColor: '#f0fdf4' }}>
            <h2 className="text-lg font-semibold" style={{ color: '#1B5E20' }}>
              Branding white-label
            </h2>
            <p className="text-sm text-gray-500 mt-0.5">
              Personnalisez l'apparence de vos rapports d'audit.
            </p>
          </div>

          <form onSubmit={handleBrandingSave} className="p-6 space-y-5">
            <MessageBanner message={brandingMessage} />

            {/* Logo URL */}
            <div>
              <label htmlFor="logoUrl" className="block text-sm font-medium text-gray-700 mb-1">
                URL du logo
              </label>
              <input
                id="logoUrl"
                type="url"
                value={logoUrl}
                onChange={(e) => setLogoUrl(e.target.value)}
                placeholder="https://example.com/logo.png"
                className={inputClasses}
                {...inputFocusHandlers}
              />
              {logoUrl && (
                <div className="mt-3 p-3 bg-gray-50 rounded-lg border border-gray-200 inline-block">
                  <p className="text-xs text-gray-500 mb-2">Aperçu :</p>
                  <img
                    src={logoUrl}
                    alt="Logo preview"
                    className="max-h-16 max-w-48 object-contain"
                    onError={(e) => { e.target.style.display = 'none'; }}
                    onLoad={(e) => { e.target.style.display = 'block'; }}
                  />
                </div>
              )}
            </div>

            {/* Colors row */}
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-5">
              {/* Primary color */}
              <div>
                <label htmlFor="primaryColor" className="block text-sm font-medium text-gray-700 mb-1">
                  Couleur primaire
                </label>
                <div className="flex items-center gap-3">
                  <input
                    id="primaryColor"
                    type="color"
                    value={primaryColor}
                    onChange={(e) => setPrimaryColor(e.target.value)}
                    className="w-12 h-10 rounded-lg border border-gray-300 cursor-pointer p-0.5"
                  />
                  <input
                    type="text"
                    value={primaryColor}
                    onChange={(e) => {
                      const v = e.target.value;
                      if (/^#[0-9A-Fa-f]{0,6}$/.test(v)) setPrimaryColor(v);
                    }}
                    maxLength={7}
                    className="flex-1 rounded-lg border border-gray-300 px-3 py-2.5 text-sm text-gray-900 font-mono focus:outline-none focus:ring-2 focus:border-transparent transition"
                    {...inputFocusHandlers}
                  />
                </div>
              </div>

              {/* Secondary color */}
              <div>
                <label htmlFor="secondaryColor" className="block text-sm font-medium text-gray-700 mb-1">
                  Couleur secondaire
                </label>
                <div className="flex items-center gap-3">
                  <input
                    id="secondaryColor"
                    type="color"
                    value={secondaryColor}
                    onChange={(e) => setSecondaryColor(e.target.value)}
                    className="w-12 h-10 rounded-lg border border-gray-300 cursor-pointer p-0.5"
                  />
                  <input
                    type="text"
                    value={secondaryColor}
                    onChange={(e) => {
                      const v = e.target.value;
                      if (/^#[0-9A-Fa-f]{0,6}$/.test(v)) setSecondaryColor(v);
                    }}
                    maxLength={7}
                    className="flex-1 rounded-lg border border-gray-300 px-3 py-2.5 text-sm text-gray-900 font-mono focus:outline-none focus:ring-2 focus:border-transparent transition"
                    {...inputFocusHandlers}
                  />
                </div>
              </div>
            </div>

            {/* Live preview card */}
            <div className="rounded-lg border border-gray-200 overflow-hidden">
              <div className="px-4 py-2.5 text-sm font-medium text-white" style={{ backgroundColor: primaryColor }}>
                Aperçu des couleurs
              </div>
              <div className="p-4 bg-white">
                <div className="flex items-center gap-3 mb-3">
                  {logoUrl && (
                    <img
                      src={logoUrl}
                      alt="Logo"
                      className="h-8 object-contain"
                      onError={(e) => { e.target.style.display = 'none'; }}
                    />
                  )}
                  <span className="text-sm font-semibold" style={{ color: primaryColor }}>
                    {companyName || 'Votre entreprise'}
                  </span>
                </div>
                <div className="h-2 rounded-full mb-2" style={{ backgroundColor: primaryColor, width: '75%' }} />
                <div className="h-2 rounded-full" style={{ backgroundColor: secondaryColor, width: '50%' }} />
                <p className="text-xs text-gray-400 mt-3">
                  Ce aperçu montre comment vos couleurs apparaîtront dans les rapports PDF.
                </p>
              </div>
            </div>

            {/* Save button */}
            <div className="pt-2">
              <button
                type="submit"
                disabled={brandingSaving}
                className="rounded-lg px-5 py-2.5 text-sm font-semibold text-white shadow-sm transition duration-150 ease-in-out disabled:opacity-50 disabled:cursor-not-allowed hover:opacity-90"
                style={{ backgroundColor: '#1B5E20' }}
              >
                {brandingSaving ? 'Enregistrement...' : 'Enregistrer le branding'}
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
}
