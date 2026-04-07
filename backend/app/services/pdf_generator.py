"""
Génération du rapport PDF white-label via ReportLab (pure Python, pas de dépendance système).
Version améliorée : jauge visuelle, radar chart, alertes, échéances, risque financier, barres de progression.
"""

from __future__ import annotations

import hashlib
import math
import os
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    BaseDocTemplate,
    Flowable,
    Frame,
    KeepTogether,
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
from app.models.organization import Organization as Partner


# ---------------------------------------------------------------------------
# Constantes
# ---------------------------------------------------------------------------

RISK_COLORS: Dict[str, colors.Color] = {
    "faible": colors.HexColor("#16A34A"),
    "modere": colors.HexColor("#CA8A04"),
    "eleve": colors.HexColor("#EA580C"),
    "critique": colors.HexColor("#DC2626"),
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
    "legal_requirement": "Exigences légales",
}

CRITERION_ORDER = [
    "specificity", "compensation", "labels",
    "proportionality", "future_commitment", "justification",
    "legal_requirement",
]

# Axes du radar (sous-ensemble sans legal_requirement)
RADAR_CRITERIA = [
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


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

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


RISK_LABELS: Dict[str, str] = {
    "faible": "faible",
    "modere": "modéré",
    "eleve": "élevé",
    "critique": "critique",
}


def _risk_label(risk_level: Optional[str]) -> str:
    """Retourne le niveau de risque avec accents."""
    return RISK_LABELS.get(risk_level or "", risk_level or "—")


def _score_color(score: float) -> colors.Color:
    """Retourne la couleur correspondant au score."""
    if score <= 25:
        return colors.HexColor("#DC2626")
    elif score <= 50:
        return colors.HexColor("#EA580C")
    elif score <= 75:
        return colors.HexColor("#CA8A04")
    else:
        return colors.HexColor("#16A34A")


def _count_issues(claim) -> int:
    """Compte le nombre de non-conformités + risques d'une claim."""
    count = 0
    for r in claim.results:
        if r.verdict in ("non_conforme", "risque"):
            count += 1
    return count


# ---------------------------------------------------------------------------
# Custom Flowables
# ---------------------------------------------------------------------------

class GaugeFlowable(Flowable):
    """Jauge semi-circulaire (speedometer) avec aiguille."""

    def __init__(self, score: float, width: float = 200, height: float = 130):
        super().__init__()
        self.score = score or 0
        self.width = width
        self.height = height

    def draw(self):
        c = self.canv
        cx = self.width / 2
        cy = 30  # Centre de l'arc, un peu au-dessus du bas

        radius = 80
        arc_width = 18

        # Dessiner l'arc de fond (gris clair)
        c.saveState()
        c.setStrokeColor(colors.HexColor("#E5E7EB"))
        c.setLineWidth(arc_width)
        c.setLineCap(1)
        # Arc de 180 à 0 degrés (demi-cercle supérieur)
        # ReportLab arc: x1, y1, x2, y2, startAngle, extent
        x1 = cx - radius
        y1 = cy - radius
        x2 = cx + radius
        y2 = cy + radius
        c.arc(x1, y1, x2, y2, 0, 180)
        c.restoreState()

        # Segments colorés de l'arc
        segments = [
            (0, 45, "#DC2626"),      # 0-25 : rouge
            (45, 45, "#EA580C"),     # 25-50 : orange
            (90, 45, "#CA8A04"),     # 50-75 : jaune
            (135, 45, "#16A34A"),    # 75-100 : vert
        ]
        for start, extent, hex_color in segments:
            c.saveState()
            c.setStrokeColor(colors.HexColor(hex_color))
            c.setLineWidth(arc_width)
            c.setLineCap(1)
            c.arc(x1, y1, x2, y2, start, extent)
            c.restoreState()

        # Aiguille
        angle_deg = 180 - (self.score / 100 * 180)  # 180=gauche(0), 0=droite(100)
        angle_rad = math.radians(angle_deg)
        needle_len = radius - 15
        nx = cx + needle_len * math.cos(angle_rad)
        ny = cy + needle_len * math.sin(angle_rad)

        c.saveState()
        c.setStrokeColor(colors.HexColor("#1F2937"))
        c.setLineWidth(2.5)
        c.line(cx, cy, nx, ny)
        # Cercle central
        c.setFillColor(colors.HexColor("#1F2937"))
        c.circle(cx, cy, 5, fill=1, stroke=0)
        c.restoreState()

        # Score au centre
        score_color = _score_color(self.score)
        c.saveState()
        c.setFont("Helvetica-Bold", 28)
        c.setFillColor(score_color)
        c.drawCentredString(cx, cy + 30, f"{self.score:.0f}")
        c.setFont("Helvetica", 10)
        c.setFillColor(colors.HexColor("#6B7280"))
        c.drawCentredString(cx, cy + 18, "/ 100")
        c.restoreState()

        # Étiquettes min/max
        c.saveState()
        c.setFont("Helvetica", 7)
        c.setFillColor(colors.HexColor("#9CA3AF"))
        c.drawString(cx - radius - 5, cy - 8, "0")
        c.drawRightString(cx + radius + 5, cy - 8, "100")
        c.restoreState()


class SummaryDotsFlowable(Flowable):
    """Pastilles colorées résumé : X non conformes, Y à risque, Z conformes."""

    def __init__(self, conformes: int, risque: int, non_conformes: int, width: float = 400):
        super().__init__()
        self.conformes = conformes
        self.risque = risque
        self.non_conformes = non_conformes
        self.width = width
        self.height = 24

    def draw(self):
        c = self.canv
        items = [
            (colors.HexColor("#DC2626"), f"{self.non_conformes} non conforme{'s' if self.non_conformes > 1 else ''}"),
            (colors.HexColor("#CA8A04"), f"{self.risque} à risque"),
            (colors.HexColor("#16A34A"), f"{self.conformes} conforme{'s' if self.conformes > 1 else ''}"),
        ]
        x = 0
        spacing = self.width / 3
        for i, (color, text) in enumerate(items):
            cx = x + spacing * i + spacing / 2
            cy = self.height / 2
            # Cercle
            c.saveState()
            c.setFillColor(color)
            c.circle(cx - 30, cy, 5, fill=1, stroke=0)
            # Texte
            c.setFont("Helvetica", 9)
            c.setFillColor(colors.HexColor("#374151"))
            c.drawString(cx - 22, cy - 3, text)
            c.restoreState()


class RadarChartFlowable(Flowable):
    """Radar chart (spider chart) pur ReportLab."""

    def __init__(self, scores: Dict[str, float], width: float = 280, height: float = 260):
        super().__init__()
        self.scores = scores
        self.width = width
        self.height = height

    def draw(self):
        c = self.canv
        cx = self.width / 2
        cy = self.height / 2 + 10
        radius = 100
        axes = RADAR_CRITERIA
        n = len(axes)

        if n == 0:
            return

        # Angle pour chaque axe (départ en haut, sens horaire)
        angles = []
        for i in range(n):
            a = math.pi / 2 - (2 * math.pi * i / n)
            angles.append(a)

        # Grilles concentriques (20, 40, 60, 80, 100%)
        for level in [0.2, 0.4, 0.6, 0.8, 1.0]:
            c.saveState()
            c.setStrokeColor(colors.HexColor("#E5E7EB"))
            c.setLineWidth(0.5)
            path = c.beginPath()
            for i, a in enumerate(angles):
                px = cx + radius * level * math.cos(a)
                py = cy + radius * level * math.sin(a)
                if i == 0:
                    path.moveTo(px, py)
                else:
                    path.lineTo(px, py)
            path.close()
            c.drawPath(path, fill=0, stroke=1)
            c.restoreState()

        # Axes
        c.saveState()
        c.setStrokeColor(colors.HexColor("#D1D5DB"))
        c.setLineWidth(0.5)
        for a in angles:
            c.line(cx, cy, cx + radius * math.cos(a), cy + radius * math.sin(a))
        c.restoreState()

        # Polygone des données
        values = []
        for criterion in axes:
            val = self.scores.get(criterion)
            if val is None:
                values.append(0.5)  # Si pas de données, milieu
            else:
                values.append(val / 100.0)

        c.saveState()
        # Remplissage
        fill_color = colors.Color(0.10, 0.40, 0.13, alpha=0.2)  # vert semi-transparent
        c.setFillColor(fill_color)
        c.setStrokeColor(colors.HexColor("#1B5E20"))
        c.setLineWidth(2)
        path = c.beginPath()
        for i, (a, v) in enumerate(zip(angles, values)):
            px = cx + radius * v * math.cos(a)
            py = cy + radius * v * math.sin(a)
            if i == 0:
                path.moveTo(px, py)
            else:
                path.lineTo(px, py)
        path.close()
        c.drawPath(path, fill=1, stroke=1)
        c.restoreState()

        # Points sur les sommets
        for a, v in zip(angles, values):
            px = cx + radius * v * math.cos(a)
            py = cy + radius * v * math.sin(a)
            c.saveState()
            c.setFillColor(colors.HexColor("#1B5E20"))
            c.circle(px, py, 3, fill=1, stroke=0)
            c.restoreState()

        # Labels des axes
        c.saveState()
        c.setFont("Helvetica", 7)
        c.setFillColor(colors.HexColor("#374151"))
        label_offset = 16
        for i, a in enumerate(angles):
            criterion = axes[i]
            label = CRITERION_LABELS.get(criterion, criterion)
            lx = cx + (radius + label_offset) * math.cos(a)
            ly = cy + (radius + label_offset) * math.sin(a)

            # Ajuster l'alignement selon la position
            if abs(math.cos(a)) < 0.1:  # En haut ou en bas
                c.drawCentredString(lx, ly - 3, label)
            elif math.cos(a) > 0:  # À droite
                c.drawString(lx, ly - 3, label)
            else:  # À gauche
                c.drawRightString(lx, ly - 3, label)
        c.restoreState()

        # Valeurs en %
        c.saveState()
        c.setFont("Helvetica-Bold", 7)
        c.setFillColor(colors.HexColor("#1B5E20"))
        for i, (a, v) in enumerate(zip(angles, values)):
            score_val = v * 100
            px = cx + (radius * v + 12) * math.cos(a)
            py = cy + (radius * v + 12) * math.sin(a)
            c.drawCentredString(px, py - 2, f"{score_val:.0f}%")
        c.restoreState()


class ProgressBarFlowable(Flowable):
    """Barre de progression horizontale segmentée par verdict."""

    def __init__(self, conformes: int, risque: int, non_conformes: int, na: int,
                 width: float = 400, height: float = 14):
        super().__init__()
        self.conformes = conformes
        self.risque = risque
        self.non_conformes = non_conformes
        self.na = na
        self.total = conformes + risque + non_conformes + na
        self.width = width
        self.height = height

    def draw(self):
        if self.total == 0:
            return
        c = self.canv
        bar_height = 10
        y = (self.height - bar_height) / 2
        x = 0

        segments = [
            (self.conformes, "#16A34A"),
            (self.risque, "#CA8A04"),
            (self.non_conformes, "#DC2626"),
            (self.na, "#D1D5DB"),
        ]
        for count, hex_color in segments:
            if count == 0:
                continue
            seg_width = (count / self.total) * self.width
            c.saveState()
            c.setFillColor(colors.HexColor(hex_color))
            c.roundRect(x, y, seg_width, bar_height, 2, fill=1, stroke=0)
            c.restoreState()
            x += seg_width

        # Légende compacte à droite
        legend_x = self.width + 8
        c.saveState()
        c.setFont("Helvetica", 6)
        c.setFillColor(colors.HexColor("#6B7280"))
        parts = []
        if self.conformes:
            parts.append(f"{self.conformes}C")
        if self.risque:
            parts.append(f"{self.risque}R")
        if self.non_conformes:
            parts.append(f"{self.non_conformes}NC")
        if self.na:
            parts.append(f"{self.na}N/A")
        c.drawString(legend_x, y + 1, " | ".join(parts))
        c.restoreState()


class AlertBoxFlowable(Flowable):
    """Encadré alerte rouge pour allégations à risque maximal."""

    def __init__(self, claim_text: str, issues: list, width: float = 480):
        super().__init__()
        self.claim_text = claim_text
        self.issues = issues
        self.width = width
        # Calculer la hauteur approximative
        self.height = 60 + len(issues) * 14

    def draw(self):
        c = self.canv

        # Background rouge clair + bordure rouge
        c.saveState()
        c.setFillColor(colors.HexColor("#FEF2F2"))
        c.setStrokeColor(colors.HexColor("#DC2626"))
        c.setLineWidth(2)
        c.roundRect(0, 0, self.width, self.height, 4, fill=1, stroke=1)
        c.restoreState()

        # Icône triangle d'alerte
        tx = 15
        ty = self.height - 22
        c.saveState()
        c.setFillColor(colors.HexColor("#DC2626"))
        path = c.beginPath()
        path.moveTo(tx, ty - 10)
        path.lineTo(tx + 7, ty + 4)
        path.lineTo(tx - 7, ty + 4)
        path.close()
        c.drawPath(path, fill=1, stroke=0)
        # Point d'exclamation dans le triangle
        c.setFillColor(colors.white)
        c.setFont("Helvetica-Bold", 7)
        c.drawCentredString(tx, ty - 5, "!")
        c.restoreState()

        # Titre
        c.saveState()
        c.setFont("Helvetica-Bold", 9)
        c.setFillColor(colors.HexColor("#991B1B"))
        n_issues = len(self.issues)
        c.drawString(30, self.height - 20, f"Allégation à risque maximal — {n_issues} problèmes détectés")
        c.restoreState()

        # Texte de la claim (tronqué)
        c.saveState()
        c.setFont("Helvetica-Oblique", 8)
        c.setFillColor(colors.HexColor("#7F1D1D"))
        claim_display = self.claim_text[:90] + ("..." if len(self.claim_text) > 90 else "")
        c.drawString(15, self.height - 36, f"« {claim_display} »")
        c.restoreState()

        # Liste des problèmes
        c.saveState()
        c.setFont("Helvetica", 8)
        c.setFillColor(colors.HexColor("#991B1B"))
        y = self.height - 52
        for issue in self.issues:
            text = issue[:100] + ("..." if len(issue) > 100 else "")
            c.drawString(25, y, f"• {text}")
            y -= 14
        c.restoreState()


# ---------------------------------------------------------------------------
# Styles
# ---------------------------------------------------------------------------

def _build_styles(primary: colors.Color, secondary: colors.Color):
    ss = getSampleStyleSheet()
    styles = {
        "title": ParagraphStyle("title", parent=ss["Title"], fontSize=22, textColor=primary, spaceAfter=6),
        "h1": ParagraphStyle("h1", parent=ss["Heading1"], fontSize=16, textColor=primary, spaceAfter=8, spaceBefore=16),
        "h2": ParagraphStyle("h2", parent=ss["Heading2"], fontSize=13, textColor=secondary, spaceAfter=6, spaceBefore=12),
        "h2_alert": ParagraphStyle("h2_alert", parent=ss["Heading2"], fontSize=13, textColor=colors.HexColor("#DC2626"), spaceAfter=6, spaceBefore=12),
        "body": ParagraphStyle("body", parent=ss["Normal"], fontSize=10, leading=14, spaceAfter=4),
        "small": ParagraphStyle("small", parent=ss["Normal"], fontSize=8, textColor=colors.gray, spaceAfter=2),
        "italic": ParagraphStyle("italic", parent=ss["Normal"], fontSize=10, leading=14, textColor=colors.HexColor("#555555"), spaceAfter=4),
        "bold": ParagraphStyle("bold", parent=ss["Normal"], fontSize=10, leading=14, spaceAfter=4),
        "cover_score": ParagraphStyle("cover_score", parent=ss["Title"], fontSize=48, alignment=1, spaceAfter=4),
        "cover_center": ParagraphStyle("cover_center", parent=ss["Normal"], fontSize=14, alignment=1, spaceAfter=4),
        "cover_small": ParagraphStyle("cover_small", parent=ss["Normal"], fontSize=10, alignment=1, textColor=colors.gray, spaceAfter=4),
        "disclaimer": ParagraphStyle("disclaimer", parent=ss["Normal"], fontSize=8, textColor=colors.gray, leading=11),
        "alert_body": ParagraphStyle("alert_body", parent=ss["Normal"], fontSize=9, textColor=colors.HexColor("#991B1B"), leading=12),
        "deadline_footer": ParagraphStyle("deadline_footer", parent=ss["Normal"], fontSize=9, textColor=colors.HexColor("#EA580C"), leading=12, spaceBefore=6),
    }
    return styles


# ---------------------------------------------------------------------------
# Page templates avec header/footer
# ---------------------------------------------------------------------------

def _build_doc(filepath: str, partner: Partner, is_starter: bool = False) -> BaseDocTemplate:
    primary = _hex(partner.brand_primary_color) if not is_starter else colors.HexColor("#1B5E20")
    company = "GreenAudit" if is_starter else (partner.name or "")
    email = "contact@green-audit.fr" if is_starter else (partner.contact_email or "")
    phone = "" if is_starter else (partner.contact_phone or "")

    def _header_footer(canvas, doc):
        canvas.saveState()
        canvas.setFont("Helvetica", 8)
        canvas.setFillColor(colors.gray)
        canvas.drawString(20 * mm, A4[1] - 12 * mm, company)
        canvas.setStrokeColor(primary)
        canvas.setLineWidth(0.5)
        canvas.line(20 * mm, A4[1] - 14 * mm, A4[0] - 20 * mm, A4[1] - 14 * mm)
        footer_parts = [p for p in [company, phone, email] if p]
        footer_text = " — ".join(footer_parts)
        canvas.setFont("Helvetica", 7)
        canvas.setFillColor(colors.gray)
        canvas.drawCentredString(A4[0] / 2, 12 * mm, footer_text)
        canvas.drawRightString(A4[0] - 20 * mm, 12 * mm, f"Page {doc.page}")
        canvas.restoreState()

    def _cover_footer(canvas, doc):
        pass

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
# Sections du rapport
# ---------------------------------------------------------------------------

def _cover_elements(audit: Audit, partner: Partner, styles: dict, is_starter: bool = False) -> list:
    """Page 1 : page de garde avec jauge et pastilles résumé."""
    elements = []
    elements.append(Spacer(1, 40 * mm))
    elements.append(Paragraph("Rapport d'audit anti-greenwashing", styles["title"]))
    elements.append(Paragraph("Directive EmpCo (EU 2024/825)", styles["cover_center"]))
    elements.append(Spacer(1, 8 * mm))
    elements.append(Paragraph(f"<b>{audit.company_name}</b>", styles["cover_center"]))
    elements.append(Paragraph(f"Secteur : {audit.sector}", styles["cover_center"]))
    elements.append(Spacer(1, 8 * mm))

    # Jauge semi-circulaire
    score = float(audit.global_score or 0)
    gauge = GaugeFlowable(score, width=200, height=130)
    # Centrer la jauge via un tableau
    gauge_table = Table([[gauge]], colWidths=[200])
    gauge_table.setStyle(TableStyle([("ALIGN", (0, 0), (-1, -1), "CENTER")]))
    elements.append(gauge_table)

    # Niveau de risque texte
    risk_color = RISK_COLORS.get(audit.risk_level or "", colors.gray)
    risk_text = f"Risque {_risk_label(audit.risk_level)}"
    risk_style = ParagraphStyle("risk", parent=styles["cover_center"], textColor=risk_color, fontSize=14, spaceAfter=6)
    elements.append(Paragraph(f"<b>{risk_text}</b>", risk_style))
    elements.append(Spacer(1, 6 * mm))

    # Pastilles résumé
    dots = SummaryDotsFlowable(
        conformes=audit.conforming_claims or 0,
        risque=audit.at_risk_claims or 0,
        non_conformes=audit.non_conforming_claims or 0,
        width=400,
    )
    dots_table = Table([[dots]], colWidths=[400])
    dots_table.setStyle(TableStyle([("ALIGN", (0, 0), (-1, -1), "CENTER")]))
    elements.append(dots_table)

    # Bloc progression post-correction (si applicable)
    corrected = _compute_corrected_score(audit)
    if corrected:
        elements.append(Spacer(1, 4 * mm))
        initial_score = float(audit.global_score or 0)
        correction_style = ParagraphStyle(
            "correction_cover",
            parent=styles["cover_small"],
            fontSize=11,
            textColor=colors.HexColor("#16A34A"),
        )
        elements.append(Paragraph(
            f"Score initial : <b>{initial_score:.0f}/100</b> → Score après {corrected['corrected_count']} correction(s) : "
            f"<b>{corrected['corrected_score']}/100</b> (risque {_risk_label(corrected['corrected_risk'])})",
            correction_style,
        ))

    elements.append(Spacer(1, 8 * mm))

    # Logo en bas de page de garde
    from io import BytesIO
    from reportlab.platypus import Image as RLImage
    from reportlab.lib.utils import ImageReader

    def _logo_elements(img_reader, max_w_mm=60, max_h_mm=50):
        """Retourne (img, col_w) en respectant le ratio, dans les limites max."""
        iw, ih = img_reader.getSize()
        max_w = max_w_mm * mm
        max_h = max_h_mm * mm
        ratio = min(max_w / iw, max_h / ih)
        w, h = iw * ratio, ih * ratio
        img = RLImage(img_reader, width=w, height=h)
        tbl = Table([[img]], colWidths=[w])
        tbl.setStyle(TableStyle([("ALIGN", (0, 0), (-1, -1), "CENTER")]))
        return tbl

    greenaudit_logo = Path(__file__).parent.parent / "static" / "logo.png"
    logo_added = False

    if not is_starter and partner.logo_data:
        try:
            img_reader = ImageReader(BytesIO(partner.logo_data))
            elements.append(_logo_elements(img_reader))
            elements.append(Spacer(1, 3 * mm))
            logo_added = True
        except Exception:
            pass

    if not logo_added and greenaudit_logo.exists():
        try:
            img_reader = ImageReader(str(greenaudit_logo))
            elements.append(_logo_elements(img_reader))
            elements.append(Spacer(1, 3 * mm))
        except Exception:
            pass

    elements.append(Paragraph(
        f"Audit réalisé le {_format_date(audit.completed_at)} par {'GreenAudit' if is_starter else partner.name}",
        styles["cover_small"],
    ))
    elements.append(NextPageTemplate("content"))
    elements.append(PageBreak())
    return elements


def _summary_elements(audit: Audit, styles: dict) -> list:
    """Section synthèse exécutive."""
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
        f"Score global : <b>{audit.global_score}/100</b> — Risque <b>{_risk_label(audit.risk_level)}</b>. "
        f"{_summary_phrase(audit.risk_level)}",
        styles["body"],
    ))

    # Bloc progression post-correction
    corrected = _compute_corrected_score(audit)
    if corrected:
        elements.append(Spacer(1, 4 * mm))

        prog_data = [
            ["", "Score", "Niveau de risque", "Allégations conformes"],
            [
                "Audit initial",
                f"{float(audit.global_score or 0):.0f}/100",
                _risk_label(audit.risk_level).capitalize(),
                f"{audit.conforming_claims} / {audit.total_claims}",
            ],
            [
                f"Après {corrected['corrected_count']} correction(s)",
                f"{corrected['corrected_score']}/100",
                _risk_label(corrected["corrected_risk"]).capitalize(),
                f"{corrected['corrected_conforming']} / {audit.total_claims}",
            ],
        ]
        page_width = A4[0] - 40 * mm
        prog_table = Table(prog_data, colWidths=[page_width * 0.30, page_width * 0.20, page_width * 0.25, page_width * 0.25])
        prog_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#E8F5E9")),
            ("FONTSIZE", (0, 0), (-1, -1), 9),
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("ALIGN", (0, 0), (0, -1), "LEFT"),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.lightgrey),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ("TOPPADDING", (0, 0), (-1, -1), 5),
            ("TEXTCOLOR", (1, 2), (1, 2), colors.HexColor("#16A34A")),
            ("FONTNAME", (1, 2), (1, 2), "Helvetica-Bold"),
        ]))
        elements.append(Paragraph("<b>Progression après corrections</b>", styles["body"]))
        elements.append(prog_table)
        elements.append(Spacer(1, 2 * mm))
        elements.append(Paragraph(
            "Ce score est indicatif. Il reflète la progression déclarée par l'organisation "
            "et ne remplace pas un nouvel audit de vérification.",
            styles["disclaimer"],
        ))

    return elements


