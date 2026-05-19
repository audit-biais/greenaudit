"""
Script de test — génère le rapport marque pour la Raffinerie du Midi.
Usage : python3 generate_rapport_marque_test.py
"""
import os
import sys
import uuid
from datetime import datetime, timezone
from decimal import Decimal

# ── Charger le .env AVANT tout import de app.config ──────────────────────────
# pydantic-settings lit le .env via model_config, mais les variables déjà
# présentes dans os.environ ont la priorité. On force-load ici pour être
# certain que ANTHROPIC_API_KEY (et les autres) sont bien disponibles.
_ENV_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
if os.path.exists(_ENV_FILE):
    with open(_ENV_FILE, encoding="utf-8") as _f:
        for _line in _f:
            _line = _line.strip()
            if _line and not _line.startswith("#") and "=" in _line:
                _k, _v = _line.split("=", 1)
                os.environ[_k.strip()] = _v.strip()

# La SECRET_KEY du .env de dev est rejetée par le validateur pydantic — on la remplace
# uniquement pour ce script de test (n'affecte pas le .env).
import secrets as _secrets
os.environ["SECRET_KEY"] = _secrets.token_hex(32)

sys.path.insert(0, os.path.dirname(__file__))

from app.models.audit import Audit
from app.models.claim import Claim
from app.models.claim_result import ClaimResult
from app.services.pdf_generator_marque import generate_marque_pdf


def _make_result(criterion, verdict, explanation, recommendation=None, regulation_reference=None):
    r = ClaimResult()
    r.id = uuid.uuid4()
    r.criterion = criterion
    r.verdict = verdict
    r.explanation = explanation
    r.recommendation = recommendation
    r.regulation_reference = regulation_reference
    return r


def _make_claim(
    text, support_type, scope, verdict, regulatory_basis, regime,
    source_url=None, is_false_positive=False, results=None,
):
    c = Claim()
    c.id = uuid.uuid4()
    c.claim_text = text
    c.support_type = support_type
    c.scope = scope
    c.overall_verdict = verdict
    c.regulatory_basis = regulatory_basis
    c.regime = regime
    c.source_url = source_url
    c.is_false_positive = is_false_positive
    c.results = results or []
    return c


