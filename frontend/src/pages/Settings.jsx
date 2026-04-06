import { useState, useEffect } from 'react';
import { useAuth } from '../api/auth';
import api from '../api/client';

const MEMBER_LIMITS = { pro: 10, enterprise: null };

const PLAN_LABELS = {
  starter: 'Starter',
  free: 'Starter',
  pro: 'Pro',
  enterprise: 'Enterprise',
};

const PLAN_COLORS = {
  starter: 'bg-gray-100 text-gray-600',
  free: 'bg-gray-100 text-gray-600',
  pro: 'bg-[#eaf4ee] text-[#1a5c3a]',
  enterprise: 'bg-purple-100 text-purple-700',
};

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
  const { user } = useAuth();

  const [companyName, setCompanyName] = useState('');
  const [contactName, setContactName] = useState('');
  const [contactPhone, setContactPhone] = useState('');
  const [profileSaving, setProfileSaving] = useState(false);
  const [profileMessage, setProfileMessage] = useState(null);

  const [primaryColor, setPrimaryColor] = useState('#1a5c3a');
  const [secondaryColor, setSecondaryColor] = useState('#2E7D32');
  const [logoFile, setLogoFile] = useState(null);
  const [hasLogo, setHasLogo] = useState(false);
  const [brandingSaving, setBrandingSaving] = useState(false);
  const [brandingMessage, setBrandingMessage] = useState(null);
  const [checkoutLoading, setCheckoutLoading] = useState(false);
  const [portalLoading, setPortalLoading] = useState(false);

  useEffect(() => {
    if (!user?.organization?.id) return;
    // Charger les détails complets de l'organisation (contact_name, contact_phone, etc.)
    api.get('/organizations/me').then((res) => {
      const org = res.data;
      setCompanyName(org.name || '');
      setContactName(org.contact_name || '');
      setContactPhone(org.contact_phone || '');
      setPrimaryColor(org.brand_primary_color || '#1a5c3a');
      setSecondaryColor(org.brand_secondary_color || '#2E7D32');
      setHasLogo(org.has_logo || false);
    }).catch(() => {
      // Fallback sur les données user si la route org échoue
      setCompanyName(user.organization?.name || user.company_name || '');
      setPrimaryColor(user.organization?.brand_primary_color || '#1a5c3a');
      setSecondaryColor(user.organization?.brand_secondary_color || '#2E7D32');
    });
  }, [user]);

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
      await api.put('/organizations/settings', {
        name: companyName,
        contact_name: contactName || null,
        contact_phone: contactPhone || null,
      });
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
      // Sauvegarder les couleurs
      await api.put('/organizations/settings', {
        brand_primary_color: primaryColor,
        brand_secondary_color: secondaryColor,
      });

      // Uploader le logo si un fichier a été sélectionné
      if (logoFile) {
        const formData = new FormData();
        formData.append('logo', logoFile);
        await api.post('/organizations/logo', formData, {
          headers: { 'Content-Type': 'multipart/form-data' },
        });
        setHasLogo(true);
        setLogoFile(null);
      }

      setBrandingMessage({ type: 'success', text: 'Branding mis à jour avec succès.' });
    } catch (err) {
      const detail = err.response?.data?.detail;
      setBrandingMessage({ type: 'error', text: typeof detail === 'string' ? detail : 'Erreur lors de la mise à jour.' });
    } finally {
      setBrandingSaving(false);
    }
  };

  const logoPreviewUrl = logoFile ? URL.createObjectURL(logoFile) : null;

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

      {/* Section Branding — Pro/Enterprise uniquement */}
      {['starter', 'free'].includes(user?.subscription_plan) ? (
        <div className="bg-white rounded-2xl border border-gray-100 overflow-hidden">
          <div className="px-6 py-4 border-b border-gray-50 bg-gray-50">
            <div className="flex items-center gap-2">
              <h2 className="text-sm font-bold text-gray-400">Branding white-label</h2>
              <span className="text-xs font-semibold px-2 py-0.5 rounded-full bg-gray-100 text-gray-400">Pro</span>
            </div>
            <p className="text-xs text-gray-400 mt-0.5">Personnalisez le logo et les couleurs de vos rapports PDF.</p>
          </div>
          <div className="p-6 flex flex-col items-center justify-center text-center gap-3 py-10">
            <svg className="w-8 h-8 text-gray-300" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
            </svg>
            <p className="text-sm text-gray-400">Le branding white-label est réservé au plan Pro.</p>
          </div>
        </div>
      ) : (
      <div className="bg-white rounded-2xl border border-gray-100 overflow-hidden">
        <div className="px-6 py-4 border-b border-gray-50 bg-[#eaf4ee]">
          <h2 className="text-sm font-bold text-[#1a5c3a]">Branding white-label</h2>
          <p className="text-xs text-gray-500 mt-0.5">Personnalisez l'apparence de vos rapports d'audit.</p>
        </div>
        <form onSubmit={handleBrandingSave} className="p-6 space-y-5">
          <MessageBanner message={brandingMessage} />

          {/* Logo */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1.5">Logo (PNG ou JPEG, max 2 Mo)</label>
            <input type="file" accept="image/png,image/jpeg"
              onChange={(e) => setLogoFile(e.target.files[0] || null)}
              className="block w-full text-sm text-gray-600 file:mr-4 file:py-2 file:px-4 file:rounded-full file:border-0 file:text-sm file:font-semibold file:bg-[#eaf4ee] file:text-[#1a5c3a] hover:file:bg-[#d4ecdd] cursor-pointer" />
            {logoPreviewUrl && (
              <div className="mt-3 p-3 bg-gray-50 rounded-xl border border-gray-100 inline-block">
                <p className="text-xs text-gray-400 mb-2">Aperçu :</p>
                <img src={logoPreviewUrl} alt="Logo preview" className="max-h-16 max-w-48 object-contain" />
              </div>
            )}
            {!logoPreviewUrl && hasLogo && (
              <p className="mt-2 text-xs text-[#1a5c3a]">Un logo est déjà enregistré. Sélectionnez un fichier pour le remplacer.</p>
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
                {logoPreviewUrl && (
                  <img src={logoPreviewUrl} alt="Logo" className="h-8 object-contain" />
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
      )}

      {/* ── Équipe — Pro/Enterprise uniquement ── */}
      {['pro', 'enterprise'].includes(user?.subscription_plan) && user?.role === 'admin' && (
        <TeamSection user={user} />
      )}

      {/* ── Abonnement ── */}
      <SubscriptionSection
        user={user}
        checkoutLoading={checkoutLoading}
        setCheckoutLoading={setCheckoutLoading}
        portalLoading={portalLoading}
        setPortalLoading={setPortalLoading}
      />
    </div>
  );
}

function TeamSection({ user }) {
  const plan = user?.subscription_plan;
  const limit = MEMBER_LIMITS[plan] ?? null;

  const [members, setMembers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [showForm, setShowForm] = useState(false);
  const [inviteEmail, setInviteEmail] = useState('');
  const [invitePassword, setInvitePassword] = useState('');
  const [inviteRole, setInviteRole] = useState('member');
  const [inviting, setInviting] = useState(false);
  const [deletingId, setDeletingId] = useState(null);

  useEffect(() => {
    api.get('/organizations/members')
      .then((res) => setMembers(res.data))
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  useEffect(() => {
    if (success) { const t = setTimeout(() => setSuccess(''), 4000); return () => clearTimeout(t); }
  }, [success]);

  const handleInvite = async (e) => {
    e.preventDefault();
    setInviting(true);
    setError('');
    try {
      const res = await api.post('/organizations/members', {
        email: inviteEmail,
        password: invitePassword,
        role: inviteRole,
      });
      setMembers((prev) => [...prev, res.data]);
      setInviteEmail('');
      setInvitePassword('');
      setInviteRole('member');
      setShowForm(false);
      setSuccess('Collaborateur ajouté avec succès.');
    } catch (err) {
      setError(err.response?.data?.detail || "Erreur lors de l'invitation.");
    } finally {
      setInviting(false);
    }
  };

  const handleDelete = async (memberId) => {
    if (!window.confirm('Supprimer ce membre ?')) return;
    setDeletingId(memberId);
    try {
      await api.delete(`/organizations/members/${memberId}`);
      setMembers((prev) => prev.filter((m) => m.id !== memberId));
      setSuccess('Membre supprimé.');
    } catch (err) {
      setError(err.response?.data?.detail || 'Erreur lors de la suppression.');
    } finally {
      setDeletingId(null);
    }
  };

  const atLimit = limit !== null && members.length >= limit;

  return (
    <div className="bg-white rounded-2xl border border-gray-100 overflow-hidden">
      <div className="px-6 py-4 border-b border-gray-50 bg-[#eaf4ee] flex items-center justify-between">
        <div>
          <div className="flex items-center gap-2">
            <h2 className="text-sm font-bold text-[#1a5c3a]">Équipe</h2>
            {limit !== null && (
              <span className="text-xs font-semibold px-2 py-0.5 rounded-full bg-white text-[#1a5c3a] border border-[#1a5c3a]/20">
                {members.length}/{limit}
              </span>
            )}
          </div>
          <p className="text-xs text-gray-500 mt-0.5">Gérez les collaborateurs de votre organisation.</p>
        </div>
        {!atLimit && (
          <button
            onClick={() => setShowForm((v) => !v)}
            className="text-xs font-semibold px-3 py-1.5 rounded-full bg-[#1a5c3a] text-white hover:bg-[#14472d] transition-colors"
          >
            {showForm ? 'Annuler' : '+ Inviter'}
          </button>
        )}
      </div>

      <div className="p-6 space-y-4">
        {error && (
          <div className="p-3 bg-red-50 border border-red-100 rounded-xl text-red-700 text-sm">{error}</div>
        )}
        {success && (
          <div className="p-3 bg-[#eaf4ee] border border-[#1a5c3a]/20 rounded-xl text-[#1a5c3a] text-sm">{success}</div>
        )}

        {/* Formulaire invitation */}
        {showForm && (
          <form onSubmit={handleInvite} className="p-4 bg-gray-50 rounded-xl border border-gray-100 space-y-3">
            <p className="text-xs font-semibold text-gray-700">Nouveau collaborateur</p>
            <input
              type="email" required placeholder="Email" value={inviteEmail}
              onChange={(e) => setInviteEmail(e.target.value)}
              className={inputCls}
            />
            <input
              type="password" required placeholder="Mot de passe temporaire" value={invitePassword}
              onChange={(e) => setInvitePassword(e.target.value)}
              className={inputCls}
            />
            <select
              value={inviteRole} onChange={(e) => setInviteRole(e.target.value)}
              className={inputCls}
            >
              <option value="member">Membre</option>
              <option value="admin">Administrateur</option>
            </select>
            <button
              type="submit" disabled={inviting}
              className="w-full py-2.5 rounded-xl bg-[#1a5c3a] text-white text-sm font-semibold hover:bg-[#14472d] transition disabled:opacity-50"
            >
              {inviting ? 'Ajout en cours...' : 'Ajouter le collaborateur'}
            </button>
          </form>
        )}

        {atLimit && (
          <div className="p-3 bg-orange-50 border border-orange-100 rounded-xl text-orange-700 text-xs">
            Limite de {limit} membres atteinte pour le plan Pro.
          </div>
        )}

        {/* Liste des membres */}
        {loading ? (
          <p className="text-sm text-gray-400">Chargement...</p>
        ) : members.length === 0 ? (
          <p className="text-sm text-gray-400">Aucun membre pour l'instant.</p>
        ) : (
          <div className="divide-y divide-gray-50">
            {members.map((m) => (
              <div key={m.id} className="flex items-center justify-between py-3">
                <div>
                  <p className="text-sm font-medium text-gray-900">{m.email}</p>
                  <div className="flex items-center gap-2 mt-0.5">
                    <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${
                      m.role === 'admin'
                        ? 'bg-[#eaf4ee] text-[#1a5c3a]'
                        : 'bg-gray-100 text-gray-500'
                    }`}>
                      {m.role === 'admin' ? 'Admin' : 'Membre'}
                    </span>
                    {m.is_self && (
                      <span className="text-xs text-gray-400">(vous)</span>
                    )}
                  </div>
                </div>
                <div className="flex items-center gap-4">
                  <div className="text-right">
                    <p className="text-sm font-semibold text-gray-900">{m.audits_count ?? 0}</p>
                    <p className="text-xs text-gray-400">audit{m.audits_count !== 1 ? 's' : ''}</p>
                  </div>
                  {!m.is_self && (
                    <button
                      onClick={() => handleDelete(m.id)}
                      disabled={deletingId === m.id}
                      className="text-xs text-red-400 hover:text-red-600 font-medium disabled:opacity-50"
                    >
                      {deletingId === m.id ? '...' : 'Supprimer'}
                    </button>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

function SubscriptionSection({ user, checkoutLoading, setCheckoutLoading, portalLoading, setPortalLoading }) {
  const plan = user?.subscription_plan || 'starter';
  const auditsUsed = user?.audits_this_month ?? 0;
  const auditsLimit = user?.audits_limit ?? 1;
  const isPro = plan === 'pro';
  const isEnterprise = plan === 'enterprise';
  const isStarter = !isPro && !isEnterprise;

  const handleUpgrade = async () => {
    setCheckoutLoading(true);
    try {
      const res = await api.post('/payment/create-checkout');
      window.location.href = res.data.checkout_url;
    } catch (err) {
      alert('Erreur lors de la création du checkout. Réessayez.');
      setCheckoutLoading(false);
    }
  };

  const handlePortal = async () => {
    setPortalLoading(true);
    try {
      const res = await api.post('/payment/portal');
      window.location.href = res.data.portal_url;
    } catch (err) {
      alert('Erreur lors de l\'ouverture du portail. Réessayez.');
      setPortalLoading(false);
    }
  };

  return (
    <div className="bg-white rounded-2xl border border-gray-100 p-6">
      <h2 className="text-base font-semibold text-gray-900 mb-5">Abonnement</h2>

      {/* Plan actuel */}
      <div className="flex items-center justify-between mb-4">
        <div>
          <p className="text-sm text-gray-500 mb-1">Plan actuel</p>
          <span className={`inline-block text-xs font-semibold px-3 py-1 rounded-full ${PLAN_COLORS[plan] || PLAN_COLORS.starter}`}>
            {PLAN_LABELS[plan] || 'Starter'}
          </span>
        </div>
        {(isPro) && (
          <div className="text-right">
            <p className="text-sm text-gray-500 mb-1">Audits ce mois</p>
            <p className="text-sm font-semibold text-gray-900">{auditsUsed} / {auditsLimit}</p>
          </div>
        )}
        {isEnterprise && (
          <div className="text-right">
            <p className="text-sm text-gray-500">Audits</p>
            <p className="text-sm font-semibold text-gray-900">Illimités</p>
          </div>
        )}
      </div>

      {/* Barre de progression pour Pro */}
      {isPro && (
        <div className="mb-5">
          <div className="w-full bg-gray-100 rounded-full h-1.5">
            <div
              className="bg-[#1a5c3a] h-1.5 rounded-full transition-all"
              style={{ width: `${Math.min((auditsUsed / auditsLimit) * 100, 100)}%` }}
            />
          </div>
          {auditsUsed >= auditsLimit && (
            <p className="text-xs text-orange-600 mt-1">
              Limite atteinte —{' '}
              <a href="/contact" className="underline font-semibold hover:text-orange-700">
                contactez-nous
              </a>{' '}
              pour ajouter des audits (400€/audit).
            </p>
          )}
        </div>
      )}

      {/* Starter → upgrade */}
      {isStarter && (
        <div className="rounded-xl bg-gray-50 border border-gray-100 p-4 mb-4">
          <p className="text-sm text-gray-600 mb-3">
            Votre audit d'essai est inclus. Passez au plan Pro pour accéder à l'analyse complète,
            les rapports PDF, l'Evidence Vault et le monitoring continu.
          </p>
          <div className="flex items-baseline gap-2 mb-3">
            <span className="text-2xl font-bold text-gray-900">2 990€</span>
            <span className="text-sm text-gray-500">/mois · 12 mois</span>
          </div>
          <button
            onClick={handleUpgrade}
            disabled={checkoutLoading}
            className="w-full py-2.5 rounded-xl bg-[#1a5c3a] text-white text-sm font-semibold hover:bg-[#154d30] transition disabled:opacity-60"
          >
            {checkoutLoading ? 'Redirection...' : 'Passer au plan Pro'}
          </button>
        </div>
      )}

      {/* Pro → gérer abonnement */}
      {isPro && (
        <button
          onClick={handlePortal}
          disabled={portalLoading}
          className="w-full py-2.5 rounded-xl bg-gray-100 text-gray-700 text-sm font-medium hover:bg-gray-200 transition disabled:opacity-60"
        >
          {portalLoading ? 'Ouverture...' : 'Gérer mon abonnement (factures, résiliation)'}
        </button>
      )}

      {/* Enterprise */}
      {isEnterprise && (
        <p className="text-sm text-gray-500">
          Plan Enterprise actif. Contactez-nous pour toute modification.
        </p>
      )}
    </div>
  );
}
