# GreenAudit — SaaS Audit Anti-Greenwashing

## Contexte projet

SaaS d'audit de conformité anti-greenwashing, conforme à la directive EmpCo (EU 2024/825, applicable 27 sept 2026). Modèle B2B2B white-label identique à AuditBiais : des partenaires (agences com, cabinets RSE, avocats) achètent l'audit en white-label et le revendent à leurs clients.

**Stack identique à AuditBiais :**
- Backend : FastAPI + PostgreSQL
- Frontend : React + Tailwind CSS
- Génération PDF : WeasyPrint (ou ReportLab)
- Auth : JWT avec multi-tenant (tenant = partenaire)
- Déploiement : Railway (back) + Vercel (front)

## Structure du projet

```
greenaudit/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI app + CORS
│   │   ├── config.py            # Settings (env vars)
│   │   ├── database.py          # SQLAlchemy async engine + session
│   │   ├── models/              # SQLAlchemy models
│   │   │   ├── partner.py
│   │   │   ├── audit.py
│   │   │   ├── claim.py
│   │   │   └── claim_result.py
│   │   ├── schemas/             # Pydantic schemas (request/response)
│   │   │   ├── partner.py
│   │   │   ├── audit.py
│   │   │   ├── claim.py
│   │   │   └── claim_result.py
│   │   ├── routers/             # API routes
│   │   │   ├── partners.py
│   │   │   ├── audits.py
│   │   │   ├── claims.py
│   │   │   └── reports.py
│   │   ├── services/            # Business logic
│   │   │   ├── analysis_engine.py   # Moteur d'analyse des 6 règles
│   │   │   ├── scoring.py           # Calcul scoring global
│   │   │   └── pdf_generator.py     # Génération rapport PDF white-label
│   │   ├── auth/
│   │   │   ├── jwt.py
│   │   │   └── dependencies.py  # get_current_partner, etc.
│   │   └── utils/
│   │       └── blacklist.py     # Liste termes génériques interdits
│   ├── alembic/                 # Migrations DB
│   ├── tests/
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── pages/
│   │   │   ├── Dashboard.jsx        # Vue partenaire : liste audits
│   │   │   ├── NewAudit.jsx         # Formulaire création audit
│   │   │   ├── ClaimForm.jsx        # Saisie des claims (multi-step)
│   │   │   ├── AuditResults.jsx     # Résultats + téléchargement PDF
│   │   │   ├── Settings.jsx         # Branding white-label
│   │   │   └── Login.jsx
│   │   ├── components/
│   │   ├── api/                     # Axios client
│   │   └── App.jsx
│   ├── package.json
│   └── vite.config.js
└── CLAUDE.md
```

## Modèle de données PostgreSQL

### Table `partners`
```sql
CREATE TABLE partners (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    company_name VARCHAR(255) NOT NULL,
    logo_url TEXT,
    brand_primary_color VARCHAR(7) DEFAULT '#1B5E20',
    brand_secondary_color VARCHAR(7) DEFAULT '#2E7D32',
    contact_name VARCHAR(255),
    contact_phone VARCHAR(50),
    stripe_customer_id VARCHAR(255),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
```

### Table `audits`
```sql
CREATE TABLE audits (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    partner_id UUID NOT NULL REFERENCES partners(id),
    -- Infos entreprise auditée
    company_name VARCHAR(255) NOT NULL,
    sector VARCHAR(100) NOT NULL,  -- e-commerce, cosmetiques, alimentaire, textile, services, autre
    website_url TEXT,
    contact_email VARCHAR(255),
    -- Résultats
    status VARCHAR(50) DEFAULT 'draft',  -- draft, in_progress, completed
    total_claims INTEGER DEFAULT 0,
    conforming_claims INTEGER DEFAULT 0,
    non_conforming_claims INTEGER DEFAULT 0,
    at_risk_claims INTEGER DEFAULT 0,
    global_score DECIMAL(5,2),  -- 0 à 100
    risk_level VARCHAR(20),  -- faible, modere, eleve, critique
    -- Méta
    pdf_url TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    completed_at TIMESTAMPTZ
);
```

