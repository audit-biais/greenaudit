"""
Génération du rapport PDF white-label via WeasyPrint.

Produit un HTML complet avec CSS intégré, puis le convertit en PDF.
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional

from app.config import settings
from app.models.audit import Audit
from app.models.partner import Partner


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

RISK_COLORS: Dict[str, str] = {
    "faible": "#2E7D32",
    "modere": "#F9A825",
    "eleve": "#E65100",
    "critique": "#B71C1C",
}

VERDICT_LABELS: Dict[str, str] = {
    "conforme": "Conforme",
    "non_conforme": "Non conforme",
    "risque": "Risque",
    "non_applicable": "N/A",
}

VERDICT_COLORS: Dict[str, str] = {
    "conforme": "#2E7D32",
    "non_conforme": "#B71C1C",
    "risque": "#E65100",
    "non_applicable": "#757575",
}

CRITERION_LABELS: Dict[str, str] = {
    "specificity": "Spécificité",
    "compensation": "Neutralité carbone",
    "labels": "Labels",
    "proportionality": "Proportionnalité",
    "future_commitment": "Engagements futurs",
    "justification": "Justification / Preuves",
}

SUPPORT_LABELS: Dict[str, str] = {
    "web": "Site web",
    "packaging": "Packaging",
    "publicite": "Publicité",
    "reseaux_sociaux": "Réseaux sociaux",
    "autre": "Autre",
}

PRIORITY_ORDER = ["critique", "eleve", "modere", "faible"]


def _risk_color(level: Optional[str]) -> str:
    return RISK_COLORS.get(level or "", "#757575")


def _verdict_badge(verdict: str) -> str:
    color = VERDICT_COLORS.get(verdict, "#757575")
    label = VERDICT_LABELS.get(verdict, verdict)
    return (
        f'<span style="background:{color};color:#fff;padding:2px 8px;'
        f'border-radius:4px;font-size:0.85em;">{label}</span>'
    )


def _escape(text: Optional[str]) -> str:
    if not text:
        return ""
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def _format_date(dt: Optional[datetime]) -> str:
    if dt is None:
        return "—"
    return dt.strftime("%d/%m/%Y")


# ---------------------------------------------------------------------------
# Sections HTML
# ---------------------------------------------------------------------------

def _css(partner: Partner) -> str:
    primary = partner.brand_primary_color or "#1B5E20"
    secondary = partner.brand_secondary_color or "#2E7D32"
    return f"""
    @page {{
        size: A4;
        margin: 30mm 20mm 30mm 20mm;
        @top-center {{
            content: element(page-header);
        }}
        @bottom-center {{
            content: element(page-footer);
        }}
    }}
    @page :first {{
        @top-center {{ content: none; }}
        @bottom-center {{ content: none; }}
    }}
    .page-header {{
        position: running(page-header);
        display: flex;
        justify-content: space-between;
        align-items: center;
        border-bottom: 1px solid {primary};
        padding-bottom: 4px;
        font-size: 8px;
        color: #999;
    }}
    .page-header img {{ max-height: 24px; }}
    .page-footer {{
        position: running(page-footer);
        text-align: center;
        font-size: 8px;
        color: #999;
        border-top: 1px solid #ddd;
        padding-top: 4px;
    }}
    * {{ box-sizing: border-box; }}
    body {{
        font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif;
        font-size: 11px;
        color: #333;
        line-height: 1.5;
    }}
    h1 {{ color: {primary}; font-size: 22px; margin-top: 0; }}
    h2 {{ color: {primary}; font-size: 16px; border-bottom: 2px solid {secondary}; padding-bottom: 4px; }}
    h3 {{ color: {secondary}; font-size: 13px; }}
    .cover {{ page-break-after: always; text-align: center; padding-top: 80px; }}
    .cover .score {{ font-size: 64px; font-weight: bold; margin: 30px 0 10px; }}
    .cover .risk {{ font-size: 20px; padding: 6px 20px; border-radius: 8px; color: #fff; display: inline-block; }}
    table {{ width: 100%; border-collapse: collapse; margin: 10px 0; font-size: 10.5px; }}
    th, td {{ border: 1px solid #ddd; padding: 6px 8px; text-align: left; vertical-align: top; }}
    th {{ background: {primary}; color: #fff; font-weight: 600; }}
    .section {{ page-break-inside: avoid; margin-bottom: 20px; }}
    .claim-box {{ border: 1px solid #ccc; border-radius: 6px; padding: 12px; margin-bottom: 16px; page-break-inside: avoid; }}
    .claim-text {{ background: #f5f5f5; padding: 8px; border-left: 4px solid {secondary}; margin: 8px 0; font-style: italic; }}
    .summary-grid {{ display: flex; gap: 16px; margin: 16px 0; }}
    .summary-card {{ flex: 1; text-align: center; padding: 12px; border-radius: 8px; background: #f5f5f5; }}
    .summary-card .number {{ font-size: 28px; font-weight: bold; }}
    .footer {{ font-size: 9px; color: #777; border-top: 1px solid #ddd; padding-top: 6px; margin-top: 30px; }}
    .header-bar {{ display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; padding-bottom: 10px; border-bottom: 2px solid {primary}; }}
    .header-bar img {{ max-height: 40px; }}
    .priority-critique {{ border-left: 4px solid #B71C1C; }}
    .priority-eleve {{ border-left: 4px solid #E65100; }}
    .priority-modere {{ border-left: 4px solid #F9A825; }}
    .priority-faible {{ border-left: 4px solid #2E7D32; }}
    """


def _cover_page(audit: Audit, partner: Partner) -> str:
    risk_color = _risk_color(audit.risk_level)
    logo_html = ""
    if partner.logo_url:
        logo_html = f'<img src="{_escape(partner.logo_url)}" style="max-height:80px;margin-bottom:20px;" />'
    return f"""
    <div class="cover">
        {logo_html}
        <h1>Rapport d'audit anti-greenwashing</h1>
        <p style="font-size:18px;color:#555;">Directive EmpCo (EU 2024/825)</p>
        <hr style="margin:20px auto;width:60%;" />
        <p style="font-size:16px;"><strong>{_escape(audit.company_name)}</strong></p>
        <p>Secteur : {_escape(audit.sector)}</p>
        <div class="score" style="color:{risk_color};">{audit.global_score}/100</div>
        <div class="risk" style="background:{risk_color};">
            Risque {audit.risk_level or '—'}
        </div>
        <p style="margin-top:40px;color:#999;">
            Audit réalisé le {_format_date(audit.completed_at)}<br/>
            par {_escape(partner.company_name)}
        </p>
    </div>
    """


def _executive_summary(audit: Audit) -> str:
    total = audit.total_claims or 1
    conf_pct = round((audit.conforming_claims / total) * 100)
    nc_pct = round((audit.non_conforming_claims / total) * 100)
    risk_pct = round((audit.at_risk_claims / total) * 100)

    return f"""
    <h2>1. Synthèse exécutive</h2>
    <div class="summary-grid">
        <div class="summary-card">
            <div class="number">{audit.total_claims}</div>
            <div>Allégations analysées</div>
        </div>
        <div class="summary-card">
            <div class="number" style="color:#2E7D32;">{audit.conforming_claims}</div>
            <div>Conformes ({conf_pct}%)</div>
        </div>
        <div class="summary-card">
            <div class="number" style="color:#E65100;">{audit.at_risk_claims}</div>
            <div>À risque ({risk_pct}%)</div>
        </div>
        <div class="summary-card">
            <div class="number" style="color:#B71C1C;">{audit.non_conforming_claims}</div>
            <div>Non conformes ({nc_pct}%)</div>
        </div>
    </div>
    <p>
        L'entreprise <strong>{_escape(audit.company_name)}</strong> présente un niveau de risque
        <strong style="color:{_risk_color(audit.risk_level)};">{audit.risk_level}</strong>
        avec un score global de <strong>{audit.global_score}/100</strong>.
        {_summary_phrase(audit)}
    </p>
    """


def _summary_phrase(audit: Audit) -> str:
    if audit.risk_level == "faible":
        return "La majorité des allégations sont conformes. Quelques ajustements mineurs peuvent être envisagés."
    elif audit.risk_level == "modere":
        return "Plusieurs allégations nécessitent des corrections pour assurer la conformité à la directive EmpCo."
    elif audit.risk_level == "eleve":
        return "Un nombre significatif d'allégations sont non conformes. Des actions correctives urgentes sont recommandées."
    else:
        return "La situation est critique. La majorité des allégations environnementales sont non conformes et exposent l'entreprise à des sanctions."


def _claim_detail_section(claims: list) -> str:
    html = '<h2>2. Détail des allégations</h2>'
    for i, claim in enumerate(claims, 1):
        support = SUPPORT_LABELS.get(claim.support_type, claim.support_type)
        scope_label = "Entreprise" if claim.scope == "entreprise" else "Produit"
        if claim.product_name:
            scope_label += f" — {_escape(claim.product_name)}"

        html += f"""
        <div class="claim-box">
            <h3>Allégation #{i} {_verdict_badge(claim.overall_verdict or 'non_applicable')}</h3>
            <div class="claim-text">« {_escape(claim.claim_text)} »</div>
            <p><strong>Support :</strong> {support} | <strong>Portée :</strong> {scope_label}</p>
            <table>
                <tr>
                    <th style="width:22%;">Critère</th>
                    <th style="width:13%;">Verdict</th>
                    <th>Explication</th>
                    <th style="width:25%;">Recommandation</th>
                </tr>
        """
        for result in sorted(claim.results, key=lambda r: _criterion_sort_key(r.criterion)):
            criterion_label = CRITERION_LABELS.get(result.criterion, result.criterion)
            rec = _escape(result.recommendation) if result.recommendation else "—"
            html += f"""
                <tr>
                    <td>{criterion_label}</td>
                    <td>{_verdict_badge(result.verdict)}</td>
                    <td>{_escape(result.explanation)}</td>
                    <td>{rec}</td>
                </tr>
            """
        html += "</table></div>"
    return html


def _criterion_sort_key(criterion: str) -> int:
    order = ["specificity", "compensation", "labels", "proportionality", "future_commitment", "justification"]
    try:
        return order.index(criterion)
    except ValueError:
        return 99


def _correction_plan(claims: list) -> str:
    """Plan de correction priorisé par urgence."""
    actions: List[Dict[str, str]] = []

    for claim in claims:
        if claim.overall_verdict == "conforme":
            continue
        for result in claim.results:
            if result.verdict in ("non_conforme", "risque") and result.recommendation:
                priority = "critique" if result.verdict == "non_conforme" else "eleve"
                actions.append({
                    "priority": priority,
                    "claim_text": claim.claim_text[:80],
                    "criterion": CRITERION_LABELS.get(result.criterion, result.criterion),
                    "action": result.recommendation,
                    "reference": result.regulation_reference or "",
                })

    if not actions:
        return "<h2>3. Plan de correction</h2><p>Aucune action corrective nécessaire.</p>"

    # Trier par priorité
    actions.sort(key=lambda a: PRIORITY_ORDER.index(a["priority"]) if a["priority"] in PRIORITY_ORDER else 99)

    html = "<h2>3. Plan de correction priorisé</h2>"
    html += """
    <table>
        <tr>
            <th style="width:10%;">Priorité</th>
            <th style="width:20%;">Allégation</th>
            <th style="width:15%;">Critère</th>
            <th>Action corrective</th>
        </tr>
    """
    for a in actions:
        badge_color = RISK_COLORS.get(a["priority"], "#757575")
        html += f"""
        <tr class="priority-{a['priority']}">
            <td><span style="background:{badge_color};color:#fff;padding:2px 6px;border-radius:3px;font-size:0.85em;">
                {a['priority'].capitalize()}</span></td>
            <td>{_escape(a['claim_text'])}…</td>
            <td>{a['criterion']}</td>
            <td>{_escape(a['action'])}</td>
        </tr>
        """
    html += "</table>"
    return html


def _labels_checklist(claims: list) -> str:
    """Checklist des labels : à retirer vs à conserver."""
    to_remove: List[str] = []
    to_keep: List[str] = []

    for claim in claims:
        if not claim.has_label:
            continue
        name = claim.label_name or "Label non précisé"
        if claim.label_is_certified:
            to_keep.append(name)
        else:
            to_remove.append(name)

    if not to_remove and not to_keep:
        return ""

    html = "<h2>4. Checklist labels</h2>"
    if to_remove:
        html += "<h3>Labels à retirer (auto-décernés)</h3><ul>"
        for name in to_remove:
            html += f"<li style='color:#B71C1C;'>{_escape(name)}</li>"
        html += "</ul>"
    if to_keep:
        html += "<h3>Labels conformes à conserver</h3><ul>"
        for name in to_keep:
            html += f"<li style='color:#2E7D32;'>{_escape(name)}</li>"
        html += "</ul>"
    return html


def _regulatory_references() -> str:
    return """
    <h2>5. Références réglementaires</h2>
    <table>
        <tr><th>Texte</th><th>Référence</th><th>Objet</th></tr>
        <tr>
            <td>Directive EmpCo</td>
            <td>EU 2024/825</td>
            <td>Interdiction des allégations environnementales trompeuses, labels auto-décernés,
                claims de neutralité carbone par compensation</td>
        </tr>
        <tr>
            <td>Loi AGEC</td>
            <td>Loi n° 2020-105</td>
            <td>Interdiction des mentions « biodégradable » et « respectueux de l'environnement »
                sur les produits (Art. 13)</td>
        </tr>
        <tr>
            <td>Guide ADEME 2025</td>
            <td>Recommandations claims environnementales</td>
            <td>Bonnes pratiques de communication environnementale,
                méthodologie de justification des allégations</td>
        </tr>
        <tr>
            <td>Code de la consommation</td>
            <td>Art. L121-1 et suivants</td>
            <td>Pratiques commerciales trompeuses, sanctions applicables</td>
        </tr>
    </table>
    """


def _disclaimer(partner: Partner) -> str:
    return f"""
    <div class="footer" style="margin-top:40px;">
        <h2>Avertissement</h2>
        <p>Ce rapport est un outil d'aide à la conformité et ne constitue pas un conseil juridique.
        Il est recommandé de consulter un avocat spécialisé pour toute question relative à la
        conformité réglementaire de vos communications environnementales.</p>
        <p style="margin-top:12px;">
            <strong>{_escape(partner.company_name)}</strong><br/>
            {_escape(partner.contact_name) or ''}
            {(' — ' + _escape(partner.contact_phone)) if partner.contact_phone else ''}<br/>
            {_escape(partner.email)}
        </p>
    </div>
    """


# ---------------------------------------------------------------------------
# Point d'entrée principal
# ---------------------------------------------------------------------------

def generate_audit_pdf(audit: Audit, partner: Partner) -> str:
    """
    Génère le rapport PDF complet et le sauvegarde sur disque.

    Args:
        audit: Audit avec claims et claim_results chargés (eager loaded)
        partner: Partner avec infos branding

    Returns:
        Chemin relatif du fichier PDF généré
    """
    claims = sorted(audit.claims, key=lambda c: c.created_at)

    # Header et footer running pour chaque page (sauf la première)
    logo_header = ""
    if partner.logo_url:
        logo_header = f'<img src="{_escape(partner.logo_url)}" />'
    running_header = f"""
    <div class="page-header">
        <span>{logo_header}</span>
        <span>{_escape(partner.company_name)}</span>
    </div>
    """
    running_footer = f"""
    <div class="page-footer">
        {_escape(partner.company_name)}
        {(' — ' + _escape(partner.contact_phone)) if partner.contact_phone else ''}
        {(' — ' + _escape(partner.email)) if partner.email else ''}
        &nbsp;|&nbsp; Page <span class="page-number"></span>
    </div>
    """

    html_content = f"""
    <!DOCTYPE html>
    <html lang="fr">
    <head>
        <meta charset="UTF-8" />
        <style>{_css(partner)}</style>
    </head>
    <body>
        {running_header}
        {running_footer}
        {_cover_page(audit, partner)}
        {_executive_summary(audit)}
        {_claim_detail_section(claims)}
        {_correction_plan(claims)}
        {_labels_checklist(claims)}
        {_regulatory_references()}
        {_disclaimer(partner)}
    </body>
    </html>
    """

    # Créer le dossier de stockage
    storage_path = Path(settings.PDF_STORAGE_PATH)
    storage_path.mkdir(parents=True, exist_ok=True)

    filename = f"greenaudit_{audit.id}.pdf"
    filepath = storage_path / filename

    from weasyprint import HTML  # lazy import — nécessite les libs système (Pango, GLib)

    HTML(string=html_content).write_pdf(str(filepath))

    return filename