def _compute_corrected_score(audit: Audit) -> Optional[dict]:
    """
    Calcule un score indicatif post-correction.
    Les allégations marquées is_corrected=True sont traitées comme conformes.
    Retourne None si aucune allégation n'est corrigée.
    """
    claims = audit.claims or []
    corrected_count = sum(1 for c in claims if getattr(c, "is_corrected", False))
    if corrected_count == 0:
        return None

    total = len(claims)
    if total == 0:
        return None

    # Score actuel
    conforming = audit.conforming_claims or 0
    at_risk = audit.at_risk_claims or 0

    # Score post-correction : les allégations corrigées qui étaient NC ou risque deviennent conformes
    # On recalcule en ajoutant les corrigées aux conformes
    corrected_conforming = conforming
    corrected_at_risk = at_risk
    for claim in claims:
        if not getattr(claim, "is_corrected", False):
            continue
        verdict = claim.overall_verdict
        if verdict == "non_conforme":
            corrected_conforming += 1
        elif verdict == "risque":
            corrected_conforming += 1
            corrected_at_risk = max(0, corrected_at_risk - 1)

    corrected_nc = total - corrected_conforming - corrected_at_risk
    corrected_nc = max(0, corrected_nc)

    corrected_score = round(
        (corrected_conforming * 100 + corrected_at_risk * 50) / total
    )

    if corrected_score >= 80:
        corrected_risk = "faible"
    elif corrected_score >= 60:
        corrected_risk = "modere"
    elif corrected_score >= 40:
        corrected_risk = "eleve"
    else:
        corrected_risk = "critique"

    return {
        "corrected_count": corrected_count,
        "corrected_score": corrected_score,
        "corrected_risk": corrected_risk,
        "corrected_conforming": corrected_conforming,
    }