### Table `claims`
```sql
CREATE TABLE claims (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    audit_id UUID NOT NULL REFERENCES audits(id) ON DELETE CASCADE,
    claim_text TEXT NOT NULL,  -- Texte exact de l'allégation
    support_type VARCHAR(50) NOT NULL,  -- web, packaging, publicite, reseaux_sociaux, autre
    scope VARCHAR(50) NOT NULL,  -- produit, entreprise
    product_name VARCHAR(255),  -- Si scope = produit
    -- Preuves déclarées
    has_proof BOOLEAN DEFAULT FALSE,
    proof_description TEXT,
    proof_type VARCHAR(100),  -- certification_tierce, rapport_interne, donnees_fournisseur, aucune
    -- Labels
    has_label BOOLEAN DEFAULT FALSE,
    label_name VARCHAR(255),
    label_is_certified BOOLEAN,  -- Certification tierce ou auto-décerné ?
    -- Engagement futur
    is_future_commitment BOOLEAN DEFAULT FALSE,
    target_date DATE,
    has_independent_verification BOOLEAN DEFAULT FALSE,
    -- Résultat global de la claim
    overall_verdict VARCHAR(20),  -- conforme, non_conforme, risque
    created_at TIMESTAMPTZ DEFAULT NOW()
);
```

### Table `claim_results`
```sql
CREATE TABLE claim_results (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    claim_id UUID NOT NULL REFERENCES claims(id) ON DELETE CASCADE,
    criterion VARCHAR(50) NOT NULL,  -- specificity, justification, proportionality, compensation, labels, future_commitment
    verdict VARCHAR(20) NOT NULL,  -- conforme, non_conforme, risque, non_applicable
    explanation TEXT NOT NULL,  -- Explication du verdict pour le rapport
    recommendation TEXT,  -- Action corrective recommandée
    regulation_reference TEXT,  -- Article EmpCo ou loi AGEC cité
    created_at TIMESTAMPTZ DEFAULT NOW()
);
```

## Moteur d'analyse — Les 6 règles

Le moteur est dans `services/analysis_engine.py`. Pour chaque claim, il applique 6 règles et produit un `claim_result` par règle.

### Règle 1 — Claims génériques (blacklist)

Détecte les termes génériques interdits par EmpCo dans `claim_text`. Si un terme est trouvé SANS qualification spécifique → `non_conforme`.

```python
BLACKLIST_TERMS = [
    "écologique", "éco-responsable", "éco responsable", "eco-friendly",
    "vert", "green", "respectueux de l'environnement",
    "respectueux de la planète", "ami de la nature", "nature friendly",
    "durable", "sustainable",  # seulement si utilisé seul sans contexte
    "biodégradable",  # sans certification/preuve
    "naturel", "natural",  # sur cosmétiques sans certification
    "climate friendly", "bon pour la planète",
    "zéro déchet", "zero waste",  # sans preuve quantifiée
    "propre", "clean",  # dans contexte environnemental
]
```

**Logique :** Le terme seul = `non_conforme`. Le terme + qualification mesurable (ex: "30% de plastique recyclé") = `risque` (vérifier la preuve). Terme absent = `non_applicable`.

### Règle 2 — Neutralité carbone par compensation

Détecte les claims de type "neutre en carbone", "carbon neutral", "zéro émission", "climate neutral", "compensé carbone". Si la claim repose sur de la compensation (offsets) → `non_conforme` SYSTÉMATIQUEMENT. C'est une interdiction absolue d'EmpCo, pas de nuance.

```python
CARBON_NEUTRAL_TERMS = [
    "neutre en carbone", "carbon neutral", "neutralité carbone",
    "climate neutral", "zéro émission", "zero emission",
    "impact neutre", "compensé carbone", "compensation carbone",
    "net zero", "net zéro",
]
```

### Règle 3 — Labels auto-décernés

Si `has_label = True` :
- `label_is_certified = False` → `non_conforme` (label auto-décerné interdit par EmpCo)
- `label_is_certified = True` → `conforme`
- `has_label = False` → `non_applicable`

### Règle 4 — Proportionnalité (ensemble vs aspect)

Si `scope = "entreprise"` mais la claim ne concerne qu'un aspect partiel → `risque` ou `non_conforme`.

**Logique simplifiée MVP :** On demande dans le formulaire "Cette allégation concerne-t-elle l'ensemble de votre activité ou un aspect spécifique ?" Si l'utilisateur indique "entreprise" mais que le claim_text mentionne un élément spécifique (emballage, transport, un produit) → `risque`.

### Règle 5 — Engagements futurs

Si `is_future_commitment = True` :
- `has_independent_verification = True` + `target_date` défini → `conforme`
- `has_independent_verification = False` OU pas de `target_date` → `non_conforme`
- `is_future_commitment = False` → `non_applicable`

### Règle 6 — Preuve et traçabilité

- `has_proof = True` + `proof_type` in (`certification_tierce`, `donnees_fournisseur`) → `conforme`
- `has_proof = True` + `proof_type = rapport_interne` → `risque` (preuve faible)
- `has_proof = False` ou `proof_type = aucune` → `non_conforme`

### Scoring global

