# GreenAudit — MVP Spec

## Produit

SaaS d'audit de conformité anti-greenwashing, conforme à la Directive EmpCo (EU 2024/825, applicable le 27 septembre 2026).

**Modèle B2B2B white-label :**
- Des partenaires (agences com, cabinets RSE, avocats) s'abonnent
- Ils utilisent GreenAudit pour auditer leurs clients marques
- Ils revendent les rapports à leurs clients sous leur propre marque

---

## Pricing cible

| Plan | Prix | Limite | Cible |
|------|------|--------|-------|
| Free | 0€ | 1 audit/mois | Test |
| Essentiel | 250€/mois | 10 audits/mois | Petites agences |
| Pro | 500€/mois | Illimité | Cabinets RSE |
| Enterprise | Sur devis | Illimité + white-label custom | Grands groupes |

**Manque actuellement : Stripe (V2)**

---

## Stack technique

| Couche | Techno | URL prod |
|--------|--------|----------|
| Backend | FastAPI + PostgreSQL | `greenaudit-production.up.railway.app` |
| Frontend | React + Vite + Tailwind | Vercel (prj_DHsC3MowezPH1O9111ZHJahq43Oi) |
| IA rewrites | Claude Haiku (Anthropic) | API externe |
| Déploiement | Railway (back) + Vercel (front) | Auto-deploy sur push |

---

## Fonctionnalités MVP — État actuel

### Authentification & Multi-tenant
- [x] Signup / Login JWT
- [x] Organizations (1 org = 1 partenaire)
- [x] Multi-users par org (rôle admin/member)
- [x] Quotas d'audits par org (audits_limit)
- [x] Superadmin (sirius@gmail.com)

### Panel Superadmin
- [x] Vue toutes les orgs avec stats
- [x] Changer le plan d'une org
- [x] Créer / supprimer des users
- [x] Badge "SuperAdmin" dans la navbar

### Création d'audit
- [x] Formulaire (entreprise, secteur, URL, pays)
- [x] Pays : France (AGEC renforcé) ou autre UE
- [x] Scan automatique de site web (scrape + Claude Haiku)

### Moteur d'analyse — 8 règles EmpCo

| Règle | Article | Description |
|-------|---------|-------------|
| Spécificité | Annexe I, 4bis | Termes génériques interdits (vert, durable, éco...) |
| Neutralité carbone | Annexe I, 4quater | Compensation carbone interdite |
| Labels | Annexe I, 2bis | Labels auto-décernés interdits |
| Proportionnalité | Annexe I, 4ter | Scope entreprise vs aspect partiel + composants mineurs |
| Engagements futurs | Art. 6.2(d) | Plan + date + vérificateur indépendant obligatoires |
| Justification | Art. 6.1(b) + Art. 7 | Preuve vérifiable obligatoire |
| Exigence légale | Annexe I, 10bis | Obligation légale ≠ avantage distinctif |
| AGEC France | Loi n°2020-105, Art. 13 | Biodégradable / respectueux de l'environnement interdits |

**Versioning des règles :** `RULES_VERSION = "1.1.0"` — stocké sur chaque audit pour traçabilité.

### Filtre Écolabel (Preuve d'Excellence)
- [x] Upload de pièces justificatives par claim (Evidence Vault)
- [x] Type de document : Écolabel officiel / Certification / Rapport interne / Autre
- [x] Un Écolabel officiel dans le vault → verdict "Conforme" sur terme générique (Art. 2(s))

### Evidence Vault
- [x] Upload PDF / JPEG / PNG / Word (max 10 Mo)
- [x] Téléchargement fichier par fichier
- [x] ZIP de toutes les preuves d'un audit (dossier DGCCRF)

### Rewrite Engine
- [x] Suggestion de réécriture conforme EmpCo via Claude Haiku
- [x] Disponible sur les claims non_conforme et risque
- [x] Basé sur les raisons de non-conformité détectées

### Rapport PDF
- [x] Génération PDF complet (WeasyPrint)
- [x] Téléchargement depuis l'interface

### Monitoring continu
- [x] Scheduler APScheduler (interval 1h)
- [x] Scrape périodique du site web
- [x] Alertes en cas de nouvelles allégations détectées
- [x] Résumé des alertes non lues

---

## Ce qui manque pour monétiser (V2)

### Stripe — PRIORITÉ 1
- [ ] Plans payants (Essentiel 250€, Pro 500€)
- [ ] Webhook Stripe → mise à jour plan org
- [ ] Page checkout
- [ ] Portail client (gestion abonnement)

### Suivi corrections — PRIORITÉ 2
- [ ] Marquer une claim comme "corrigée" après réécriture
- [ ] Indicateur de progression de mise en conformité

---

## Workflow partenaire (flow complet)

```
Signup → Créer un audit → Saisir les allégations (ou scan URL)
→ Lancer l'analyse → Voir les résultats (8 critères par allégation)
→ Uploader les preuves (Evidence Vault)
→ Obtenir des suggestions de réécriture
→ Télécharger le rapport PDF + ZIP des preuves
→ Activer le monitoring pour détecter les nouvelles allégations
```

---

## Réglementation couverte

- **Directive EmpCo (EU 2024/825)** — modifie la Directive 2005/29/CE
- **Loi AGEC (n°2020-105)** — Art. 13 (France uniquement)
- **Deadline de conformité** : 27 septembre 2026

---

## Compte superadmin

- Email : sirius@gmail.com
- Mot de passe : 0139479356Aa-
- Accès : `/admin`