def _compute_radar_scores(claims: list) -> Dict[str, float]:
    """Calcule le score moyen par critère pour le radar chart."""
    scores_by_criterion: Dict[str, List[float]] = {c: [] for c in RADAR_CRITERIA}
    for claim in claims:
        for r in claim.results:
            if r.criterion not in scores_by_criterion:
                continue
            if r.verdict == "non_applicable":
                continue
            if r.verdict == "conforme":
                scores_by_criterion[r.criterion].append(100)
            elif r.verdict == "risque":
                scores_by_criterion[r.criterion].append(50)
            else:  # non_conforme
                scores_by_criterion[r.criterion].append(0)

    result = {}
    for criterion, vals in scores_by_criterion.items():
        if vals:
            result[criterion] = sum(vals) / len(vals)
        # Si pas de données, on n'inclut pas dans le dict
    return result


def _radar_elements(claims: list, styles: dict) -> list:
    """Section radar chart par critère."""
    elements = []
    elements.append(Paragraph("2. Conformité par critère", styles["h1"]))

    scores = _compute_radar_scores(claims)
    if not scores:
        elements.append(Paragraph("Données insuffisantes pour générer le graphique.", styles["body"]))
        return elements

    radar = RadarChartFlowable(scores, width=300, height=280)
    radar_table = Table([[radar]], colWidths=[300])
    radar_table.setStyle(TableStyle([("ALIGN", (0, 0), (-1, -1), "CENTER")]))
    elements.append(radar_table)
    elements.append(Spacer(1, 4 * mm))

    # Légende
    legend_text = "Score par critère : 100% = tous conformes, 50% = risque, 0% = non conforme. Les critères N/A sont exclus."
    elements.append(Paragraph(legend_text, styles["small"]))
    return elements


