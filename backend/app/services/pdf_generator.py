"""
Génération du rapport PDF white-label via ReportLab (pure Python, pas de dépendance système).
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    BaseDocTemplate,
    Frame,
    NextPageTemplate,
    PageBreak,
    PageTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
)

from app.config import settings
from app.models.audit import Audit
from app.models.partner import Partner


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

RISK_COLORS: Dict[str, colors.Color] = {
    "faible": colors.HexColor("#2E7D32"),
    "modere": colors.HexColor("#F9A825"),
    "eleve": colors.HexColor("#E65100"),
    "critique": colors.HexColor("#B71C1C"),
}

VERDICT_LABELS: Dict[str, str] = {
    "conforme": "Conforme",
    "non_conforme": "Non conforme",
    "risque": "Risque",
    "non_applicable": "N/A",
}

CRITERION_LABELS: Dict[str, str] = {
    "specificity": "Spécificité",
    "compensation": "Neutralité carbone",
    "labels": "Labels",
    "proportionality": "Proportionnalité",
    "future_commitment": "Engagements futurs",
    "justification": "Justification / Preuves",
}

CRITERION_ORDER = [
    "specificity", "compensation", "labels",
    "proportionality", "future_commitment", "justification",
]

SUPPORT_LABELS: Dict[str, str] = {
    "web": "Site web",
    "packaging": "Packaging",
    "publicite": "Publicité",
    "reseaux_sociaux": "Réseaux sociaux",
    "autre": "Autre",
}


def _hex(color_str: Optional[str], fallback: str = "#1B5E20") -> colors.Color:
    try:
        return colors.HexColor(color_str or fallback)
    except Exception:
        return colors.HexColor(fallback)


def _format_date(dt: Optional[datetime]) -> str:
    if dt is None:
        return "—"
    return dt.strftime("%d/%m/%Y")


def _summary_phrase(risk_level: Optional[str]) -> str:
    phrases = {
        "faible": "La majorité des allégations sont conformes.",
        "modere": "Plusieurs allégations nécessitent des corrections.",
        "eleve": "Un nombre significatif d'allégations sont non conformes. Actions correctives urgentes recommandées.",
        "critique": "Situation critique. La majorité des allégations exposent l'entreprise à des sanctions.",
    }
    return phrases.get(risk_level or "", phrases["critique"])


# ---------------------------------------------------------------------------
# Styles
# ---------------------------------------------------------------------------

def _build_styles(primary: colors.Color, secondary: colors.Color):
    ss = getSampleStyleSheet()
    styles = {
        "title": ParagraphStyle("title", parent=ss["Title"], fontSize=22, textColor=primary, spaceAfter=6),
        "h1": ParagraphStyle("h1", parent=ss["Heading1"], fontSize=16, textColor=primary, spaceAfter=8, spaceBefore=16),
        "h2": ParagraphStyle("h2", parent=ss["Heading2"], fontSize=13, textColor=secondary, spaceAfter=6, spaceBefore=12),
        "body": ParagraphStyle("body", parent=ss["Normal"], fontSize=10, leading=14, spaceAfter=4),
        "small": ParagraphStyle("small", parent=ss["Normal"], fontSize=8, textColor=colors.gray, spaceAfter=2),
        "italic": ParagraphStyle("italic", parent=ss["Normal"], fontSize=10, leading=14, textColor=colors.HexColor("#555555"), spaceAfter=4),
        "bold": ParagraphStyle("bold", parent=ss["Normal"], fontSize=10, leading=14, spaceAfter=4),
        "cover_score": ParagraphStyle("cover_score", parent=ss["Title"], fontSize=48, alignment=1, spaceAfter=4),
        "cover_center": ParagraphStyle("cover_center", parent=ss["Normal"], fontSize=14, alignment=1, spaceAfter=4),
        "cover_small": ParagraphStyle("cover_small", parent=ss["Normal"], fontSize=10, alignment=1, textColor=colors.gray, spaceAfter=4),
        "disclaimer": ParagraphStyle("disclaimer", parent=ss["Normal"], fontSize=8, textColor=colors.gray, leading=11),
    }
    return styles


# ---------------------------------------------------------------------------
# Page templates avec header/footer
# ---------------------------------------------------------------------------

def _build_doc(filepath: str, partner: Partner) -> BaseDocTemplate:
    primary = _hex(partner.brand_primary_color)
    company = partner.company_name or ""
    email = partner.email or ""
    phone = partner.contact_phone or ""

    def _header_footer(canvas, doc):
        canvas.saveState()
        # Header : nom du partenaire
        canvas.setFont("Helvetica", 8)
        canvas.setFillColor(colors.gray)
        canvas.drawString(20 * mm, A4[1] - 12 * mm, company)
        # Ligne sous le header
        canvas.setStrokeColor(primary)
        canvas.setLineWidth(0.5)
        canvas.line(20 * mm, A4[1] - 14 * mm, A4[0] - 20 * mm, A4[1] - 14 * mm)
        # Footer
        footer_parts = [p for p in [company, phone, email] if p]
        footer_text = " — ".join(footer_parts)
        canvas.setFont("Helvetica", 7)
        canvas.setFillColor(colors.gray)
        canvas.drawCentredString(A4[0] / 2, 12 * mm, footer_text)
        canvas.drawRightString(A4[0] - 20 * mm, 12 * mm, f"Page {doc.page}")
        canvas.restoreState()

    def _cover_footer(canvas, doc):
        pass  # Pas de header/footer sur la page de garde

    frame = Frame(20 * mm, 20 * mm, A4[0] - 40 * mm, A4[1] - 40 * mm, id="main")
    cover_frame = Frame(20 * mm, 20 * mm, A4[0] - 40 * mm, A4[1] - 40 * mm, id="cover")

    doc = BaseDocTemplate(
        filepath,
        pagesize=A4,
        pageTemplates=[
            PageTemplate(id="cover", frames=[cover_frame], onPage=_cover_footer),
            PageTemplate(id="content", frames=[frame], onPage=_header_footer),
        ],
    )
    return doc


# ---------------------------------------------------------------------------
# Sections
# ---------------------------------------------------------------------------

def _cover_elements(audit: Audit, partner: Partner, styles: dict) -> list:
    primary = _hex(partner.brand_primary_color)
    risk_color = RISK_COLORS.get(audit.risk_level or "", colors.gray)
    elements = []
    elements.append(Spacer(1, 60 * mm))
    elements.append(Paragraph("Rapport d'audit anti-greenwashing", styles["title"]))
    elements.append(Paragraph("Directive EmpCo (EU 2024/825)", styles["cover_center"]))
    elements.append(Spacer(1, 10 * mm))
    elements.append(Paragraph(f"<b>{audit.company_name}</b>", styles["cover_center"]))
    elements.append(Paragraph(f"Secteur : {audit.sector}", styles["cover_center"]))
    elements.append(Spacer(1, 10 * mm))

    score_style = ParagraphStyle("score", parent=styles["cover_score"], textColor=risk_color, fontSize=40, spaceAfter=12)
    elements.append(Paragraph(f"{audit.global_score}/100", score_style))
    elements.append(Spacer(1, 6 * mm))

    risk_text = f"Risque {audit.risk_level or '—'}"
    risk_style = ParagraphStyle("risk", parent=styles["cover_center"], textColor=risk_color, fontSize=16, spaceAfter=8)
    elements.append(Paragraph(f"<b>{risk_text}</b>", risk_style))
    elements.append(Spacer(1, 25 * mm))
    elements.append(Paragraph(
        f"Audit réalisé le {_format_date(audit.completed_at)} par {partner.company_name}",
        styles["cover_small"],
    ))
    elements.append(NextPageTemplate("content"))
    elements.append(PageBreak())
    return elements


def _summary_elements(audit: Audit, styles: dict) -> list:
    elements = []
    elements.append(Paragraph("1. Synthèse exécutive", styles["h1"]))

    total = audit.total_claims or 1
    data = [
        ["Allégations", "Conformes", "À risque", "Non conformes"],
        [
            str(audit.total_claims),
            f"{audit.conforming_claims} ({round(audit.conforming_claims / total * 100)}%)",
            f"{audit.at_risk_claims} ({round(audit.at_risk_claims / total * 100)}%)",
            f"{audit.non_conforming_claims} ({round(audit.non_conforming_claims / total * 100)}%)",
        ],
    ]
    page_width = A4[0] - 40 * mm
    t = Table(data, colWidths=[page_width / 4] * 4)
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1B5E20")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTSIZE", (0, 0), (-1, -1), 10),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.lightgrey),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
    ]))
    elements.append(t)
    elements.append(Spacer(1, 4 * mm))
    elements.append(Paragraph(
        f"Score global : <b>{audit.global_score}/100</b> — Risque <b>{audit.risk_level}</b>. "
        f"{_summary_phrase(audit.risk_level)}",
        styles["body"],
    ))
    return elements


def _claims_detail_elements(claims: list, styles: dict) -> list:
    elements = []
    elements.append(Paragraph("2. Détail des allégations", styles["h1"]))

    for i, claim in enumerate(claims, 1):
        verdict = VERDICT_LABELS.get(claim.overall_verdict or "", "—")
        support = SUPPORT_LABELS.get(claim.support_type, claim.support_type)
        scope = "Entreprise" if claim.scope == "entreprise" else "Produit"

        elements.append(Paragraph(f"Allégation #{i} — {verdict}", styles["h2"]))
        elements.append(Paragraph(f"<i>« {claim.claim_text} »</i>", styles["italic"]))
        elements.append(Paragraph(f"Support : {support} | Portée : {scope}", styles["small"]))
        elements.append(Spacer(1, 2 * mm))

        # Tableau des 6 critères
        data = [[
            Paragraph("<b>Critère</b>", styles["small"]),
            Paragraph("<b>Verdict</b>", styles["small"]),
            Paragraph("<b>Explication</b>", styles["small"]),
            Paragraph("<b>Recommandation</b>", styles["small"]),
        ]]
        sorted_results = sorted(
            claim.results,
            key=lambda r: CRITERION_ORDER.index(r.criterion) if r.criterion in CRITERION_ORDER else 99,
        )
        for r in sorted_results:
            data.append([
                Paragraph(CRITERION_LABELS.get(r.criterion, r.criterion), styles["small"]),
                Paragraph(VERDICT_LABELS.get(r.verdict, r.verdict), styles["small"]),
                Paragraph(r.explanation or "", styles["small"]),
                Paragraph(r.recommendation or "—", styles["small"]),
            ])

        page_width = A4[0] - 40 * mm
        col_widths = [page_width * 0.17, page_width * 0.13, page_width * 0.40, page_width * 0.30]
        t = Table(data, colWidths=col_widths, repeatRows=1)
        t.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1B5E20")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTSIZE", (0, 0), (-1, 0), 9),
            ("FONTSIZE", (0, 1), (-1, -1), 8),
            ("ALIGN", (0, 0), (-1, 0), "LEFT"),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.lightgrey),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ("TOPPADDING", (0, 0), (-1, -1), 5),
            ("LEFTPADDING", (0, 0), (-1, -1), 4),
            ("RIGHTPADDING", (0, 0), (-1, -1), 4),
        ]))
        elements.append(t)
        elements.append(Spacer(1, 6 * mm))

    return elements


def _correction_plan_elements(claims: list, styles: dict) -> list:
    elements = []
    elements.append(Paragraph("3. Plan de correction priorisé", styles["h1"]))

    actions = []
    for claim in claims:
        if claim.overall_verdict == "conforme":
            continue
        for r in claim.results:
            if r.verdict in ("non_conforme", "risque") and r.recommendation:
                priority = "Critique" if r.verdict == "non_conforme" else "Élevé"
                actions.append((priority, claim.claim_text[:60] + "…", CRITERION_LABELS.get(r.criterion, r.criterion), r.recommendation))

    if not actions:
        elements.append(Paragraph("Aucune action corrective nécessaire.", styles["body"]))
        return elements

    # Trier critique en premier
    actions.sort(key=lambda a: 0 if a[0] == "Critique" else 1)

    data = [[
        Paragraph("<b>Priorité</b>", styles["small"]),
        Paragraph("<b>Allégation</b>", styles["small"]),
        Paragraph("<b>Critère</b>", styles["small"]),
        Paragraph("<b>Action corrective</b>", styles["small"]),
    ]]
    for a in actions:
        data.append([
            Paragraph(a[0], styles["small"]),
            Paragraph(a[1], styles["small"]),
            Paragraph(a[2], styles["small"]),
            Paragraph(a[3], styles["small"]),
        ])

    page_width = A4[0] - 40 * mm
    t = Table(data, colWidths=[page_width * 0.12, page_width * 0.25, page_width * 0.18, page_width * 0.45], repeatRows=1)
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1B5E20")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.lightgrey),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
    ]))
    elements.append(t)
    return elements


def _labels_checklist_elements(claims: list, styles: dict) -> list:
    to_remove = []
    to_keep = []
    for claim in claims:
        if not claim.has_label:
            continue
        name = claim.label_name or "Label non précisé"
        if claim.label_is_certified:
            to_keep.append(name)
        else:
            to_remove.append(name)

    if not to_remove and not to_keep:
        return []

    elements = []
    elements.append(Paragraph("4. Checklist labels", styles["h1"]))
    if to_remove:
        elements.append(Paragraph("Labels à retirer (auto-décernés) :", styles["body"]))
        for name in to_remove:
            elements.append(Paragraph(f"  • {name}", styles["body"]))
    if to_keep:
        elements.append(Paragraph("Labels conformes à conserver :", styles["body"]))
        for name in to_keep:
            elements.append(Paragraph(f"  • {name}", styles["body"]))
    return elements


def _references_elements(styles: dict) -> list:
    elements = []
    elements.append(Paragraph("5. Références réglementaires", styles["h1"]))
    page_width = A4[0] - 40 * mm
    data = [
        [Paragraph("<b>Texte</b>", styles["small"]), Paragraph("<b>Référence</b>", styles["small"]), Paragraph("<b>Objet</b>", styles["small"])],
        [Paragraph("Directive EmpCo", styles["small"]), Paragraph("EU 2024/825", styles["small"]), Paragraph("Interdiction allégations trompeuses, labels auto-décernés, neutralité carbone par compensation", styles["small"])],
        [Paragraph("Loi AGEC", styles["small"]), Paragraph("Loi n° 2020-105", styles["small"]), Paragraph("Interdiction mentions « biodégradable » et « respectueux de l'environnement » (Art. 13)", styles["small"])],
        [Paragraph("Guide ADEME 2025", styles["small"]), Paragraph("Recommandations", styles["small"]), Paragraph("Bonnes pratiques de communication environnementale", styles["small"])],
        [Paragraph("Code de la consommation", styles["small"]), Paragraph("Art. L121-1+", styles["small"]), Paragraph("Pratiques commerciales trompeuses", styles["small"])],
    ]
    t = Table(data, colWidths=[page_width * 0.20, page_width * 0.20, page_width * 0.60], repeatRows=1)
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1B5E20")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.lightgrey),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
    ]))
    elements.append(t)
    return elements


def _disclaimer_elements(partner: Partner, styles: dict) -> list:
    elements = []
    elements.append(Spacer(1, 10 * mm))
    elements.append(Paragraph("Avertissement", styles["h1"]))
    elements.append(Paragraph(
        "Ce rapport est un outil d'aide à la conformité et ne constitue pas un conseil juridique. "
        "Il est recommandé de consulter un avocat spécialisé pour toute question relative à la "
        "conformité réglementaire de vos communications environnementales.",
        styles["disclaimer"],
    ))
    contact_parts = [p for p in [partner.company_name, partner.contact_name, partner.contact_phone, partner.email] if p]
    elements.append(Spacer(1, 4 * mm))
    elements.append(Paragraph(" — ".join(contact_parts), styles["disclaimer"]))
    return elements


# ---------------------------------------------------------------------------
# Point d'entrée principal
# ---------------------------------------------------------------------------

def generate_audit_pdf(audit: Audit, partner: Partner) -> str:
    """
    Génère le rapport PDF complet et le sauvegarde sur disque.

    Returns:
        Nom du fichier PDF généré.
    """
    claims = sorted(audit.claims, key=lambda c: c.created_at)
    primary = _hex(partner.brand_primary_color)
    secondary = _hex(partner.brand_secondary_color, "#2E7D32")
    styles = _build_styles(primary, secondary)

    # Créer le dossier de stockage
    storage_path = Path(settings.PDF_STORAGE_PATH)
    storage_path.mkdir(parents=True, exist_ok=True)

    filename = f"greenaudit_{audit.id}.pdf"
    filepath = str(storage_path / filename)

    doc = _build_doc(filepath, partner)

    elements = []
    elements.extend(_cover_elements(audit, partner, styles))
    elements.extend(_summary_elements(audit, styles))
    elements.extend(_claims_detail_elements(claims, styles))
    elements.extend(_correction_plan_elements(claims, styles))
    elements.extend(_labels_checklist_elements(claims, styles))
    elements.extend(_references_elements(styles))
    elements.extend(_disclaimer_elements(partner, styles))

    doc.build(elements)

    return filename
