import { useState, useEffect, Fragment } from 'react'
import { useNavigate } from 'react-router-dom'
import api from '../api/client'

const PLAN_LABELS = {
  free: 'Gratuit',
  starter: 'Starter',
  essentiel: 'Essentiel',
  partner: 'Partner',
  pro: 'Pro',
  enterprise: 'Entreprise',
}

const PLAN_COLORS = {
  free: 'bg-gray-100 text-gray-600',
  starter: 'bg-gray-100 text-gray-600',
  essentiel: 'bg-blue-100 text-blue-700',
  partner: 'bg-blue-100 text-blue-700',
  pro: 'bg-green-100 text-green-700',
  enterprise: 'bg-purple-100 text-purple-700',
}

const EMPTY_FORM = { email: '', password: '', role: 'member' }

export default function AdminPanel() {
  const [orgs, setOrgs] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [expandedOrg, setExpandedOrg] = useState(null)
  const [addingTo, setAddingTo] = useState(null)
  const [form, setForm] = useState(EMPTY_FORM)
  const [creating, setCreating] = useState(false)
  const [createError, setCreateError] = useState('')
  const [deleting, setDeleting] = useState(null)
  const navigate = useNavigate()

  const loadData = () => {
    setLoading(true)
    api.get('/admin/overview')
      .then(r => setOrgs(r.data))
      .catch(err => setError(err.response?.data?.detail || 'Erreur de chargement'))
      .finally(() => setLoading(false))
  }

  useEffect(() => { loadData() }, [])

  const handleSetPlan = async (orgId, plan) => {
    try {
      await api.patch(`/admin/orgs/${orgId}/plan`, { plan })
      loadData()
    } catch (err) {
      alert(err.response?.data?.detail || 'Erreur lors du changement de plan')
    }
  }

  const handleCreate = async (e, orgId) => {
    e.preventDefault()
    setCreating(true)
    setCreateError('')
    try {
      await api.post('/admin/users', { ...form, org_id: orgId })
      setAddingTo(null)
      setForm(EMPTY_FORM)
      loadData()
    } catch (err) {
      setCreateError(err.response?.data?.detail || 'Erreur lors de la création')
    } finally {
      setCreating(false)
    }
  }

  const handleDelete = async (userId, email) => {
    if (!window.confirm(`Supprimer le compte "${email}" ? Cette action est irréversible.`)) return
    setDeleting(userId)
    try {
      await api.delete(`/admin/users/${userId}`)
      loadData()
    } catch (err) {
      alert(err.response?.data?.detail || 'Erreur lors de la suppression')
    } finally {
      setDeleting(null)
    }
  }

  const realOrgs = orgs.filter(o => o.org_id !== null)
  const totalAudits = realOrgs.reduce((sum, o) => sum + o.audits_this_month, 0)
  const payingOrgs = realOrgs.filter(o => o.plan !== 'free').length
  const totalUsers = orgs.reduce((sum, o) => sum + o.members.length, 0)

  if (loading) return (
    <div className="flex items-center justify-center h-64 text-gray-400">Chargement...</div>
  )
  if (error) return (
    <div className="p-6 text-red-600 bg-red-50 rounded-xl">{error}</div>
  )

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-black text-gray-900">Super Admin</h1>
        <span className="text-xs text-gray-400">Accès restreint</span>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {[
          { label: 'Organisations', value: realOrgs.length },
          { label: 'Clients payants', value: payingOrgs },
          { label: 'Audits ce mois', value: totalAudits },
          { label: 'Comptes total', value: totalUsers },
        ].map(s => (
          <div key={s.label} className="bg-white rounded-xl border border-gray-100 p-5 text-center">
            <div className="text-3xl font-black text-[#1a5c3a]">{s.value}</div>
            <div className="text-sm text-gray-500 mt-1">{s.label}</div>
          </div>
        ))}
      </div>

      {/* Table */}
      <div className="bg-white rounded-xl border border-gray-100 overflow-hidden">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-gray-100 bg-gray-50">
              <th className="text-left px-4 py-3 font-semibold text-gray-600">Organisation</th>
              <th className="text-left px-4 py-3 font-semibold text-gray-600">Admin</th>
              <th className="text-left px-4 py-3 font-semibold text-gray-600">Plan</th>
              <th className="text-center px-4 py-3 font-semibold text-gray-600">Audits / mois</th>
              <th className="text-center px-4 py-3 font-semibold text-gray-600">Limite</th>
              <th className="text-center px-4 py-3 font-semibold text-gray-600">Membres</th>
              <th className="text-center px-4 py-3 font-semibold text-gray-600">Inscrit le</th>
              <th className="px-4 py-3"></th>
            </tr>
          </thead>
          <tbody>
            {orgs.map((org) => (
              <Fragment key={org.org_id ?? 'solo'}>
                <tr className="border-b border-gray-50 hover:bg-gray-50 transition-colors">
                  <td className="px-4 py-3 font-medium text-gray-900">{org.org_name}</td>
                  <td className="px-4 py-3 text-gray-500 text-xs">{org.admin_email || '—'}</td>
                  <td className="px-4 py-3">
                    {org.org_id ? (
                      <select
                        className={`text-xs font-semibold px-2 py-1 rounded-full border-0 cursor-pointer ${PLAN_COLORS[org.plan] || 'bg-gray-100 text-gray-600'}`}
                        value={org.plan}
                        onChange={(e) => handleSetPlan(org.org_id, e.target.value)}
                      >
                        <option value="starter">Starter</option>
                        <option value="partner">Partner</option>
                        <option value="pro">Pro</option>
                        <option value="enterprise">Entreprise</option>
                      </select>
                    ) : (
                      <span className="text-xs font-semibold px-2 py-1 rounded-full bg-gray-100 text-gray-600">
                        {PLAN_LABELS[org.plan] || org.plan}
                      </span>
                    )}
                  </td>
                  <td className="px-4 py-3 text-center font-mono text-gray-700">{org.audits_this_month}</td>
                  <td className="px-4 py-3 text-center font-mono text-gray-700">
                    {org.audits_limit >= 9999 ? '∞' : org.audits_limit}
                  </td>
                  <td className="px-4 py-3 text-center text-gray-700">{org.members.length}</td>
                  <td className="px-4 py-3 text-center text-gray-400 text-xs">{org.created_at || '—'}</td>
                  <td className="px-4 py-3 text-right space-x-2">
                    <button
                      className="text-xs text-[#1a5c3a] font-semibold hover:underline"
                      onClick={() => setExpandedOrg(expandedOrg === (org.org_id ?? 'solo') ? null : (org.org_id ?? 'solo'))}
                    >
                      {expandedOrg === (org.org_id ?? 'solo') ? 'Masquer' : 'Voir'}
                    </button>
                    {org.org_id && (
                      <button
                        className="text-xs text-blue-600 font-semibold hover:underline"
                        onClick={() => { setAddingTo(org.org_id); setForm(EMPTY_FORM); setCreateError('') }}
                      >
                        + Ajouter
                      </button>
                    )}
                  </td>
                </tr>

                {/* Formulaire ajout compte */}
                {addingTo === org.org_id && (
                  <tr className="bg-blue-50">
                    <td colSpan="8" className="px-6 py-4">
                      <form onSubmit={(e) => handleCreate(e, org.org_id)} className="flex flex-wrap items-end gap-3">
                        <div>
                          <label className="block text-xs font-medium text-gray-600 mb-1">Email</label>
                          <input
                            type="email" required
                            placeholder="email@exemple.com"
                            value={form.email}
                            onChange={(e) => setForm({ ...form, email: e.target.value })}
                            className="border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-[#1a5c3a]"
                          />
                        </div>
                        <div>
                          <label className="block text-xs font-medium text-gray-600 mb-1">Mot de passe</label>
                          <input
                            type="password" required minLength={6}
                            placeholder="Min. 6 caractères"
                            value={form.password}
                            onChange={(e) => setForm({ ...form, password: e.target.value })}
                            className="border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-[#1a5c3a]"
                          />
                        </div>
                        <div>
                          <label className="block text-xs font-medium text-gray-600 mb-1">Rôle</label>
                          <select
                            value={form.role}
                            onChange={(e) => setForm({ ...form, role: e.target.value })}
                            className="border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-[#1a5c3a]"
                          >
                            <option value="member">Collaborateur</option>
                            <option value="admin">Admin</option>
                          </select>
                        </div>
                        <button
                          type="submit" disabled={creating}
                          className="px-4 py-2 bg-[#1a5c3a] text-white text-sm font-semibold rounded-lg hover:bg-[#14472d] disabled:opacity-50"
                        >
                          {creating ? '...' : 'Créer'}
                        </button>
                        <button
                          type="button"
                          onClick={() => setAddingTo(null)}
                          className="px-4 py-2 bg-gray-200 text-gray-700 text-sm font-semibold rounded-lg hover:bg-gray-300"
                        >
                          Annuler
                        </button>
                        {createError && <p className="w-full text-xs text-red-600">{createError}</p>}
                      </form>
                    </td>
                  </tr>
                )}

                {/* Liste membres */}
                {expandedOrg === (org.org_id ?? 'solo') && (
                  <tr className="bg-gray-50">
                    <td colSpan="8" className="px-6 py-4">
                      <table className="w-full text-sm">
                        <thead>
                          <tr className="text-xs text-gray-500">
                            <th className="text-left pb-2">Email</th>
                            <th className="text-left pb-2">Rôle</th>
                            <th className="text-center pb-2">Audits ce mois</th>
                            <th className="pb-2"></th>
                          </tr>
                        </thead>
                        <tbody>
                          {org.members.map((m) => (
                            <tr key={m.user_id} className="border-t border-gray-200">
                              <td className="py-2 text-gray-700">{m.email}</td>
                              <td className="py-2">
                                <span className={`text-xs font-semibold px-2 py-0.5 rounded-full ${m.role === 'admin' ? 'bg-[#eaf4ee] text-[#1a5c3a]' : 'bg-gray-100 text-gray-600'}`}>
                                  {m.role === 'admin' ? 'Admin' : 'Collaborateur'}
                                </span>
                              </td>
                              <td className="py-2 text-center font-mono text-gray-700">{m.audits_this_month}</td>
                              <td className="py-2 text-right">
                                <button
                                  onClick={() => handleDelete(m.user_id, m.email)}
                                  disabled={deleting === m.user_id}
                                  className="text-xs text-red-500 hover:text-red-700 font-semibold disabled:opacity-50"
                                >
                                  {deleting === m.user_id ? '...' : 'Supprimer'}
                                </button>
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </td>
                  </tr>
                )}
              </Fragment>
            ))}
          </tbody>
        </table>

        {orgs.length === 0 && (
          <div className="text-center py-16 text-gray-400">Aucune organisation pour l'instant.</div>
        )}
      </div>
    </div>
  )
}