def _claims_detail_elements(claims: list, styles: dict, is_starter: bool = False) -> list:
    """Section détail des allégations avec barres de progression et alertes."""
    elements = []
    elements.append(Paragraph("3. Détail des allégations", styles["h1"]))

    for i, claim in enumerate(claims, 1):
        verdict = VERDICT_LABELS.get(claim.overall_verdict or "", "—")
        support = SUPPORT_LABELS.get(claim.support_type, claim.support_type)
        scope = "Entreprise" if claim.scope == "entreprise" else "Produit"

        # Compter les verdicts pour la barre de progression
        c_conf = sum(1 for r in claim.results if r.verdict == "conforme")
        c_risk = sum(1 for r in claim.results if r.verdict == "risque")
        c_nc = sum(1 for r in claim.results if r.verdict == "non_conforme")
        c_na = sum(1 for r in claim.results if r.verdict == "non_applicable")

        claim_elements = []

        # Vérifier si c'est une allégation à risque maximal (3+ problèmes)
        n_issues = _count_issues(claim)
        is_alert = n_issues >= 3

        if is_alert:
            claim_elements.append(Paragraph(f"Allégation #{i} — {verdict}", styles["h2_alert"]))
        else:
            claim_elements.append(Paragraph(f"Allégation #{i} — {verdict}", styles["h2"]))

        claim_elements.append(Paragraph(f"<i>« {claim.claim_text} »</i>", styles["italic"]))
        claim_elements.append(Paragraph(f"Support : {support} | Portée : {scope}", styles["small"]))
        claim_elements.append(Spacer(1, 2 * mm))

        # Barre de progression
        bar = ProgressBarFlowable(c_conf, c_risk, c_nc, c_na, width=380, height=14)
        claim_elements.append(bar)
        claim_elements.append(Spacer(1, 2 * mm))

        # Encadré alerte rouge si 3+ problèmes
        if is_alert:
            issues = []
            sorted_results = sorted(
                claim.results,
                key=lambda r: CRITERION_ORDER.index(r.criterion) if r.criterion in CRITERION_ORDER else 99,
            )
            for r in sorted_results:
                if r.verdict in ("non_conforme", "risque"):
                    label = CRITERION_LABELS.get(r.criterion, r.criterion)
                    verdict_label = VERDICT_LABELS.get(r.verdict, r.verdict)
                    issues.append(f"[{verdict_label}] {label} : {r.explanation or ''}")
            alert = AlertBoxFlowable(claim.claim_text, issues, width=A4[0] - 44 * mm)
            claim_elements.append(alert)
            claim_elements.append(Spacer(1, 3 * mm))

        # Tableau des critères
        if is_starter:
            data = [[
                Paragraph("<b>Critère</b>", styles["small"]),
                Paragraph("<b>Verdict</b>", styles["small"]),
                Paragraph("<b>Explication</b>", styles["small"]),
            ]]
        else:
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
            if is_starter:
                data.append([
                    Paragraph(CRITERION_LABELS.get(r.criterion, r.criterion), styles["small"]),
                    Paragraph(VERDICT_LABELS.get(r.verdict, r.verdict), styles["small"]),
                    Paragraph(r.explanation or "", styles["small"]),
                ])
            else:
                data.append([
                    Paragraph(CRITERION_LABELS.get(r.criterion, r.criterion), styles["small"]),
                    Paragraph(VERDICT_LABELS.get(r.verdict, r.verdict), styles["small"]),
                    Paragraph(r.explanation or "", styles["small"]),
                    Paragraph(r.recommendation or "—", styles["small"]),
                ])

        page_width = A4[0] - 40 * mm
        if is_starter:
            col_widths = [page_width * 0.20, page_width * 0.15, page_width * 0.65]
        else:
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
        claim_elements.append(t)
        claim_elements.append(Spacer(1, 2 * mm))

        # Badge "Corrigée" si l'allégation a été marquée comme corrigée
        if getattr(claim, "is_corrected", False):
            corrected_at = getattr(claim, "corrected_at", None)
            date_str = f" le {corrected_at.strftime('%d/%m/%Y')}" if corrected_at else ""
            claim_elements.append(
                Paragraph(
                    f"<font color='#16A34A'><b>Corrigée{date_str}</b></font>",
                    styles["small"],
                )
            )
            claim_elements.append(Spacer(1, 2 * mm))

        # Liste des pièces justificatives uploadées
        evidence_files = getattr(claim, "evidence_files", [])
        if evidence_files:
            DOC_TYPE_LABELS = {
                "ecolabel": "Écolabel",
                "certification": "Certification",
                "rapport_interne": "Rapport interne",
                "autre": "Autre",
            }
            ev_data = [[
                Paragraph("<b>Pièce justificative</b>", styles["small"]),
                Paragraph("<b>Type</b>", styles["small"]),
                Paragraph("<b>Taille</b>", styles["small"]),
            ]]
            for ef in evidence_files:
                size_kb = round(getattr(ef, "file_size", 0) / 1024, 1)
                doc_label = DOC_TYPE_LABELS.get(getattr(ef, "document_type", "autre"), "Autre")
                ev_data.append([
                    Paragraph(getattr(ef, "filename", "—"), styles["small"]),
                    Paragraph(doc_label, styles["small"]),
                    Paragraph(f"{size_kb} Ko", styles["small"]),
                ])
            ev_table = Table(ev_data, colWidths=[page_width * 0.55, page_width * 0.25, page_width * 0.20], repeatRows=1)
            ev_table.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#E8F5E9")),
                ("FONTSIZE", (0, 0), (-1, -1), 8),
                ("ALIGN", (0, 0), (-1, 0), "LEFT"),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.lightgrey),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("LEFTPADDING", (0, 0), (-1, -1), 4),
                ("RIGHTPADDING", (0, 0), (-1, -1), 4),
            ]))
            claim_elements.append(Paragraph("<b>Pièces justificatives</b>", styles["small"]))
            claim_elements.append(Spacer(1, 1 * mm))
            claim_elements.append(ev_table)
            claim_elements.append(Spacer(1, 2 * mm))

        claim_elements.append(Spacer(1, 4 * mm))

        # KeepTogether pour éviter les coupures au milieu d'une allégation
        elements.append(KeepTogether(claim_elements))

    return elements


