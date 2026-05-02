"""Crée un audit de démonstration pré-analysé pour les nouveaux utilisateurs."""
from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audit import Audit
from app.models.claim import Claim
from app.models.claim_result import ClaimResult

logger = logging.getLogger(__name__)

_DEMO_CLAIMS = [
    {
        "claim_text": "Nos produits sont écologiques et naturels",
        "support_type": "web",
        "scope": "produit",
        "has_proof": False,
        "overall_verdict": "non_conforme",
        "regulatory_basis": "annexe_I_4bis",
        "regime": "liste_noire",
        "status": "À traiter",
        "results": [
            {
                "criterion": "specificity",
                "verdict": "non_conforme",
                "explanation": "Les termes 'écologiques' et 'naturels' sont des qualificatifs génériques interdits par la directive EmpCo sans qualification mesurable ni preuve.",
                "recommendation": "Remplacer par une allégation chiffrée : ex. '40% d'ingrédients d'origine naturelle certifiés Cosmos Organic'.",
                "regulation_reference": "Directive EmpCo (UE) 2024/825 — Annexe I, point 4 bis",
            },
            {
                "criterion": "compensation",
                "verdict": "non_applicable",
                "explanation": "Aucune revendication de neutralité carbone ou compensation détectée.",
                "recommendation": None,
                "regulation_reference": None,
            },
            {
                "criterion": "labels",
                "verdict": "non_applicable",
                "explanation": "Aucun label déclaré pour cette allégation.",
                "recommendation": None,
                "regulation_reference": None,
            },
            {
                "criterion": "proportionality",
                "verdict": "non_applicable",
                "explanation": "L'allégation porte sur un produit, pas sur l'ensemble de l'entreprise.",
                "recommendation": None,
                "regulation_reference": None,
            },
            {
                "criterion": "future_commitment",
                "verdict": "non_applicable",
                "explanation": "L'allégation est formulée au présent, pas comme engagement futur.",
                "recommendation": None,
                "regulation_reference": None,
            },
            {
                "criterion": "justification",
                "verdict": "non_conforme",
                "explanation": "Aucune preuve documentée fournie pour soutenir les termes 'écologiques' et 'naturels'.",
                "recommendation": "Reformuler l'allégation puis déposer les justificatifs dans le dossier de conformité.",
                "regulation_reference": "Directive EmpCo (UE) 2024/825 — Art. 6 §1",
            },
            {
                "criterion": "legal_requirement",
                "verdict": "non_applicable",
                "explanation": "Aucune exigence légale présentée comme avantage concurrentiel détectée.",
                "recommendation": None,
                "regulation_reference": None,
            },
            {
                "criterion": "agec_france",
                "verdict": "non_applicable",
                "explanation": "Aucun terme relevant spécifiquement de la loi AGEC (France) détecté.",
                "recommendation": None,
                "regulation_reference": None,
            },
        ],
    },
    {
        "claim_text": "Nous visons à réduire nos émissions de CO₂ de 40% d'ici 2027",
        "support_type": "web",
        "scope": "entreprise",
        "is_future_commitment": True,
        "has_proof": True,
        "proof_type": "rapport_interne",
        "overall_verdict": "risque",
        "regulatory_basis": "article_6_1d",
        "regime": "cas_par_cas",
        "status": "À traiter",
        "results": [
            {
                "criterion": "specificity",
                "verdict": "conforme",
                "explanation": "L'engagement est chiffré (40%) et daté (2027), ce qui répond à l'exigence de précision de la directive EmpCo.",
                "recommendation": None,
                "regulation_reference": "Directive EmpCo (UE) 2024/825 — Art. 6 §1",
            },
            {
                "criterion": "compensation",
                "verdict": "non_applicable",
                "explanation": "Aucune revendication de neutralité carbone par compensation détectée.",
                "recommendation": None,
                "regulation_reference": None,
            },
            {
                "criterion": "labels",
                "verdict": "non_applicable",
                "explanation": "Aucun label déclaré pour cette allégation.",
                "recommendation": None,
                "regulation_reference": None,
            },
            {
                "criterion": "proportionality",
                "verdict": "conforme",
                "explanation": "L'allégation porte sur l'ensemble des émissions de l'entreprise, cohérente avec la portée 'entreprise' déclarée.",
                "recommendation": None,
                "regulation_reference": None,
            },
            {
                "criterion": "future_commitment",
                "verdict": "risque",
                "explanation": "L'engagement futur est bien formulé mais manque de vérification par un organisme indépendant, exigée par la directive EmpCo.",
                "recommendation": "Faire valider la trajectoire de réduction par un tiers accrédité (ex: SBTi, Bureau Veritas) et documenter le plan annuel.",
                "regulation_reference": "Directive EmpCo (UE) 2024/825 — Art. 6 §1 d)",
            },
            {
                "criterion": "justification",
                "verdict": "risque",
                "explanation": "La preuve repose sur un rapport interne. Une certification tierce renforcerait significativement la défendabilité.",
                "recommendation": "Remplacer ou compléter le rapport interne par une certification tierce (ex: ISO 14064, bilan carbone certifié).",
                "regulation_reference": "Directive EmpCo (UE) 2024/825 — Art. 6 §1",
            },
            {
                "criterion": "legal_requirement",
                "verdict": "non_applicable",
                "explanation": "Aucune exigence légale présentée comme avantage concurrentiel détectée.",
                "recommendation": None,
                "regulation_reference": None,
            },
            {
                "criterion": "agec_france",
                "verdict": "non_applicable",
                "explanation": "Aucun terme relevant spécifiquement de la loi AGEC (France) détecté.",
                "recommendation": None,
                "regulation_reference": None,
            },
        ],
    },
    {
        "claim_text": "30% de plastique recyclé certifié GRS dans nos emballages",
        "support_type": "packaging",
        "scope": "produit",
        "has_proof": True,
        "proof_type": "certification_tierce",
        "has_label": True,
        "label_name": "GRS (Global Recycled Standard)",
        "label_is_certified": True,
        "overall_verdict": "conforme",
        "regulatory_basis": "article_6_general",
        "regime": "cas_par_cas",
        "status": "À traiter",
        "results": [
            {
                "criterion": "specificity",
                "verdict": "conforme",
                "explanation": "L'allégation est précise : pourcentage chiffré (30%), matière identifiée (plastique recyclé), périmètre défini (emballages).",
                "recommendation": None,
                "regulation_reference": "Directive EmpCo (UE) 2024/825 — Art. 6 §1",
            },
            {
                "criterion": "compensation",
                "verdict": "non_applicable",
                "explanation": "Aucune revendication de neutralité carbone ou compensation détectée.",
                "recommendation": None,
                "regulation_reference": None,
            },
            {
                "criterion": "labels",
                "verdict": "conforme",
                "explanation": "Le label GRS (Global Recycled Standard) est certifié par un organisme tiers accrédité. Conforme à la directive EmpCo.",
                "recommendation": None,
                "regulation_reference": "Directive EmpCo (UE) 2024/825 — Annexe I, point 2 bis",
            },
            {
                "criterion": "proportionality",
                "verdict": "non_applicable",
                "explanation": "L'allégation porte sur un produit spécifique, pas sur l'ensemble de l'entreprise.",
                "recommendation": None,
                "regulation_reference": None,
            },
            {
                "criterion": "future_commitment",
                "verdict": "non_applicable",
                "explanation": "L'allégation est formulée au présent, pas comme engagement futur.",
                "recommendation": None,
                "regulation_reference": None,
            },
            {
                "criterion": "justification",
                "verdict": "conforme",
                "explanation": "Certification tierce GRS fournie. Niveau de preuve satisfaisant selon la directive EmpCo.",
                "recommendation": None,
                "regulation_reference": "Directive EmpCo (UE) 2024/825 — Art. 6 §1",
            },
            {
                "criterion": "legal_requirement",
                "verdict": "non_applicable",
                "explanation": "Aucune exigence légale présentée comme avantage concurrentiel détectée.",
                "recommendation": None,
                "regulation_reference": None,
            },
            {
                "criterion": "agec_france",
                "verdict": "conforme",
                "explanation": "L'indication du taux de matière recyclée sur emballage est conforme aux exigences de la loi AGEC (Art. 13).",
                "recommendation": None,
                "regulation_reference": "Loi AGEC (France) — Art. 13 — Affichage environnemental",
            },
        ],
    },
]


async def create_demo_audit(organization_id: uuid.UUID, db: AsyncSession) -> None:
    try:
        audit = Audit(
            organization_id=organization_id,
            company_name="BioVerde France [DÉMO]",
            sector="cosmetiques",
            website_url="https://bioverde-exemple.fr",
            status="completed",
            total_claims=3,
            conforming_claims=1,
            non_conforming_claims=1,
            at_risk_claims=1,
            global_score=50,
            risk_level="eleve",
            country="fr",
            rules_version="2.0.0",
            completed_at=datetime.now(timezone.utc),
        )
        db.add(audit)
        await db.flush()

        for claim_data in _DEMO_CLAIMS:
            results_data = claim_data["results"]
            claim_fields = {k: v for k, v in claim_data.items() if k != "results"}
            claim = Claim(audit_id=audit.id, **claim_fields)
            db.add(claim)
            await db.flush()

            for r in results_data:
                db.add(ClaimResult(claim_id=claim.id, **r))

        await db.commit()
        logger.info(f"Audit de démonstration créé pour l'organisation {organization_id}")

    except Exception as e:
        await db.rollback()
        logger.error(f"Erreur création audit démo: {e}")