```python
def calculate_global_score(claim_results: list[ClaimResult]) -> tuple[float, str]:
    """
    Calcul du score global de l'audit.
    
    - Chaque claim a un overall_verdict basé sur ses 6 claim_results
    - Une claim est "conforme" si AUCUN critère n'est non_conforme et max 1 est "risque"
    - Une claim est "non_conforme" si AU MOINS 1 critère est non_conforme
    - Une claim est "risque" si aucun non_conforme mais 2+ critères "risque"
    
    Score global = (claims conformes * 100 + claims risque * 50) / total_claims applicable
    
    Risk level:
    - >= 80 : "faible"
    - >= 60 : "modere"  
    - >= 40 : "eleve"
    - < 40  : "critique"
    """
```

## API Endpoints

### Auth
- `POST /api/auth/register` — Inscription partenaire
- `POST /api/auth/login` — Login → JWT token
- `GET /api/auth/me` — Profil partenaire courant

### Partners
- `GET /api/partners/me` — Infos partenaire
- `PUT /api/partners/me` — Modifier profil + branding
- `PUT /api/partners/me/branding` — Upload logo + couleurs

### Audits
- `POST /api/audits` — Créer un audit (draft)
- `GET /api/audits` — Lister les audits du partenaire
- `GET /api/audits/{audit_id}` — Détail d'un audit
- `DELETE /api/audits/{audit_id}` — Supprimer (si draft)

### Claims
- `POST /api/audits/{audit_id}/claims` — Ajouter une claim
- `GET /api/audits/{audit_id}/claims` — Lister les claims d'un audit
- `PUT /api/claims/{claim_id}` — Modifier une claim
- `DELETE /api/claims/{claim_id}` — Supprimer une claim

### Analyse
- `POST /api/audits/{audit_id}/analyze` — Lancer l'analyse (applique les 6 règles sur chaque claim, calcule le scoring, met à jour le status de l'audit)
- `GET /api/audits/{audit_id}/results` — Récupérer les résultats détaillés

### Rapports
- `POST /api/audits/{audit_id}/report` — Générer le PDF
- `GET /api/audits/{audit_id}/report/download` — Télécharger le PDF
- `GET /api/audits/{audit_id}/share/{token}` — Lien de partage client (lecture seule, pas d'auth)

## Rapport PDF — Structure

Le PDF généré contient ces sections dans cet ordre :

1. **Page de garde** — Logo partenaire, nom de l'entreprise auditée, date, score global en gros, niveau de risque avec code couleur
2. **Synthèse exécutive** — Score global, nb claims total / conformes / non conformes / risque, répartition graphique (camembert ou barre), phrase de synthèse
3. **Détail claim par claim** — Pour chaque claim : texte original, support, tableau des 6 critères avec verdict + explication, recommandation de correction
4. **Plan de correction priorisé** — Actions classées par urgence (critique > élevé > modéré), pour chaque action : claim concernée, ce qu'il faut faire (supprimer / reformuler / documenter), deadline suggérée
5. **Checklist labels** — Labels à retirer (auto-décernés) vs labels conformes à conserver
6. **Références réglementaires** — Articles EmpCo cités, loi AGEC, guide ADEME 2025
7. **Disclaimer** — "Ce rapport est un outil d'aide à la conformité et ne constitue pas un conseil juridique."

**Branding white-label :** Logo partenaire en haut de chaque page, couleurs primaire/secondaire du partenaire pour les titres et accents, coordonnées du partenaire en pied de page.

## Variables d'environnement

```env
DATABASE_URL=postgresql+asyncpg://user:pass@host:5432/greenaudit
SECRET_KEY=xxx
JWT_ALGORITHM=HS256
JWT_EXPIRATION_HOURS=24
CORS_ORIGINS=http://localhost:5173,https://greenaudit.app
PDF_STORAGE_PATH=./reports
# Optionnel
STRIPE_SECRET_KEY=sk_xxx
STRIPE_WEBHOOK_SECRET=whsec_xxx
```

## Conventions de code

- Python 3.11+, type hints partout
- SQLAlchemy 2.0 avec async
- Pydantic v2 pour les schemas
- Alembic pour les migrations
- Tests avec pytest + httpx (AsyncClient)
- Noms de variables et commentaires en français OK pour la logique métier, anglais pour le code technique
- Docstrings en français

## Ordre de développement recommandé

1. Setup projet FastAPI + database.py + config.py
2. Models SQLAlchemy (4 tables) + migration Alembic initiale
3. Schemas Pydantic (request/response)
4. Auth (register/login/JWT) + dependency get_current_partner
5. CRUD endpoints (partners, audits, claims)
6. Moteur d'analyse (analysis_engine.py + scoring.py) — C'EST LE CŒUR
7. Endpoint POST /analyze qui orchestre tout
8. Génération PDF (pdf_generator.py)
9. Endpoint rapport (generate + download + share link)
10. Tests