def _correction_plan_elements(claims: list, styles: dict) -> list:
    """Section plan de correction avec échéances."""
    elements = []
    elements.append(Paragraph("4. Plan de correction priorisé", styles["h1"]))

    actions = []
    for claim in claims:
        if claim.overall_verdict == "conforme":
            continue
        for r in claim.results:
            if r.verdict in ("non_conforme", "risque") and r.recommendation:
                if r.verdict == "non_conforme":
                    priority = "Critique"
                    deadline = "Immédiat (< 30 jours)"
                else:
                    priority = "Élevé"
                    deadline = "Court terme (< 90 jours)"
                actions.append((priority, claim.claim_text[:55] + "…",
                                CRITERION_LABELS.get(r.criterion, r.criterion),
                                r.recommendation, deadline))

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
        Paragraph("<b>Échéance</b>", styles["small"]),
    ]]
    for a in actions:
        data.append([
            Paragraph(a[0], styles["small"]),
            Paragraph(a[1], styles["small"]),
            Paragraph(a[2], styles["small"]),
            Paragraph(a[3], styles["small"]),
            Paragraph(a[4], styles["small"]),
        ])

    page_width = A4[0] - 40 * mm
    t = Table(data, colWidths=[page_width * 0.10, page_width * 0.22, page_width * 0.14, page_width * 0.36, page_width * 0.18], repeatRows=1)
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
    elements.append(Paragraph(
        "<b>Date limite de mise en conformité directive EmpCo : 27 septembre 2026</b>",
        styles["deadline_footer"],
    ))
    return elements