def build_raffinerie_audit() -> Audit:
    audit = Audit()
    audit.id = uuid.uuid4()
    audit.company_name = "Raffinerie du Midi"
    audit.sector = "Énergie / Pétrochimie"
    audit.website_url = "https://www.raffinerie-du-midi.fr"
    audit.status = "completed"
    audit.global_score = Decimal("22.00")
    audit.risk_level = "critique"
    audit.total_claims = 7
    audit.conforming_claims = 1
    audit.at_risk_claims = 1
    audit.non_conforming_claims = 5
    audit.completed_at = datetime(2026, 5, 15, tzinfo=timezone.utc)
    audit.organization = None

    claims = [
        _make_claim(
            text="La Raffinerie du Midi s'engage à atteindre la neutralité carbone d'ici 2035 "
                 "grâce à nos programmes de compensation carbone.",
            support_type="web",
            scope="entreprise",
            verdict="non_conforme",
            regulatory_basis="annexe_I_4quater",
            regime="liste_noire",
            source_url="https://www.raffinerie-du-midi.fr/engagement-environnemental",
            results=[
                _make_result(
                    "compensation", "non_conforme",
                    "La neutralité carbone revendiquée repose exclusivement sur des mécanismes "
                    "de compensation (crédits carbone), ce qui est explicitement interdit par "
                    "l'Annexe I, point 4 quater de la directive EmpCo.",
                    "Supprimer l'allégation de neutralité carbone par compensation. "
                    "Remplacer par une réduction réelle mesurable des émissions scope 1+2, "
                    "certifiée par un tiers (ex. SBTi). Ex. : 'Émissions réduites de 35 % "
                    "depuis 2019 sur les scopes 1 et 2, vérifiées par Bureau Veritas.'",
                    "Directive EmpCo (UE) 2024/825 — Annexe I, point 4 quater",
                ),
            ],
        ),
        _make_claim(
            text="Nos carburants sont verts et respectueux de l'environnement.",
            support_type="publicite",
            scope="produit",
            verdict="non_conforme",
            regulatory_basis="annexe_I_4bis",
            regime="liste_noire",
            source_url="https://www.raffinerie-du-midi.fr/produits/carburants",
            results=[
                _make_result(
                    "specificity", "non_conforme",
                    "Les termes 'verts' et 'respectueux de l'environnement' sont des "
                    "allégations génériques interdites sans qualification mesurable ni "
                    "référence à un standard reconnu.",
                    "Remplacer par une allégation précise et vérifiable. Ex. : 'Diesel "
                    "contenant 7 % de biodiesel certifié ISCC, réduisant les émissions "
                    "de CO₂ de 3,5 % en cycle de vie par rapport au diesel fossile pur.'",
                    "Directive EmpCo (UE) 2024/825 — Annexe I, point 4 bis",
                ),
            ],
        ),
        _make_claim(
            text="Entreprise éco-responsable engagée pour un avenir plus durable.",
            support_type="web",
            scope="entreprise",
            verdict="non_conforme",
            regulatory_basis="annexe_I_4bis",
            regime="liste_noire",
            source_url="https://www.raffinerie-du-midi.fr/a-propos",
            results=[
                _make_result(
                    "specificity", "non_conforme",
                    "'Éco-responsable' et 'avenir plus durable' sont des allégations "
                    "génériques sans ancrage factuel. L'Annexe I, point 4 bis interdit "
                    "toute allégation non étayée par des preuves spécifiques.",
                    "Supprimer ou restreindre à un aspect précis. Ex. : 'Notre site de "
                    "Frontignan est certifié ISO 14001 depuis 2021 — consulter notre "
                    "rapport environnemental 2025.'",
                    "Directive EmpCo (UE) 2024/825 — Annexe I, point 4 bis",
                ),
            ],
        ),
        _make_claim(
            text="Notre production est conforme aux normes environnementales européennes.",
            support_type="web",
            scope="entreprise",
            verdict="non_conforme",
            regulatory_basis="annexe_I_10bis",
            regime="liste_noire",
            source_url="https://www.raffinerie-du-midi.fr/conformite",
            results=[
                _make_result(
                    "legal_requirement", "non_conforme",
                    "La conformité aux normes européennes est une obligation légale, "
                    "pas un avantage environnemental distinctif. La présenter comme un "
                    "engagement volontaire est interdit par l'Annexe I, point 10 bis.",
                    "Supprimer cette mention ou reformuler clairement : 'Nous respectons "
                    "les réglementations environnementales en vigueur — comme l'ensemble "
                    "des acteurs du secteur.'",
                    "Directive EmpCo (UE) 2024/825 — Annexe I, point 10 bis",
                ),
            ],
        ),
        _make_claim(
            text="Nous visons à réduire nos émissions de CO₂ de 50 % d'ici 2035.",
            support_type="web",
            scope="entreprise",
            verdict="risque",
            regulatory_basis="article_6_1d",
            regime="cas_par_cas",
            source_url="https://www.raffinerie-du-midi.fr/trajectoire-carbone",
            results=[
                _make_result(
                    "future_commitment", "risque",
                    "L'engagement est chiffré (50 %) et daté (2035), mais aucun plan "
                    "de vérification indépendante ni de jalons intermédiaires n'est "
                    "documenté, comme l'exige l'Art. 6 §2 point d de la directive EmpCo.",
                    "Faire valider la trajectoire par un organisme accrédité (SBTi, "
                    "Bureau Veritas) et publier des objectifs intermédiaires vérifiables "
                    "sur le site. Documenter le plan dans le dossier de conformité.",
                    "Directive EmpCo (UE) 2024/825 — Art. 6, §2, point d",
                ),
            ],
        ),
        _make_claim(
            text="Nos installations utilisent 100 % d'électricité renouvelable.",
            support_type="web",
            scope="entreprise",
            verdict="non_conforme",
            regulatory_basis="annexe_I_4ter",
            regime="liste_noire",
            source_url="https://www.raffinerie-du-midi.fr/energie",
            results=[
                _make_result(
                    "proportionality", "non_conforme",
                    "L'allégation porte sur 'les installations' dans leur ensemble, "
                    "mais seuls les bureaux administratifs sont concernés par les "
                    "contrats d'énergie renouvelable. La portée de l'allégation dépasse "
                    "les pratiques réelles de l'entreprise.",
                    "Restreindre la portée : 'Nos bureaux administratifs sont alimentés "
                    "à 100 % par électricité renouvelable (contrat Garanties d'Origine, "
                    "EDF ENR).' Ne pas généraliser au site industriel.",
                    "Directive EmpCo (UE) 2024/825 — Annexe I, point 4 ter",
                ),
            ],
        ),
        _make_claim(
            text="Notre programme de certification ISO 14001 atteste de notre engagement environnemental.",
            support_type="web",
            scope="entreprise",
            verdict="conforme",
            regulatory_basis="article_6_general",
            regime="cas_par_cas",
            source_url="https://www.raffinerie-du-midi.fr/certifications",
            results=[
                _make_result(
                    "specificity", "conforme",
                    "La certification ISO 14001 est un standard reconnu et vérifiable "
                    "par un organisme tiers. L'allégation est spécifique et justifiable.",
                    None,
                    "Directive EmpCo (UE) 2024/825 — Art. 6 §1 point b",
                ),
            ],
        ),
    ]

    audit.claims = claims
    return audit


if __name__ == "__main__":
    print("Génération du rapport marque — Raffinerie du Midi...")
    audit = build_raffinerie_audit()
    filename, sha256 = generate_marque_pdf(audit)
    print(f"\nRapport généré : {filename}")
    print(f"SHA-256        : {sha256}")
    print(f"Chemin complet : ./reports/{filename}")

    # Ouvrir automatiquement sur macOS
    import subprocess
    subprocess.run(["open", f"./reports/{filename}"], check=False)
    print("\nOuverture du PDF...")