def _financial_risk_elements(audit: Audit, styles: dict) -> list:
    """Section estimation du risque financier."""
    elements = []
    elements.append(Paragraph("5. Exposition aux sanctions", styles["h1"]))

    nc_count = audit.non_conforming_claims or 0

    # Encadré jaune avec bordure orange
    box_data = []
    box_data.append([Paragraph(
        "<b>Sanctions encourues en cas de greenwashing avéré :</b>",
        ParagraphStyle("warn_title", parent=styles["body"], fontSize=9, textColor=colors.HexColor("#92400E")),
    )])
    box_data.append([Paragraph(
        "• <b>Pratique commerciale trompeuse</b> (Code conso Art. L132-2) : "
        "jusqu'à 300 000 € d'amende et 2 ans d'emprisonnement pour les personnes physiques, "
        "jusqu'à 1 500 000 € pour les personnes morales",
        ParagraphStyle("warn_item", parent=styles["small"], fontSize=8, textColor=colors.HexColor("#78350F"), leading=11),
    )])
    box_data.append([Paragraph(
        "• <b>Amende administrative DGCCRF</b> : jusqu'à 100 000 € par infraction",
        ParagraphStyle("warn_item2", parent=styles["small"], fontSize=8, textColor=colors.HexColor("#78350F"), leading=11),
    )])
    box_data.append([Paragraph(
        "• <b>Injonction de cessation</b> : retrait immédiat des communications non conformes",
        ParagraphStyle("warn_item3", parent=styles["small"], fontSize=8, textColor=colors.HexColor("#78350F"), leading=11),
    )])
    box_data.append([Spacer(1, 2 * mm)])
    box_data.append([Paragraph(
        f"Avec <b>{nc_count} allégation{'s' if nc_count > 1 else ''} non conforme{'s' if nc_count > 1 else ''}</b> "
        f"identifiée{'s' if nc_count > 1 else ''}, l'exposition potentielle est significative.",
        ParagraphStyle("warn_summary", parent=styles["body"], fontSize=9, textColor=colors.HexColor("#92400E")),
    )])
    box_data.append([Spacer(1, 2 * mm)])
    box_data.append([Paragraph(
        "<i>Note : Les sanctions sont déterminées par chaque État membre conformément "
        "à l'article 13 de la directive 2005/29/CE. Les montants ci-dessus correspondent "
        "au cadre légal français en vigueur à la date d'audit. "
        "Consultez un avocat pour une évaluation précise.</i>",
        ParagraphStyle("warn_disclaimer", parent=styles["small"], fontSize=7, textColor=colors.HexColor("#92400E"), leading=10),
    )])

    page_width = A4[0] - 40 * mm
    t = Table(box_data, colWidths=[page_width - 8])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#FFFBEB")),
        ("BOX", (0, 0), (-1, -1), 1.5, colors.HexColor("#EA580C")),
        ("LEFTPADDING", (0, 0), (-1, -1), 10),
        ("RIGHTPADDING", (0, 0), (-1, -1), 10),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    elements.append(t)
    return elements


def _labels_checklist_elements(claims: list, styles: dict) -> list:
    """Section checklist labels."""
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
    elements.append(Paragraph("6. Checklist labels", styles["h1"]))
    if to_remove:
        elements.append(Paragraph("Labels à retirer (auto-décernés) :", styles["body"]))
        for name in to_remove:
            elements.append(Paragraph(f"  • {name}", styles["body"]))
    if to_keep:
        elements.append(Paragraph("Labels conformes à conserver :", styles["body"]))
        for name in to_keep:
            elements.append(Paragraph(f"  • {name}", styles["body"]))
    return elements


def _upgrade_banner_elements(section_title: str, styles: dict) -> list:
    """Encadré 'Disponible en plan Pro' pour les sections bridées en Starter."""
    elements = []
    elements.append(Paragraph(section_title, styles["h1"]))
    page_width = A4[0] - 40 * mm
    banner_data = [[
        Paragraph(
            "<b>Disponible avec le plan Pro</b><br/>"
            "Cette section est réservée aux partenaires Pro et Enterprise. "
            "Passez au plan Pro pour accéder au rapport complet : plan de correction priorisé, "
            "risque financier estimé, références réglementaires détaillées et checklist labels.",
            ParagraphStyle("upgrade_text", parent=styles["body"], fontSize=9,
                           textColor=colors.HexColor("#1B5E20"), leading=13),
        )
    ]]
    t = Table(banner_data, colWidths=[page_width])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#F0FDF4")),
        ("BOX", (0, 0), (-1, -1), 1.5, colors.HexColor("#1B5E20")),
        ("LEFTPADDING", (0, 0), (-1, -1), 14),
        ("RIGHTPADDING", (0, 0), (-1, -1), 14),
        ("TOPPADDING", (0, 0), (-1, -1), 12),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 12),
    ]))
    elements.append(t)
    elements.append(Spacer(1, 6 * mm))
    return elements


def _references_elements(styles: dict) -> list:
    """Section références réglementaires."""
    elements = []
    elements.append(Paragraph("7. Références réglementaires", styles["h1"]))
    page_width = A4[0] - 40 * mm
    data = [
        [Paragraph("<b>Texte</b>", styles["small"]), Paragraph("<b>Référence</b>", styles["small"]), Paragraph("<b>Objet</b>", styles["small"])],
        [Paragraph("Directive EmpCo", styles["small"]), Paragraph("EU 2024/825", styles["small"]), Paragraph("Modifie la directive 2005/29/CE — protection des consommateurs contre le greenwashing", styles["small"])],
        [Paragraph("Annexe I, point 2bis", styles["small"]), Paragraph("Dir. 2005/29/CE modifiée", styles["small"]), Paragraph("Interdiction des labels de durabilité non certifiés par un tiers ou une autorité publique", styles["small"])],
        [Paragraph("Annexe I, point 4bis", styles["small"]), Paragraph("Dir. 2005/29/CE modifiée", styles["small"]), Paragraph("Interdiction des allégations environnementales génériques sans performance excellente reconnue", styles["small"])],
        [Paragraph("Annexe I, point 4ter", styles["small"]), Paragraph("Dir. 2005/29/CE modifiée", styles["small"]), Paragraph("Interdiction des allégations sur l'ensemble du produit/entreprise ne concernant qu'un aspect", styles["small"])],
        [Paragraph("Annexe I, point 4quater", styles["small"]), Paragraph("Dir. 2005/29/CE modifiée", styles["small"]), Paragraph("Interdiction de la neutralité carbone par compensation d'émissions", styles["small"])],
        [Paragraph("Annexe I, point 10bis", styles["small"]), Paragraph("Dir. 2005/29/CE modifiée", styles["small"]), Paragraph("Interdiction de présenter des exigences légales comme avantage distinctif", styles["small"])],
        [Paragraph("Art. 6.2(d)", styles["small"]), Paragraph("Dir. 2005/29/CE modifiée", styles["small"]), Paragraph("Engagements futurs : plan détaillé, objectifs mesurables, vérification indépendante", styles["small"])],
        [Paragraph("Loi AGEC", styles["small"]), Paragraph("Loi n° 2020-105", styles["small"]), Paragraph("Interdiction mentions « biodégradable » et « respectueux de l'environnement » (Art. 13)", styles["small"])],
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


def _disclaimer_elements(partner: Partner, styles: dict, is_starter: bool = False) -> list:
    """Section avertissement final."""
    elements = []
    elements.append(Spacer(1, 10 * mm))
    elements.append(Paragraph("Avertissement", styles["h1"]))
    elements.append(Paragraph(
        "Ce rapport est un outil d'aide à la conformité et ne constitue pas un conseil juridique. "
        "Il est recommandé de consulter un avocat spécialisé pour toute question relative à la "
        "conformité réglementaire de vos communications environnementales.",
        styles["disclaimer"],
    ))
    if is_starter:
        elements.append(Spacer(1, 4 * mm))
        elements.append(Paragraph(
            "Ce rapport est une version d'aperçu (plan Starter). Le rapport complet inclut les recommandations "
            "de correction, le plan d'action priorisé, le risque financier estimé et les références réglementaires détaillées. "
            "Contactez-nous sur green-audit.fr pour passer au plan Pro.",
            styles["disclaimer"],
        ))
    else:
        contact_parts = [p for p in [partner.name, partner.contact_name, partner.contact_phone, partner.contact_email] if p]
        elements.append(Spacer(1, 4 * mm))
        elements.append(Paragraph(" — ".join(contact_parts), styles["disclaimer"]))
    return elements


# ---------------------------------------------------------------------------
# Point d'entrée principal
# ---------------------------------------------------------------------------

def generate_audit_pdf(audit: Audit, partner: Partner) -> Tuple[str, str]:
    """
    Génère le rapport PDF complet et le sauvegarde sur disque.

    Returns:
        Tuple (nom du fichier PDF, hash SHA-256 du fichier).
    """
    is_starter = (partner.subscription_plan or "starter") in ("starter", "free")

    claims = sorted(audit.claims, key=lambda c: c.created_at)
    primary = _hex(partner.brand_primary_color)
    secondary = _hex(partner.brand_secondary_color, "#2E7D32")
    styles = _build_styles(primary, secondary)

    storage_path = Path(settings.PDF_STORAGE_PATH)
    storage_path.mkdir(parents=True, exist_ok=True)

    filename = f"greenaudit_{audit.id}.pdf"
    filepath = str(storage_path / filename)

    doc = _build_doc(filepath, partner, is_starter=is_starter)

    elements = []
    elements.extend(_cover_elements(audit, partner, styles, is_starter=is_starter))
    elements.extend(_summary_elements(audit, styles))
    elements.extend(_radar_elements(claims, styles))
    elements.extend(_claims_detail_elements(claims, styles, is_starter=is_starter))
    if is_starter:
        elements.extend(_upgrade_banner_elements("4. Plan de correction priorisé", styles))
        elements.extend(_upgrade_banner_elements("5. Risque financier estimé", styles))
        elements.extend(_upgrade_banner_elements("7. Références réglementaires", styles))
    else:
        elements.extend(_correction_plan_elements(claims, styles))
        elements.extend(_financial_risk_elements(audit, styles))
        elements.extend(_labels_checklist_elements(claims, styles))
        elements.extend(_references_elements(styles))
    elements.extend(_disclaimer_elements(partner, styles, is_starter=is_starter))

    doc.build(elements)

    # Calculer le SHA-256 du fichier généré
    sha256 = hashlib.sha256(Path(filepath).read_bytes()).hexdigest()

    # Ajouter le hash en pied du PDF (reconstruction légère avec canvas)
    _stamp_sha256(filepath, sha256, audit.id)

    return filename, sha256


def _stamp_sha256(filepath: str, sha256: str, audit_id) -> None:
    """Ajoute une ligne SHA-256 en bas de la dernière page du PDF."""
    try:
        from reportlab.pdfgen import canvas as rl_canvas
        from reportlab.lib.pagesizes import A4
        import io
        from pypdf import PdfReader, PdfWriter

        # Créer une page overlay avec juste le hash
        packet = io.BytesIO()
        c = rl_canvas.Canvas(packet, pagesize=A4)
        c.setFont("Helvetica", 6)
        c.setFillColorRGB(0.6, 0.6, 0.6)
        text = f"SHA-256 : {sha256} — Rapport #{str(audit_id)[:8].upper()}"
        c.drawCentredString(A4[0] / 2, 6 * mm, text)
        c.save()
        packet.seek(0)

        overlay_reader = PdfReader(packet)
        overlay_page = overlay_reader.pages[0]

        reader = PdfReader(filepath)
        writer = PdfWriter()

        for i, page in enumerate(reader.pages):
            if i == len(reader.pages) - 1:
                page.merge_page(overlay_page)
            writer.add_page(page)

        with open(filepath, "wb") as f:
            writer.write(f)
    except Exception:
        pass  # Si pypdf n'est pas installé, on ignore — le hash est quand même en base
