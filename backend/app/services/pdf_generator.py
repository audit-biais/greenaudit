"""
Génération du rapport PDF white-label via ReportLab (pure Python, pas de dépendance système).

DESIGN v2 — avril 2026 — Refonte visuelle institutionnelle
-----------------------------------------------------------
Style cible : cabinet d'audit professionnel (KPMG, Deloitte, OneTrust).
Changements apportés par rapport à la v1 :

Palette :
  - Accent primaire   : bleu marine #0f172a (remplace vert #1B5E20)
  - Accent secondaire : bleu acier  #334155 (remplace vert #2E7D32)
  - Texte principal   : anthracite  #1e293b
  - Labels/annotations: gris ardoise #64748b
  - Conforme          : vert forêt   #15803d (sobre, non flashy)
  - Risque            : ambre        #b45309
  - Élevé             : orange brûlé #c2410c
  - Critique          : rouge sobre  #b91c1c
  - Bordures tableaux : #e2e8f0
  - Lignes alternées  : #f8fafc

AlertBoxFlowable :
  - Bordure gauche épaisse colorée (4pt) + fond très légèrement teinté
  - Label textuel "ALERTE" en majuscules (pas d'icône SVG)

Tableaux :
  - Header : bleu marine #0f172a + texte blanc
  - Lignes alternées subtiles #f8fafc
  - Bordures fines #e2e8f0
  - Padding généreux (8pt top/bottom)

Page de garde :
  - Badge "DOSSIER DE CONFORMITÉ EMPCO" en haut à droite (via footer callback)
  - Bloc client dans un encadré sobre
  - Niveau de risque dans un cadre coloré
  - Pied de page : cabinet auditeur + mention confidentiel

Allégations :
  - Chaque bloc dans un encadré à bordure fine #e2e8f0
  - Référence réglementaire principale en pied de bloc (petit gris)

Corrections texte :
  - "détecte" → "détecte" (accents corrigés partout)
  - "neutralité" correctement accentué
  - CO₂ (caractère Unicode correct)

Fonctionnalités conservées intégralement :
  - White-label (branding partenaire, couleurs dynamiques)
  - Starter vs Pro gating
  - SHA-256, nonce PDF
  - Score post-correction, radar, plan de correction, risque financier
"""

from __future__ import annotations

import hashlib
import logging
import math
import os
import tempfile
from urllib.parse import urlparse

logger = logging.getLogger(__name__)
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
    HRFlowable,
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
# Palette institutionnelle v2
# ---------------------------------------------------------------------------

_C_NAVY    = "#0f172a"   # Bleu marine profond — accent primaire
_C_STEEL   = "#334155"   # Bleu acier — accent secondaire
_C_TEXT    = "#1e293b"   # Anthracite — texte principal
_C_SLATE   = "#64748b"   # Gris ardoise — labels / annotations
_C_LIGHT   = "#94a3b8"   # Gris clair — texte très discret
_C_BORDER  = "#e2e8f0"   # Bordure tableau / encadré
_C_ALT     = "#f8fafc"   # Ligne alternée tableau

_C_CONFORME  = "#15803d"  # Vert forêt
_C_RISQUE    = "#b45309"  # Ambre
_C_ELEVE     = "#c2410c"  # Orange brûlé
_C_CRITIQUE  = "#b91c1c"  # Rouge sobre


# ---------------------------------------------------------------------------
# Constantes
# ---------------------------------------------------------------------------

RISK_COLORS: Dict[str, colors.Color] = {
    "faible":   colors.HexColor(_C_CONFORME),
    "modere":   colors.HexColor(_C_RISQUE),
    "eleve":    colors.HexColor(_C_ELEVE),
    "critique": colors.HexColor(_C_CRITIQUE),
}

VERDICT_LABELS: Dict[str, str] = {
    "conforme":       "Conforme",
    "non_conforme":   "Non conforme",
    "risque":         "Risque",
    "non_applicable": "N/A",
}

CRITERION_LABELS: Dict[str, str] = {
    "specificity":       "Spécificité",
    "compensation":      "Neutralité carbone",
    "labels":            "Labels",
    "proportionality":   "Proportionnalité",
    "future_commitment": "Engagements futurs",
    "justification":     "Justification / Preuves",
    "legal_requirement": "Exigences légales",
}

# Labels raccourcis pour le radar (espace contraint)
RADAR_CRITERION_LABELS: Dict[str, str] = {
    "specificity":       "Spécificité",
    "compensation":      "Neutr. carbone",
    "labels":            "Labels",
    "proportionality":   "Proportion.",
    "future_commitment": "Engagements",
    "justification":     "Justification",
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
    "web":            "Site web",
    "packaging":      "Packaging",
    "publicite":      "Publicité",
    "reseaux_sociaux": "Réseaux sociaux",
    "autre":          "Autre",
}

REGULATORY_BASIS_LABELS: Dict[str, str] = {
    "annexe_I_2bis":     "Annexe I, pt 2 bis — Label sans certification tierce",
    "annexe_I_4bis":     "Annexe I, pt 4 bis — Allégation environnementale générique",
    "annexe_I_4ter":     "Annexe I, pt 4 ter — Proportionnalité ensemble vs aspect",
    "annexe_I_4quater":  "Annexe I, pt 4 quater — Neutralité carbone par compensation",
    "annexe_I_10bis":    "Annexe I, pt 10 bis — Caractéristique légale présentée comme distinctive",
    "article_6_1d":      "Art. 6, §2, pt d — Engagement futur sans plan vérifiable",
    "article_6_general": "Art. 6, §1, pt b — Justification des allégations",
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _rl_escape(text: str) -> str:
    """Échappe les caractères XML spéciaux pour ReportLab Paragraph."""
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def _hex(color_str: Optional[str], fallback: str = _C_NAVY) -> colors.Color:
    try:
        return colors.HexColor(color_str or fallback)
    except Exception:
        return colors.HexColor(fallback)


def _format_date(dt: Optional[datetime]) -> str:
    if dt is None:
        return "—"
    return dt.strftime("%d/%m/%Y")


def _format_phone(phone: str) -> str:
    digits = "".join(c for c in phone if c.isdigit())
    if len(digits) == 10 and digits.startswith("0"):
        return " ".join(digits[i:i+2] for i in range(0, 10, 2))
    return phone


def _smart_truncate(text: str, max_chars: int) -> str:
    if len(text) <= max_chars:
        return text
    truncated = text[:max_chars]
    last_space = truncated.rfind(" ")
    if last_space > max_chars // 2:
        return truncated[:last_space] + "…"
    return truncated + "…"


def _summary_phrase(risk_level: Optional[str]) -> str:
    phrases = {
        "faible":   "La majorité des allégations sont conformes.",
        "modere":   "Plusieurs allégations nécessitent des corrections.",
        "eleve":    "Un nombre significatif d'allégations sont non conformes. Actions correctives urgentes recommandées.",
        "critique": "Situation critique. La majorité des allégations exposent l'entreprise à des sanctions.",
    }
    return phrases.get(risk_level or "", phrases["critique"])


RISK_LABELS: Dict[str, str] = {
    "faible":   "faible",
    "modere":   "modéré",
    "eleve":    "élevé",
    "critique": "critique",
}


def _risk_label(risk_level: Optional[str]) -> str:
    """Retourne le niveau de risque avec accents."""
    return RISK_LABELS.get(risk_level or "", risk_level or "—")


def _score_color(score: float) -> colors.Color:
    """Retourne la couleur correspondant au score (palette institutionnelle)."""
    if score <= 25:
        return colors.HexColor(_C_CRITIQUE)
    elif score <= 50:
        return colors.HexColor(_C_ELEVE)
    elif score <= 75:
        return colors.HexColor(_C_RISQUE)
    else:
        return colors.HexColor(_C_CONFORME)


def _count_issues(claim) -> int:
    """Compte le nombre de non-conformités + risques d'une claim."""
    count = 0
    for r in claim.results:
        if r.verdict in ("non_conforme", "risque"):
            count += 1
    return count


def _reformulation_hint(regulatory_basis: Optional[str]) -> Optional[str]:
    """Retourne une suggestion de reformulation pour les allégations liste_noire."""
    hints: Dict[str, str] = {
        "annexe_I_4bis": (
            "Remplacez l'allégation générique par une formulation précise et mesurable. "
            "Ex. : « Emballage composé à 40 % de plastique recyclé, certifié Recyclass » "
            "plutôt que « produit écologique »."
        ),
        "annexe_I_4ter": (
            "Restreignez la portée à l'aspect concerné. "
            "Ex. : « Notre packaging est fabriqué à 80 % de carton issu de forêts gérées "
            "durablement (PEFC) » plutôt qu'une formulation couvrant l'ensemble de l'activité."
        ),
        "annexe_I_4quater": (
            "Les allégations de neutralité carbone par compensation sont interdites. "
            "Privilegiez une réduction réelle des émissions avec données vérifiables. "
            "Ex. : « Émissions réduites de 42 % depuis 2019, mesurées par un tiers indépendant (scope 1+2) »."
        ),
        "annexe_I_2bis": (
            "Supprimez ou remplacez le label auto-décerné par un label certifié tiers reconnu "
            "(Ecocert, EU Ecolabel, NF Environnement, etc.)."
        ),
        "annexe_I_10bis": (
            "Cette caractéristique est une exigence légale — elle ne peut pas être présentée "
            "comme un avantage distinctif. Supprimez la mention ou contextualisez-la clairement."
        ),
    }
    return hints.get(regulatory_basis or "", None)


# ---------------------------------------------------------------------------
# Custom Flowables
# ---------------------------------------------------------------------------

class GaugeFlowable(Flowable):
    """Jauge semi-circulaire (arc) avec aiguille — style institutionnel."""

    def __init__(self, score: float, width: float = 200, height: float = 130):
        super().__init__()
        self.score = score or 0
        self.width = width
        self.height = height

    def draw(self):
        c = self.canv
        cx = self.width / 2
        cy = 28

        radius = 78
        arc_width = 14

        # Arc de fond (gris très clair)
        c.saveState()
        c.setStrokeColor(colors.HexColor("#e2e8f0"))
        c.setLineWidth(arc_width)
        c.setLineCap(1)
        x1, y1 = cx - radius, cy - radius
        x2, y2 = cx + radius, cy + radius
        c.arc(x1, y1, x2, y2, 0, 180)
        c.restoreState()

        # Segments colorés (palette institutionnelle)
        segments = [
            (0,   45, _C_CRITIQUE),   # 0-25
            (45,  45, _C_ELEVE),      # 25-50
            (90,  45, _C_RISQUE),     # 50-75
            (135, 45, _C_CONFORME),   # 75-100
        ]
        for start, extent, hex_color in segments:
            c.saveState()
            c.setStrokeColor(colors.HexColor(hex_color))
            c.setLineWidth(arc_width)
            c.setLineCap(1)
            c.arc(x1, y1, x2, y2, start, extent)
            c.restoreState()

        # Aiguille
        angle_deg = 180 - (self.score / 100 * 180)
        angle_rad = math.radians(angle_deg)
        needle_len = radius - 12
        nx = cx + needle_len * math.cos(angle_rad)
        ny = cy + needle_len * math.sin(angle_rad)

        c.saveState()
        c.setStrokeColor(colors.HexColor(_C_TEXT))
        c.setLineWidth(2)
        c.line(cx, cy, nx, ny)
        # Pivot central
        c.setFillColor(colors.HexColor(_C_TEXT))
        c.circle(cx, cy, 4, fill=1, stroke=0)
        c.restoreState()

        # Score centré
        score_color = _score_color(self.score)
        c.saveState()
        c.setFont("Helvetica-Bold", 26)
        c.setFillColor(score_color)
        c.drawCentredString(cx, cy + 28, f"{self.score:.0f}")
        c.setFont("Helvetica", 9)
        c.setFillColor(colors.HexColor(_C_SLATE))
        c.drawCentredString(cx, cy + 17, "/ 100")
        c.restoreState()

        # Étiquettes 0 / 100
        c.saveState()
        c.setFont("Helvetica", 7)
        c.setFillColor(colors.HexColor(_C_LIGHT))
        c.drawString(cx - radius - 4, cy - 9, "0")
        c.drawRightString(cx + radius + 4, cy - 9, "100")
        c.restoreState()


class SummaryDotsFlowable(Flowable):
    """Indicateurs résumé : points colorés + labels (style institutionnel)."""

    def __init__(self, conformes: int, risque: int, non_conformes: int, width: float = 400):
        super().__init__()
        self.conformes = conformes
        self.risque = risque
        self.non_conformes = non_conformes
        self.width = width
        self.height = 22

    def draw(self):
        c = self.canv
        items = [
            (colors.HexColor(_C_CRITIQUE), f"{self.non_conformes} non conforme{'s' if self.non_conformes > 1 else ''}"),
            (colors.HexColor(_C_RISQUE),   f"{self.risque} à risque"),
            (colors.HexColor(_C_CONFORME), f"{self.conformes} conforme{'s' if self.conformes > 1 else ''}"),
        ]
        spacing = self.width / 3
        for i, (color, text) in enumerate(items):
            cx = spacing * i + spacing / 2
            cy = self.height / 2
            c.saveState()
            c.setFillColor(color)
            c.circle(cx - 32, cy, 4.5, fill=1, stroke=0)
            c.setFont("Helvetica", 9)
            c.setFillColor(colors.HexColor(_C_TEXT))
            c.drawString(cx - 24, cy - 3, text)
            c.restoreState()


class RadarChartFlowable(Flowable):
    """Radar chart (spider chart) — palette institutionnelle bleu marine."""

    def __init__(self, scores: Dict[str, float], width: float = 360, height: float = 290):
        super().__init__()
        self.scores = scores
        self.width = width
        self.height = height

    def draw(self):
        c = self.canv
        cx = self.width / 2
        cy = self.height / 2 + 10
        radius = 85
        axes = RADAR_CRITERIA
        n = len(axes)
        if n == 0:
            return

        angles = [math.pi / 2 - (2 * math.pi * i / n) for i in range(n)]

        # Grilles concentriques
        for level in [0.2, 0.4, 0.6, 0.8, 1.0]:
            c.saveState()
            c.setStrokeColor(colors.HexColor(_C_BORDER))
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

        # Axes radiaux
        c.saveState()
        c.setStrokeColor(colors.HexColor("#cbd5e1"))
        c.setLineWidth(0.5)
        for a in angles:
            c.line(cx, cy, cx + radius * math.cos(a), cy + radius * math.sin(a))
        c.restoreState()

        # Polygone des données
        values = []
        for criterion in axes:
            val = self.scores.get(criterion)
            values.append((val / 100.0) if val is not None else 0.5)

        c.saveState()
        # Remplissage bleu marine semi-transparent
        fill_color = colors.Color(0.06, 0.09, 0.16, alpha=0.18)
        c.setFillColor(fill_color)
        c.setStrokeColor(colors.HexColor(_C_NAVY))
        c.setLineWidth(1.5)
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
            c.setFillColor(colors.HexColor(_C_STEEL))
            c.circle(px, py, 3, fill=1, stroke=0)
            c.restoreState()

        # Labels des axes
        c.saveState()
        c.setFont("Helvetica", 9)
        c.setFillColor(colors.HexColor(_C_SLATE))
        label_offset = 20
        for i, a in enumerate(angles):
            criterion = axes[i]
            label = RADAR_CRITERION_LABELS.get(criterion, criterion)
            lx = cx + (radius + label_offset) * math.cos(a)
            ly = cy + (radius + label_offset) * math.sin(a)
            if abs(math.cos(a)) < 0.1:
                c.drawCentredString(lx, ly - 3, label)
            elif math.cos(a) > 0:
                c.drawString(lx, ly - 3, label)
            else:
                c.drawRightString(lx, ly - 3, label)
        c.restoreState()

        # Pas d'étiquettes de valeur % sur les axes — le graphique est lisible
        # sans elles et elles causent des chevauchements avec les labels d'axe.


class ProgressBarFlowable(Flowable):
    """Barre de progression horizontale segmentée — palette institutionnelle."""

    def __init__(self, conformes: int, risque: int, non_conformes: int, na: int,
                 width: float = 400, height: float = 12):
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
        bar_height = 8
        y = (self.height - bar_height) / 2
        x = 0

        segments = [
            (self.conformes,   _C_CONFORME),
            (self.risque,      _C_RISQUE),
            (self.non_conformes, _C_CRITIQUE),
            (self.na,          "#cbd5e1"),
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

        # Légende compacte
        legend_x = self.width + 8
        c.saveState()
        c.setFont("Helvetica", 6)
        c.setFillColor(colors.HexColor(_C_SLATE))
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
    """Encadré alerte : bordure gauche épaisse colorée + fond légèrement teinté."""

    def __init__(self, claim_text: str, issues: list, width: float = 480):
        super().__init__()
        self.claim_text = claim_text
        self.issues = issues
        self.width = width
        self.height = 58 + len(issues) * 13

    def draw(self):
        c = self.canv
        border_w = 4  # Largeur de la bordure gauche en points

        # Fond légèrement teinté rouge
        c.saveState()
        c.setFillColor(colors.HexColor("#fef2f2"))
        c.setStrokeColor(colors.white)
        c.setLineWidth(0)
        c.rect(border_w, 0, self.width - border_w, self.height, fill=1, stroke=0)
        c.restoreState()

        # Bordure gauche épaisse rouge sobre
        c.saveState()
        c.setFillColor(colors.HexColor(_C_CRITIQUE))
        c.rect(0, 0, border_w, self.height, fill=1, stroke=0)
        c.restoreState()

        # Label "ALERTE" en majuscules
        c.saveState()
        c.setFont("Helvetica-Bold", 7)
        c.setFillColor(colors.HexColor(_C_CRITIQUE))
        n_issues = len(self.issues)
        c.drawString(border_w + 10, self.height - 16,
                     f"ALERTE — {n_issues} problème{'s' if n_issues > 1 else ''} détecté{'s' if n_issues > 1 else ''}")
        c.restoreState()

        # Citation de la claim (tronquée)
        c.saveState()
        c.setFont("Helvetica-Oblique", 8)
        c.setFillColor(colors.HexColor("#7f1d1d"))
        claim_display = self.claim_text[:90] + ("..." if len(self.claim_text) > 90 else "")
        c.drawString(border_w + 10, self.height - 30, f"« {claim_display} »")
        c.restoreState()

        # Liste des problèmes
        c.saveState()
        c.setFont("Helvetica", 8)
        c.setFillColor(colors.HexColor("#991b1b"))
        y = self.height - 44
        for issue in self.issues:
            text = issue[:100] + ("..." if len(issue) > 100 else "")
            c.drawString(border_w + 16, y, f"– {text}")
            y -= 13
        c.restoreState()


# ---------------------------------------------------------------------------
# Styles
# ---------------------------------------------------------------------------

def _build_styles(primary: colors.Color, secondary: colors.Color):
    ss = getSampleStyleSheet()
    styles = {
        "title": ParagraphStyle(
            "title", parent=ss["Title"],
            fontSize=22, textColor=primary,
            fontName="Helvetica-Bold", spaceAfter=6,
        ),
        "h1": ParagraphStyle(
            "h1", parent=ss["Heading1"],
            fontSize=14, textColor=primary,
            fontName="Helvetica-Bold", spaceAfter=8, spaceBefore=14,
        ),
        "h2": ParagraphStyle(
            "h2", parent=ss["Heading2"],
            fontSize=11, textColor=secondary,
            fontName="Helvetica-Bold", spaceAfter=5, spaceBefore=10,
        ),
        "h2_alert": ParagraphStyle(
            "h2_alert", parent=ss["Heading2"],
            fontSize=11, textColor=colors.HexColor(_C_CRITIQUE),
            fontName="Helvetica-Bold", spaceAfter=5, spaceBefore=10,
        ),
        "body": ParagraphStyle(
            "body", parent=ss["Normal"],
            fontSize=10, leading=14, spaceAfter=4,
            textColor=colors.HexColor(_C_TEXT),
        ),
        "small": ParagraphStyle(
            "small", parent=ss["Normal"],
            fontSize=8, textColor=colors.HexColor(_C_SLATE),
            spaceAfter=2, leading=11,
        ),
        "reg_ref": ParagraphStyle(
            "reg_ref", parent=ss["Normal"],
            fontSize=7, textColor=colors.HexColor(_C_LIGHT),
            spaceAfter=0, leading=10, fontName="Helvetica-Oblique",
        ),
        "italic": ParagraphStyle(
            "italic", parent=ss["Normal"],
            fontSize=10, leading=14,
            textColor=colors.HexColor("#475569"),
            spaceAfter=4, fontName="Helvetica-Oblique",
        ),
        "bold": ParagraphStyle(
            "bold", parent=ss["Normal"],
            fontSize=10, leading=14, spaceAfter=4,
            fontName="Helvetica-Bold", textColor=colors.HexColor(_C_TEXT),
        ),
        "cover_score": ParagraphStyle(
            "cover_score", parent=ss["Title"],
            fontSize=48, alignment=1, spaceAfter=4,
        ),
        "cover_center": ParagraphStyle(
            "cover_center", parent=ss["Normal"],
            fontSize=13, alignment=1, spaceAfter=4,
            textColor=colors.HexColor(_C_TEXT),
        ),
        "cover_small": ParagraphStyle(
            "cover_small", parent=ss["Normal"],
            fontSize=9, alignment=1,
            textColor=colors.HexColor(_C_SLATE), spaceAfter=4,
        ),
        "disclaimer": ParagraphStyle(
            "disclaimer", parent=ss["Normal"],
            fontSize=8, textColor=colors.HexColor(_C_SLATE), leading=11,
        ),
        "alert_body": ParagraphStyle(
            "alert_body", parent=ss["Normal"],
            fontSize=9, textColor=colors.HexColor("#991b1b"), leading=12,
        ),
        "deadline_footer": ParagraphStyle(
            "deadline_footer", parent=ss["Normal"],
            fontSize=9, textColor=colors.HexColor(_C_ELEVE),
            leading=12, spaceBefore=6,
        ),
    }
    return styles


# ---------------------------------------------------------------------------
# Page templates avec header/footer
# ---------------------------------------------------------------------------

def _build_doc(filepath: str, partner: Partner, is_starter: bool = False) -> BaseDocTemplate:
    primary = _hex(partner.brand_primary_color) if not is_starter else colors.HexColor(_C_NAVY)
    company = "GreenAudit" if is_starter else (partner.name or "GreenAudit")
    email   = "contact@green-audit.fr" if is_starter else (partner.contact_email or "")
    phone   = "" if is_starter else _format_phone(partner.contact_phone or "")

    def _header_footer(canvas, doc):
        canvas.saveState()
        # Header : nom cabinet + ligne navy
        canvas.setFont("Helvetica-Bold", 8)
        canvas.setFillColor(colors.HexColor(_C_NAVY))
        canvas.drawString(20 * mm, A4[1] - 11 * mm, company)
        canvas.setFont("Helvetica", 7)
        canvas.setFillColor(colors.HexColor(_C_SLATE))
        canvas.drawRightString(A4[0] - 20 * mm, A4[1] - 11 * mm, "Document confidentiel")
        canvas.setStrokeColor(primary)
        canvas.setLineWidth(0.75)
        canvas.line(20 * mm, A4[1] - 14 * mm, A4[0] - 20 * mm, A4[1] - 14 * mm)
        # Footer
        footer_parts = [p for p in [company, phone, email] if p]
        footer_text = " — ".join(footer_parts)
        canvas.setFont("Helvetica", 7)
        canvas.setFillColor(colors.HexColor(_C_SLATE))
        canvas.drawCentredString(A4[0] / 2, 12 * mm, footer_text)
        canvas.drawRightString(A4[0] - 20 * mm, 12 * mm, f"Page {doc.page}")
        canvas.restoreState()

    def _cover_footer(canvas, doc):
        canvas.saveState()
        # Badge "DOSSIER DE CONFORMITÉ EMPCO" en haut à droite
        badge_w = 92 * mm
        badge_h = 15 * mm
        badge_x = A4[0] - 20 * mm - badge_w
        badge_y = A4[1] - 20 * mm - badge_h
        canvas.setFillColor(colors.HexColor(_C_ALT))
        canvas.setStrokeColor(colors.HexColor(_C_NAVY))
        canvas.setLineWidth(0.5)
        canvas.rect(badge_x, badge_y, badge_w, badge_h, fill=1, stroke=1)
        canvas.setFont("Helvetica-Bold", 7)
        canvas.setFillColor(colors.HexColor(_C_NAVY))
        canvas.drawCentredString(badge_x + badge_w / 2, badge_y + 9 * mm, "DOSSIER DE CONFORMITÉ")
        canvas.setFont("Helvetica", 7)
        canvas.setFillColor(colors.HexColor(_C_STEEL))
        canvas.drawCentredString(badge_x + badge_w / 2, badge_y + 4 * mm, "Directive EmpCo — EU 2024/825")
        # Pied de page de couverture
        canvas.setFont("Helvetica", 7)
        canvas.setFillColor(colors.HexColor(_C_SLATE))
        canvas.drawCentredString(A4[0] / 2, 12 * mm,
                                 f"Rapport établi par {company} — Document confidentiel")
        canvas.restoreState()

    frame = Frame(20 * mm, 20 * mm, A4[0] - 40 * mm, A4[1] - 40 * mm, id="main")
    cover_frame = Frame(20 * mm, 20 * mm, A4[0] - 40 * mm, A4[1] - 40 * mm, id="cover")

    doc = BaseDocTemplate(
        filepath,
        pagesize=A4,
        pageTemplates=[
            PageTemplate(id="cover",   frames=[cover_frame], onPage=_cover_footer),
            PageTemplate(id="content", frames=[frame],        onPage=_header_footer),
        ],
    )
    return doc


# ---------------------------------------------------------------------------
# Sections du rapport
# ---------------------------------------------------------------------------

def _cover_elements(audit: Audit, partner: Partner, styles: dict, is_starter: bool = False) -> list:
    """Page 1 : page de garde institutionnelle."""
    from io import BytesIO
    from reportlab.platypus import Image as RLImage
    from reportlab.lib.utils import ImageReader

    def _make_logo_table(data: bytes, max_w_mm: float = 70, max_h_mm: float = 45):
        reader = ImageReader(BytesIO(data))
        iw, ih = reader.getSize()
        ratio = min((max_w_mm * mm) / iw, (max_h_mm * mm) / ih)
        w, h = iw * ratio, ih * ratio
        img = RLImage(BytesIO(data), width=w, height=h)
        tbl = Table([[img]], colWidths=[w])
        tbl.setStyle(TableStyle([("ALIGN", (0, 0), (-1, -1), "LEFT")]))
        return tbl

    greenaudit_logo = Path(__file__).parent.parent / "static" / "logo.png"
    page_width = A4[0] - 40 * mm
    elements = []
    elements.append(Spacer(1, 4 * mm))

    # Logo
    logo_added = False
    if not is_starter and partner.logo_data:
        try:
            elements.append(_make_logo_table(partner.logo_data))
            elements.append(Spacer(1, 2 * mm))
            logo_added = True
        except Exception as e:
            logger.error("Erreur logo partenaire PDF: %s", e)
    if not logo_added and greenaudit_logo.exists():
        try:
            elements.append(_make_logo_table(greenaudit_logo.read_bytes()))
            elements.append(Spacer(1, 2 * mm))
        except Exception as e:
            logger.error("Erreur logo GreenAudit PDF: %s", e)

    # Ligne séparatrice sous le logo
    elements.append(HRFlowable(
        width="100%", thickness=1,
        color=colors.HexColor(_C_BORDER), spaceAfter=5 * mm,
    ))

    # Label catégorie
    label_style = ParagraphStyle(
        "cover_label", parent=styles["cover_small"],
        fontSize=9, textColor=colors.HexColor(_C_STEEL),
        fontName="Helvetica-Bold", alignment=1, spaceAfter=5,
    )
    elements.append(Paragraph("RAPPORT D'AUDIT ANTI-GREENWASHING", label_style))

    # Titre principal
    title_style = ParagraphStyle(
        "cover_title", parent=styles["cover_center"],
        fontSize=16, fontName="Helvetica-Bold",
        textColor=colors.HexColor(_C_NAVY), spaceAfter=0,
    )
    elements.append(Paragraph("Analyse de conformité des allégations environnementales", title_style))
    elements.append(Spacer(1, 5 * mm))

    # Bloc client dans un encadré sobre
    sector_str = _rl_escape(audit.sector or "—")
    date_str = _format_date(audit.completed_at)
    company_style = ParagraphStyle(
        "cover_company", parent=styles["cover_center"],
        fontSize=16, fontName="Helvetica-Bold",
        textColor=colors.HexColor(_C_TEXT), spaceAfter=0, alignment=1,
    )
    info_style = ParagraphStyle(
        "cover_info", parent=styles["cover_small"],
        fontSize=9, textColor=colors.HexColor(_C_SLATE),
        spaceAfter=0, alignment=0,
    )
    client_data = [
        [Paragraph(f"<b>{_rl_escape(audit.company_name)}</b>", company_style), ""],
        [
            Paragraph(f"Secteur : {sector_str}", info_style),
            Paragraph(f"Date d'audit : {date_str}", info_style),
        ],
    ]
    client_table = Table(
        client_data,
        colWidths=[page_width * 0.65, page_width * 0.35],
    )
    client_table.setStyle(TableStyle([
        ("BOX",         (0, 0), (-1, -1), 0.5, colors.HexColor(_C_BORDER)),
        ("LINEBELOW",   (0, 0), (-1, 0),  0.5, colors.HexColor(_C_BORDER)),
        ("BACKGROUND",  (0, 0), (-1, 0),  colors.HexColor(_C_ALT)),
        ("SPAN",        (0, 0), (-1, 0)),
        ("LEFTPADDING",  (0, 0), (-1, -1), 12),
        ("RIGHTPADDING", (0, 0), (-1, -1), 12),
        ("TOPPADDING",   (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING",(0, 0), (-1, -1), 8),
    ]))
    elements.append(client_table)
    elements.append(Spacer(1, 22 * mm))

    # Jauge semi-circulaire centrée
    score = float(audit.global_score or 0)
    gauge = GaugeFlowable(score, width=200, height=120)
    gauge_table = Table([[gauge]], colWidths=[200])
    gauge_table.setStyle(TableStyle([("ALIGN", (0, 0), (-1, -1), "CENTER")]))
    elements.append(gauge_table)
    elements.append(Spacer(1, 8 * mm))

    # Niveau de risque dans un encadré coloré centré
    risk_color = RISK_COLORS.get(audit.risk_level or "", colors.HexColor(_C_SLATE))
    risk_label_text = _risk_label(audit.risk_level).upper()
    risk_style = ParagraphStyle(
        "risk_box_text", parent=styles["cover_center"],
        fontSize=11, fontName="Helvetica-Bold",
        textColor=risk_color, spaceAfter=0,
    )
    risk_data = [[Paragraph(f"Niveau de risque : {risk_label_text}", risk_style)]]
    risk_table = Table(risk_data, colWidths=[180])
    risk_table.setStyle(TableStyle([
        ("BOX",          (0, 0), (-1, -1), 1.5, risk_color),
        ("TOPPADDING",   (0, 0), (-1, -1), 7),
        ("BOTTOMPADDING",(0, 0), (-1, -1), 7),
        ("LEFTPADDING",  (0, 0), (-1, -1), 14),
        ("RIGHTPADDING", (0, 0), (-1, -1), 14),
    ]))
    risk_wrapper = Table([[risk_table]], colWidths=[page_width])
    risk_wrapper.setStyle(TableStyle([("ALIGN", (0, 0), (-1, -1), "CENTER")]))
    elements.append(risk_wrapper)
    elements.append(Spacer(1, 8 * mm))

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
    elements.append(Spacer(1, 4 * mm))

    # Score post-correction si applicable
    corrected = _compute_corrected_score(audit)
    if corrected:
        elements.append(Spacer(1, 4 * mm))
        correction_style = ParagraphStyle(
            "correction_cover", parent=styles["cover_small"],
            fontSize=10, textColor=colors.HexColor(_C_CONFORME),
        )
        elements.append(Paragraph(
            f"Score initial : <b>{float(audit.global_score or 0):.0f}/100</b> → "
            f"Score après {corrected['corrected_count']} correction(s) : "
            f"<b>{corrected['corrected_score']}/100</b> (risque {_risk_label(corrected['corrected_risk'])})",
            correction_style,
        ))

    elements.append(Spacer(1, 10 * mm))
    auditor_name = "GreenAudit" if is_starter else (partner.name or "GreenAudit")
    elements.append(Paragraph(
        f"Audit réalisé le {_format_date(audit.completed_at)} par {auditor_name}",
        styles["cover_small"],
    ))
    elements.append(NextPageTemplate("content"))
    elements.append(PageBreak())
    return elements


def _summary_elements(audit: Audit, styles: dict) -> list:
    """Section synthèse exécutive."""
    elements = []
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
        ("BACKGROUND",    (0, 0), (-1, 0),  colors.HexColor(_C_NAVY)),
        ("TEXTCOLOR",     (0, 0), (-1, 0),  colors.white),
        ("FONTNAME",      (0, 0), (-1, 0),  "Helvetica-Bold"),
        ("FONTSIZE",      (0, 0), (-1, -1), 10),
        ("ALIGN",         (0, 0), (-1, -1), "CENTER"),
        ("GRID",          (0, 0), (-1, -1), 0.5, colors.HexColor(_C_BORDER)),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ("TOPPADDING",    (0, 0), (-1, -1), 8),
        ("BACKGROUND",    (0, 1), (-1, 1),  colors.HexColor(_C_ALT)),
    ]))
    elements.append(KeepTogether([Paragraph("1. Synthèse exécutive", styles["h1"]), t]))
    elements.append(Spacer(1, 4 * mm))
    elements.append(Paragraph(
        f"Score global : <b>{float(audit.global_score or 0):.0f}/100</b> — Risque <b>{_risk_label(audit.risk_level)}</b>. "
        f"{_summary_phrase(audit.risk_level)}",
        styles["body"],
    ))

    # Progression post-correction
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
        prog_table = Table(
            prog_data,
            colWidths=[page_width * 0.30, page_width * 0.20, page_width * 0.25, page_width * 0.25],
        )
        prog_table.setStyle(TableStyle([
            ("BACKGROUND",    (0, 0), (-1, 0),  colors.HexColor(_C_NAVY)),
            ("TEXTCOLOR",     (0, 0), (-1, 0),  colors.white),
            ("FONTNAME",      (0, 0), (-1, 0),  "Helvetica-Bold"),
            ("BACKGROUND",    (0, 1), (-1, 1),  colors.HexColor(_C_ALT)),
            ("FONTSIZE",      (0, 0), (-1, -1), 9),
            ("ALIGN",         (0, 0), (-1, -1), "CENTER"),
            ("ALIGN",         (0, 0), (0, -1),  "LEFT"),
            ("GRID",          (0, 0), (-1, -1), 0.5, colors.HexColor(_C_BORDER)),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ("TOPPADDING",    (0, 0), (-1, -1), 6),
            ("TEXTCOLOR",     (1, 2), (1, 2),   colors.HexColor(_C_CONFORME)),
            ("FONTNAME",      (1, 2), (1, 2),   "Helvetica-Bold"),
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
    claims = [c for c in (audit.claims or []) if not getattr(c, "is_false_positive", False)]
    corrected_count = sum(1 for c in claims if getattr(c, "is_corrected", False))
    if corrected_count == 0:
        return None

    total = len(claims)
    if total == 0:
        return None

    conforming = audit.conforming_claims or 0
    at_risk    = audit.at_risk_claims or 0

    corrected_conforming = conforming
    corrected_at_risk    = at_risk
    for claim in claims:
        if not getattr(claim, "is_corrected", False):
            continue
        verdict = claim.overall_verdict
        if verdict == "non_conforme":
            corrected_conforming += 1
        elif verdict == "risque":
            corrected_conforming += 1
            corrected_at_risk = max(0, corrected_at_risk - 1)

    corrected_nc = max(0, total - corrected_conforming - corrected_at_risk)
    corrected_score = round((corrected_conforming * 100 + corrected_at_risk * 50) / total)

    if corrected_score >= 80:
        corrected_risk = "faible"
    elif corrected_score >= 60:
        corrected_risk = "modere"
    elif corrected_score >= 40:
        corrected_risk = "eleve"
    else:
        corrected_risk = "critique"

    return {
        "corrected_count":     corrected_count,
        "corrected_score":     corrected_score,
        "corrected_risk":      corrected_risk,
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
            else:
                scores_by_criterion[r.criterion].append(0)

    result = {}
    for criterion, vals in scores_by_criterion.items():
        if vals:
            result[criterion] = sum(vals) / len(vals)
    return result


def _radar_elements(claims: list, styles: dict) -> list:
    """Section radar chart par critère."""
    elements = []

    scores = _compute_radar_scores(claims)
    if not scores:
        elements.append(KeepTogether([
            Paragraph("2. Conformité par critère", styles["h1"]),
            Paragraph("Données insuffisantes pour générer le graphique.", styles["body"]),
        ]))
        return elements

    radar = RadarChartFlowable(scores, width=360, height=290)
    radar_table = Table([[radar]], colWidths=[360])
    radar_table.setStyle(TableStyle([("ALIGN", (0, 0), (-1, -1), "CENTER")]))
    elements.append(KeepTogether([Paragraph("2. Conformité par critère", styles["h1"]), radar_table]))
    elements.append(Spacer(1, 4 * mm))
    elements.append(Paragraph(
        "Score par critère : 100% = tous conformes · 50% = risque · 0% = non conforme. "
        "Les critères N/A sont exclus.",
        styles["small"],
    ))
    return elements


def _claims_detail_elements(claims: list, styles: dict, is_starter: bool = False) -> list:
    """Section détail des allégations — affichage différencié liste_noire / cas_par_cas."""
    elements = []
    h1_title = Paragraph("3. Détail des allégations", styles["h1"])

    page_width  = A4[0] - 40 * mm
    inner_width = page_width - 16  # padding 8pt de chaque côté

    claims = [c for c in claims if not getattr(c, "is_false_positive", False)]
    first_claim = True

    for i, claim in enumerate(claims, 1):
        verdict          = VERDICT_LABELS.get(claim.overall_verdict or "", "—")
        support          = SUPPORT_LABELS.get(claim.support_type, claim.support_type)
        scope            = "Entreprise" if claim.scope == "entreprise" else "Produit"
        is_liste_noire   = getattr(claim, "regime", None) == "liste_noire"
        regulatory_basis = getattr(claim, "regulatory_basis", None)
        article_label    = REGULATORY_BASIS_LABELS.get(regulatory_basis or "", "")

        c_conf = sum(1 for r in claim.results if r.verdict == "conforme")
        c_risk = sum(1 for r in claim.results if r.verdict == "risque")
        c_nc   = sum(1 for r in claim.results if r.verdict == "non_conforme")
        c_na   = sum(1 for r in claim.results if r.verdict == "non_applicable")

        n_issues = _count_issues(claim)
        is_alert = n_issues >= 3

        claim_elements = []

        # --- Titre (TÂCHE 1 + 2) ---
        if is_liste_noire:
            interdit_label = (
                f"Allégation #{i} — [INTERDIT] {article_label}"
                if article_label else f"Allégation #{i} — [INTERDIT]"
            )
            claim_elements.append(Paragraph(interdit_label, styles["h2_alert"]))
        elif is_alert:
            title_text = f"Allégation #{i} — {verdict}"
            if article_label:
                title_text += f" · {article_label}"
            claim_elements.append(Paragraph(title_text, styles["h2_alert"]))
        else:
            title_text = f"Allégation #{i} — {verdict}"
            if article_label:
                title_text += f" · {article_label}"
            claim_elements.append(Paragraph(title_text, styles["h2"]))

        claim_elements.append(Paragraph(
            f"<i>« {_rl_escape(claim.claim_text)} »</i>", styles["italic"],
        ))
        claim_elements.append(Paragraph(
            f"Support : {support} | Portée : {scope}", styles["small"],
        ))
        _src_url = getattr(claim, "source_url", None)
        if _src_url:
            _display = (_src_url[:77] + "…") if len(_src_url) > 80 else _src_url
            claim_elements.append(Paragraph(
                f'Page source : <link href="{_src_url}">{_rl_escape(_display)}</link>',
                styles["small"],
            ))
        claim_elements.append(Spacer(1, 2 * mm))

        # Barre de progression
        bar = ProgressBarFlowable(c_conf, c_risk, c_nc, c_na, width=inner_width - 40, height=12)
        claim_elements.append(bar)
        claim_elements.append(Spacer(1, 2 * mm))

        sorted_results = sorted(
            claim.results,
            key=lambda r: CRITERION_ORDER.index(r.criterion) if r.criterion in CRITERION_ORDER else 99,
        )

        if is_liste_noire:
            # --- TÂCHE 1 : tableau simplifié liste_noire (règles violées uniquement) ---
            data = [[
                Paragraph("<b>Règle violée</b>",  styles["small"]),
                Paragraph("<b>Explication</b>",   styles["small"]),
            ]]
            for r in sorted_results:
                if r.verdict == "non_applicable":
                    continue
                crit_label = CRITERION_LABELS.get(r.criterion, r.criterion)
                v_label    = VERDICT_LABELS.get(r.verdict, r.verdict)
                data.append([
                    Paragraph(
                        f"<b>{_rl_escape(crit_label)}</b> — "
                        f"<font color='{_C_CRITIQUE}'>{_rl_escape(v_label)}</font>",
                        styles["small"],
                    ),
                    Paragraph(_rl_escape(r.explanation or ""), styles["small"]),
                ])
            if len(data) > 1:
                t = Table(data, colWidths=[inner_width * 0.30, inner_width * 0.70], repeatRows=1)
                t.setStyle(TableStyle([
                    ("BACKGROUND",    (0, 0), (-1, 0),  colors.HexColor(_C_CRITIQUE)),
                    ("TEXTCOLOR",     (0, 0), (-1, 0),  colors.white),
                    ("FONTNAME",      (0, 0), (-1, 0),  "Helvetica-Bold"),
                    ("FONTSIZE",      (0, 0), (-1, -1), 8),
                    ("VALIGN",        (0, 0), (-1, -1), "TOP"),
                    ("GRID",          (0, 0), (-1, -1), 0.5, colors.HexColor(_C_BORDER)),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                    ("TOPPADDING",    (0, 0), (-1, -1), 6),
                    ("LEFTPADDING",   (0, 0), (-1, -1), 5),
                    ("RIGHTPADDING",  (0, 0), (-1, -1), 5),
                    ("BACKGROUND",    (0, 1), (-1, -1), colors.HexColor("#fff1f2")),
                ]))
                claim_elements.append(t)
                claim_elements.append(Spacer(1, 2 * mm))

            # --- TÂCHE 5 : bloc exemple de reformulation ---
            hint = _reformulation_hint(regulatory_basis)
            if hint:
                hint_style = ParagraphStyle(
                    f"hint_{i}", parent=styles["small"],
                    fontSize=8, textColor=colors.HexColor(_C_STEEL), leading=11,
                )
                hint_table = Table(
                    [
                        [Paragraph("<b>Exemple de reformulation :</b>", hint_style)],
                        [Paragraph(_rl_escape(hint), hint_style)],
                    ],
                    colWidths=[inner_width - 8],
                )
                hint_table.setStyle(TableStyle([
                    ("BACKGROUND",    (0, 0), (-1, -1), colors.HexColor("#f0f9ff")),
                    ("LINEBEFORE",    (0, 0), (0, -1),  3, colors.HexColor(_C_STEEL)),
                    ("BOX",           (0, 0), (-1, -1), 0.5, colors.HexColor(_C_STEEL)),
                    ("TOPPADDING",    (0, 0), (-1, -1), 5),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                    ("LEFTPADDING",   (0, 0), (-1, -1), 8),
                    ("RIGHTPADDING",  (0, 0), (-1, -1), 5),
                ]))
                claim_elements.append(hint_table)
                claim_elements.append(Spacer(1, 2 * mm))

        else:
            # --- TÂCHE 6 : tableau cas_par_cas sans les N/A ---
            # Encadré alerte si 3+ problèmes
            if is_alert:
                issues = []
                for r in sorted_results:
                    if r.verdict in ("non_conforme", "risque"):
                        label         = CRITERION_LABELS.get(r.criterion, r.criterion)
                        verdict_label = VERDICT_LABELS.get(r.verdict, r.verdict)
                        issues.append(f"[{verdict_label}] {label} : {r.explanation or ''}")
                alert = AlertBoxFlowable(claim.claim_text, issues, width=inner_width)
                claim_elements.append(alert)
                claim_elements.append(Spacer(1, 3 * mm))

            if is_starter:
                header_row = [
                    Paragraph("<b>Critère</b>",     styles["small"]),
                    Paragraph("<b>Verdict</b>",     styles["small"]),
                    Paragraph("<b>Explication</b>", styles["small"]),
                ]
            else:
                header_row = [
                    Paragraph("<b>Critère</b>",       styles["small"]),
                    Paragraph("<b>Verdict</b>",        styles["small"]),
                    Paragraph("<b>Explication</b>",    styles["small"]),
                    Paragraph("<b>Recommandation</b>", styles["small"]),
                ]
            data = [header_row]
            reg_refs: set = set()

            for row_i, r in enumerate(sorted_results, 1):
                if r.verdict == "non_applicable":
                    continue  # filtrer les N/A (TÂCHE 6)
                if r.regulation_reference:
                    reg_refs.add(r.regulation_reference)

                if r.verdict == "conforme":
                    text_color = colors.HexColor(_C_CONFORME)
                elif r.verdict == "risque":
                    text_color = colors.HexColor(_C_RISQUE)
                elif r.verdict == "non_conforme":
                    text_color = colors.HexColor(_C_CRITIQUE)
                else:
                    text_color = colors.HexColor(_C_SLATE)

                verdict_style = ParagraphStyle(
                    f"v_{r.criterion}_{row_i}",
                    parent=styles["small"],
                    textColor=text_color,
                    fontName="Helvetica-Bold",
                )
                if is_starter:
                    data.append([
                        Paragraph(CRITERION_LABELS.get(r.criterion, r.criterion), styles["small"]),
                        Paragraph(VERDICT_LABELS.get(r.verdict, r.verdict), verdict_style),
                        Paragraph(_rl_escape(r.explanation or ""), styles["small"]),
                    ])
                else:
                    data.append([
                        Paragraph(CRITERION_LABELS.get(r.criterion, r.criterion), styles["small"]),
                        Paragraph(VERDICT_LABELS.get(r.verdict, r.verdict), verdict_style),
                        Paragraph(_rl_escape(r.explanation or ""), styles["small"]),
                        Paragraph(_rl_escape(r.recommendation or "—"), styles["small"]),
                    ])

            if len(data) > 1:
                if is_starter:
                    col_widths = [inner_width * 0.20, inner_width * 0.15, inner_width * 0.65]
                else:
                    col_widths = [inner_width * 0.17, inner_width * 0.13, inner_width * 0.40, inner_width * 0.30]
                t = Table(data, colWidths=col_widths, repeatRows=1)
                ts = TableStyle([
                    ("BACKGROUND",    (0, 0), (-1, 0),  colors.HexColor(_C_NAVY)),
                    ("TEXTCOLOR",     (0, 0), (-1, 0),  colors.white),
                    ("FONTNAME",      (0, 0), (-1, 0),  "Helvetica-Bold"),
                    ("FONTSIZE",      (0, 0), (-1, 0),  8),
                    ("FONTSIZE",      (0, 1), (-1, -1), 8),
                    ("ALIGN",         (0, 0), (-1, 0),  "LEFT"),
                    ("VALIGN",        (0, 0), (-1, -1), "TOP"),
                    ("GRID",          (0, 0), (-1, -1), 0.5, colors.HexColor(_C_BORDER)),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                    ("TOPPADDING",    (0, 0), (-1, -1), 6),
                    ("LEFTPADDING",   (0, 0), (-1, -1), 5),
                    ("RIGHTPADDING",  (0, 0), (-1, -1), 5),
                ])
                for row_i in range(1, len(data)):
                    if row_i % 2 == 1:
                        ts.add("BACKGROUND", (0, row_i), (-1, row_i), colors.HexColor(_C_ALT))
                t.setStyle(ts)
                claim_elements.append(t)
                claim_elements.append(Spacer(1, 2 * mm))

            if reg_refs:
                ref_text = " · ".join(sorted(reg_refs)[:4])
                claim_elements.append(Paragraph(
                    f"Réf. réglementaire{'s' if len(reg_refs) > 1 else ''} : {ref_text}",
                    styles["reg_ref"],
                ))

        # --- Badge "Corrigée" (commun) ---
        if getattr(claim, "is_corrected", False):
            corrected_at = getattr(claim, "corrected_at", None)
            date_str = f" le {corrected_at.strftime('%d/%m/%Y')}" if corrected_at else ""
            claim_elements.append(Paragraph(
                f"<font color='{_C_CONFORME}'><b>Corrigée{date_str}</b></font>",
                styles["small"],
            ))
            claim_elements.append(Spacer(1, 1 * mm))

        # --- Pièces justificatives (commun) ---
        evidence_files = getattr(claim, "evidence_files", [])
        if evidence_files:
            DOC_TYPE_LABELS = {
                "ecolabel":        "Écolabel",
                "certification":   "Certification",
                "rapport_interne": "Rapport interne",
                "autre":           "Autre",
            }
            ev_data = [[
                Paragraph("<b>Pièce justificative</b>", styles["small"]),
                Paragraph("<b>Type</b>",                styles["small"]),
                Paragraph("<b>Taille</b>",              styles["small"]),
                Paragraph("<b>Déposée le</b>",          styles["small"]),
            ]]
            for ef in evidence_files:
                size_kb     = round(getattr(ef, "file_size", 0) / 1024, 1)
                doc_label   = DOC_TYPE_LABELS.get(getattr(ef, "document_type", "autre"), "Autre")
                uploaded_at = getattr(ef, "uploaded_at", None)
                date_label  = uploaded_at.strftime("%d/%m/%Y %H:%M") if uploaded_at else "—"
                ev_data.append([
                    Paragraph(getattr(ef, "filename", "—"), styles["small"]),
                    Paragraph(doc_label,                    styles["small"]),
                    Paragraph(f"{size_kb} Ko",              styles["small"]),
                    Paragraph(date_label,                   styles["small"]),
                ])
            ev_table = Table(
                ev_data,
                colWidths=[inner_width*0.42, inner_width*0.22, inner_width*0.14, inner_width*0.22],
                repeatRows=1,
            )
            ev_table.setStyle(TableStyle([
                ("BACKGROUND",    (0, 0), (-1, 0),  colors.HexColor(_C_STEEL)),
                ("TEXTCOLOR",     (0, 0), (-1, 0),  colors.white),
                ("FONTNAME",      (0, 0), (-1, 0),  "Helvetica-Bold"),
                ("FONTSIZE",      (0, 0), (-1, -1), 8),
                ("ALIGN",         (0, 0), (-1, 0),  "LEFT"),
                ("VALIGN",        (0, 0), (-1, -1), "TOP"),
                ("GRID",          (0, 0), (-1, -1), 0.5, colors.HexColor(_C_BORDER)),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                ("TOPPADDING",    (0, 0), (-1, -1), 5),
                ("LEFTPADDING",   (0, 0), (-1, -1), 5),
                ("RIGHTPADDING",  (0, 0), (-1, -1), 5),
                ("BACKGROUND",    (0, 1), (-1, -1), colors.HexColor(_C_ALT)),
            ]))
            claim_elements.append(Paragraph("<b>Pièces justificatives</b>", styles["small"]))
            claim_elements.append(Spacer(1, 1 * mm))
            claim_elements.append(ev_table)
            claim_elements.append(Spacer(1, 2 * mm))

        if first_claim:
            elements.append(h1_title)
            elements.append(Spacer(1, 3 * mm))
            first_claim = False

        elements.extend(claim_elements)
        elements.append(Spacer(1, 5 * mm))

    return elements


_GOUVERNANCE_TEXT = (
    "Au-delà des corrections immédiates et de la constitution du dossier documentaire, "
    "nous recommandons les actions de gouvernance suivantes :"
)
_GOUVERNANCE_BULLETS = [
    "Mettre en place une procédure interne de validation des contenus environnementaux "
    "avant publication, impliquant les équipes marketing, communication et RSE.",
    "Conserver les preuves dans un dossier documentaire horodaté, organisé par allégation "
    "et accessible en cas de contrôle.",
    "Effectuer une revue semestrielle des communications environnementales pour anticiper "
    "l'évolution de la directive et de la jurisprudence DGCCRF.",
    "Former les équipes marketing et communication aux exigences de la directive 2024/825 "
    "et aux interdictions absolues de l'annexe I.",
    "Désigner un référent conformité environnementale au sein de l'organisation, point de "
    "contact unique pour les questions liées aux allégations.",
]


def _correction_plan_elements(claims: list, styles: dict) -> list:
    """
    Plan de correction en 3 niveaux :
    - Niveau 1 : tableau des allégations liste_noire (pratiques interdites Annexe I)
    - Niveau 2 : tableau des allégations cas_par_cas, 1 ligne par claim, critères fusionnés
    - Niveau 3 : bloc texte générique gouvernance (statique, identique pour tous les rapports)
    """
    elements = []

    niveau1: list = []  # (claim_short, article_label, action)
    # niveau2 : dict claim_text → {"criteres": [str], "actions": [str]}
    niveau2_map: dict = {}

    for claim in claims:
        if getattr(claim, "is_false_positive", False):
            continue
        if claim.overall_verdict == "conforme":
            continue

        is_liste_noire   = getattr(claim, "regime", None) == "liste_noire"
        regulatory_basis = getattr(claim, "regulatory_basis", None)
        article_label    = REGULATORY_BASIS_LABELS.get(regulatory_basis or "", "Annexe I")
        claim_short      = _smart_truncate(claim.claim_text, 55)

        if is_liste_noire:
            first_nc = next(
                (r for r in claim.results if r.verdict in ("non_conforme", "risque")), None
            )
            action = first_nc.recommendation if first_nc else "Supprimer ou reformuler l'allégation"
            _src = getattr(claim, "source_url", None)
            if _src:
                _path = urlparse(_src).path
                source_path = _path if _path and _path != "/" else "/"
            else:
                source_path = "—"
            niveau1.append((claim_short, source_path, article_label, action))
        else:
            # Tous les critères non-conformes/risque absorbés dans niveau 2
            for r in claim.results:
                if r.verdict not in ("non_conforme", "risque") or not r.recommendation:
                    continue
                if claim_short not in niveau2_map:
                    niveau2_map[claim_short] = {"criteres": [], "actions": []}
                crit_label = CRITERION_LABELS.get(r.criterion, r.criterion)
                if crit_label not in niveau2_map[claim_short]["criteres"]:
                    niveau2_map[claim_short]["criteres"].append(crit_label)
                if r.recommendation not in niveau2_map[claim_short]["actions"]:
                    niveau2_map[claim_short]["actions"].append(r.recommendation)

    # Aplatir niveau2_map en liste de lignes fusionnées
    niveau2 = [
        (
            claim_short,
            ", ".join(v["criteres"]),
            " ; ".join(v["actions"]),
        )
        for claim_short, v in niveau2_map.items()
    ]

    title = Paragraph("4. Plan de correction priorisé", styles["h1"])

    if not niveau1 and not niveau2:
        elements.append(KeepTogether([
            title, Paragraph("Aucune action corrective nécessaire.", styles["body"])
        ]))
        return elements

    elements.append(title)
    elements.append(Spacer(1, 3 * mm))

    page_width = A4[0] - 40 * mm

    def _render_niveau_table(num: str, description: str, color_hex: str, rows: list, col2_header: str):
        niveau_elements = []
        label_style = ParagraphStyle(
            f"niveau_lbl_{num}", parent=styles["body"],
            fontSize=9, fontName="Helvetica-Bold",
            textColor=colors.HexColor(color_hex),
        )
        niveau_elements.append(Paragraph(f"NIVEAU {num} — {description}", label_style))
        niveau_elements.append(Spacer(1, 1 * mm))
        is_4col = bool(rows) and len(rows[0]) == 4
        if is_4col:
            header_row = [
                Paragraph("<b>Allégation</b>",        styles["small"]),
                Paragraph("<b>Page</b>",               styles["small"]),
                Paragraph(f"<b>{col2_header}</b>",    styles["small"]),
                Paragraph("<b>Action corrective</b>", styles["small"]),
            ]
            col_widths = [page_width * 0.27, page_width * 0.18, page_width * 0.20, page_width * 0.35]
        else:
            header_row = [
                Paragraph("<b>Allégation</b>",        styles["small"]),
                Paragraph(f"<b>{col2_header}</b>",    styles["small"]),
                Paragraph("<b>Action corrective</b>", styles["small"]),
            ]
            col_widths = [page_width * 0.30, page_width * 0.22, page_width * 0.48]
        data = [header_row]
        for row in rows:
            data.append([Paragraph(str(cell), styles["small"]) for cell in row])
        t = Table(
            data,
            colWidths=col_widths,
            repeatRows=1,
        )
        ts = TableStyle([
            ("BACKGROUND",    (0, 0), (-1, 0),  colors.HexColor(color_hex)),
            ("TEXTCOLOR",     (0, 0), (-1, 0),  colors.white),
            ("FONTNAME",      (0, 0), (-1, 0),  "Helvetica-Bold"),
            ("FONTSIZE",      (0, 0), (-1, -1), 8),
            ("VALIGN",        (0, 0), (-1, -1), "TOP"),
            ("GRID",          (0, 0), (-1, -1), 0.5, colors.HexColor(_C_BORDER)),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ("TOPPADDING",    (0, 0), (-1, -1), 6),
            ("LEFTPADDING",   (0, 0), (-1, -1), 5),
            ("RIGHTPADDING",  (0, 0), (-1, -1), 5),
        ])
        for row_i in range(1, len(data)):
            if row_i % 2 == 1:
                ts.add("BACKGROUND", (0, row_i), (-1, row_i), colors.HexColor(_C_ALT))
        t.setStyle(ts)
        niveau_elements.append(t)
        niveau_elements.append(Spacer(1, 4 * mm))
        return niveau_elements

    if niveau1:
        elements.extend(_render_niveau_table(
            "1", "Corrections immédiates — Pratiques interdites Annexe I",
            _C_CRITIQUE, niveau1, "Article EmpCo",
        ))
    if niveau2:
        elements.extend(_render_niveau_table(
            "2", "Documentation — Dossier de conformité à compléter",
            _C_RISQUE, niveau2, "Critères concernés",
        ))

    # Niveau 3 — bloc texte générique gouvernance (statique)
    gov_label_style = ParagraphStyle(
        "niveau_lbl_3", parent=styles["body"],
        fontSize=9, fontName="Helvetica-Bold",
        textColor=colors.HexColor(_C_STEEL),
    )
    gov_body_style = ParagraphStyle(
        "gov_body", parent=styles["small"],
        fontSize=8, leading=12, textColor=colors.HexColor(_C_TEXT),
    )
    gov_bullet_style = ParagraphStyle(
        "gov_bullet", parent=styles["small"],
        fontSize=8, leading=12, textColor=colors.HexColor(_C_TEXT),
        leftIndent=10, firstLineIndent=-10,
    )
    elements.append(Paragraph("NIVEAU 3 — Gouvernance — Procédures internes et suivi", gov_label_style))
    elements.append(Spacer(1, 2 * mm))
    elements.append(Paragraph(_rl_escape(_GOUVERNANCE_TEXT), gov_body_style))
    elements.append(Spacer(1, 2 * mm))
    for bullet in _GOUVERNANCE_BULLETS:
        elements.append(Paragraph(f"– {_rl_escape(bullet)}", gov_bullet_style))
        elements.append(Spacer(1, 1 * mm))
    elements.append(Spacer(1, 3 * mm))

    elements.append(Paragraph(
        "<b>Date limite de mise en conformité directive EmpCo : 27 septembre 2026</b>",
        styles["deadline_footer"],
    ))
    return elements


def _financial_risk_elements(audit: Audit, styles: dict) -> list:
    """Section estimation du risque financier."""
    elements = []
    nc_count = audit.non_conforming_claims or 0
    page_width = A4[0] - 40 * mm

    warn_title_style = ParagraphStyle(
        "warn_title", parent=styles["body"],
        fontSize=9, fontName="Helvetica-Bold",
        textColor=colors.HexColor("#7c2d12"),
    )
    warn_item_style = ParagraphStyle(
        "warn_item", parent=styles["small"],
        fontSize=8, textColor=colors.HexColor("#7c2d12"), leading=11,
    )
    warn_summary_style = ParagraphStyle(
        "warn_summary", parent=styles["body"],
        fontSize=9, textColor=colors.HexColor("#7c2d12"),
    )
    warn_note_style = ParagraphStyle(
        "warn_note", parent=styles["small"],
        fontSize=7, textColor=colors.HexColor("#7c2d12"),
        leading=10, fontName="Helvetica-Oblique",
    )

    box_data = [
        [Paragraph("Sanctions encourues en cas de greenwashing avéré :", warn_title_style)],
        [Paragraph(
            "– Pratique commerciale trompeuse (Code conso. Art. L132-2) : "
            "jusqu'à 300 000 € d'amende et 2 ans d'emprisonnement (personnes physiques), "
            "jusqu'à 1 500 000 € pour les personnes morales.",
            warn_item_style,
        )],
        [Paragraph(
            "– Amende administrative DGCCRF : jusqu'à 100 000 € par infraction.",
            warn_item_style,
        )],
        [Paragraph(
            "– Injonction de cessation : retrait immédiat des communications non conformes.",
            warn_item_style,
        )],
        [Spacer(1, 2 * mm)],
        [Paragraph(
            f"Avec <b>{nc_count} allégation{'s' if nc_count > 1 else ''} non conforme{'s' if nc_count > 1 else ''}</b> "
            f"identifiée{'s' if nc_count > 1 else ''}, l'exposition potentielle est significative.",
            warn_summary_style,
        )],
        [Spacer(1, 2 * mm)],
        [Paragraph(
            "Note : Les sanctions sont déterminées par chaque État membre conformément à "
            "l'article 13 de la directive 2005/29/CE. Les montants ci-dessus correspondent "
            "au cadre légal français en vigueur à la date d'audit. "
            "Consultez un avocat pour une évaluation précise.",
            warn_note_style,
        )],
    ]

    t = Table(box_data, colWidths=[page_width - 8])
    t.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, -1), colors.HexColor("#fff7ed")),
        ("LINEBEFORE",    (0, 0), (0, -1),  4, colors.HexColor(_C_ELEVE)),
        ("BOX",           (0, 0), (-1, -1), 0.5, colors.HexColor(_C_ELEVE)),
        ("LEFTPADDING",   (0, 0), (-1, -1), 12),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 10),
        ("TOPPADDING",    (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    elements.append(KeepTogether([Paragraph("5. Exposition aux sanctions", styles["h1"]), t]))
    return elements


def _labels_checklist_elements(claims: list, styles: dict) -> list:
    """Section checklist labels."""
    to_remove = []
    to_keep   = []
    for claim in claims:
        if not claim.has_label:
            continue
        name = claim.label_name or "Label non précisé"
        if claim.label_is_certified:
            to_keep.append(name)
        else:
            to_remove.append(name)

    elements = []

    if not to_remove and not to_keep:
        no_label = Paragraph("Aucun label déclaré dans cet audit.", styles["body"])
        elements.append(KeepTogether([Paragraph("6. Checklist labels", styles["h1"]), no_label]))
        return elements

    first_item = (
        Paragraph("Labels à retirer (auto-décernés) :", styles["body"])
        if to_remove
        else Paragraph("Labels conformes à conserver :", styles["body"])
    )
    elements.append(KeepTogether([Paragraph("6. Checklist labels", styles["h1"]), first_item]))
    if to_remove:
        elements.append(Paragraph("Labels à retirer (auto-décernés) :", styles["body"]))
        for name in to_remove:
            elements.append(Paragraph(f"  – {name}", styles["body"]))
    if to_keep:
        elements.append(Paragraph("Labels conformes à conserver :", styles["body"]))
        for name in to_keep:
            elements.append(Paragraph(f"  – {name}", styles["body"]))
    return elements


def _upgrade_banner_elements(section_title: str, styles: dict) -> list:
    """Encadré 'Disponible en plan Pro' pour les sections bridées en Starter."""
    elements = []
    elements.append(Paragraph(section_title, styles["h1"]))
    page_width = A4[0] - 40 * mm
    banner_style = ParagraphStyle(
        "upgrade_text", parent=styles["body"],
        fontSize=9, textColor=colors.HexColor(_C_STEEL), leading=13,
    )
    banner_data = [[Paragraph(
        "<b>Disponible avec le plan Pro</b><br/>"
        "Cette section est réservée aux partenaires Pro et Enterprise. "
        "Passez au plan Pro pour accéder au rapport complet : plan de correction priorisé, "
        "exposition aux sanctions, références réglementaires détaillées et checklist labels.",
        banner_style,
    )]]
    t = Table(banner_data, colWidths=[page_width])
    t.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, -1), colors.HexColor(_C_ALT)),
        ("LINEBEFORE",    (0, 0), (0, -1),  4, colors.HexColor(_C_NAVY)),
        ("BOX",           (0, 0), (-1, -1), 0.5, colors.HexColor(_C_BORDER)),
        ("LEFTPADDING",   (0, 0), (-1, -1), 14),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 14),
        ("TOPPADDING",    (0, 0), (-1, -1), 12),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 12),
    ]))
    elements.append(t)
    elements.append(Spacer(1, 6 * mm))
    return elements


def _references_elements(styles: dict) -> list:
    """Section références réglementaires."""
    elements = []
    page_width = A4[0] - 40 * mm
    data = [
        [
            Paragraph("<b>Texte</b>",      styles["small"]),
            Paragraph("<b>Référence</b>",  styles["small"]),
            Paragraph("<b>Objet</b>",      styles["small"]),
        ],
        [
            Paragraph("Directive EmpCo",          styles["small"]),
            Paragraph("EU 2024/825",              styles["small"]),
            Paragraph("Modifie la directive 2005/29/CE — protection des consommateurs contre le greenwashing", styles["small"]),
        ],
        [
            Paragraph("Annexe I, point 2bis",     styles["small"]),
            Paragraph("Dir. 2005/29/CE modifiée", styles["small"]),
            Paragraph("Interdiction des labels de durabilité non certifiés par un tiers ou une autorité publique", styles["small"]),
        ],
        [
            Paragraph("Annexe I, point 4bis",     styles["small"]),
            Paragraph("Dir. 2005/29/CE modifiée", styles["small"]),
            Paragraph("Interdiction des allégations environnementales génériques sans performance excellente reconnue", styles["small"]),
        ],
        [
            Paragraph("Annexe I, point 4ter",     styles["small"]),
            Paragraph("Dir. 2005/29/CE modifiée", styles["small"]),
            Paragraph("Interdiction des allégations sur l'ensemble du produit/entreprise ne concernant qu'un aspect", styles["small"]),
        ],
        [
            Paragraph("Annexe I, point 4quater",  styles["small"]),
            Paragraph("Dir. 2005/29/CE modifiée", styles["small"]),
            Paragraph("Interdiction de la neutralité carbone par compensation d'émissions (CO<sub>2</sub>)", styles["small"]),
        ],
        [
            Paragraph("Annexe I, point 10bis",    styles["small"]),
            Paragraph("Dir. 2005/29/CE modifiée", styles["small"]),
            Paragraph("Interdiction de présenter des exigences légales comme avantage distinctif", styles["small"]),
        ],
        [
            Paragraph("Art. 6.2(d)",              styles["small"]),
            Paragraph("Dir. 2005/29/CE modifiée", styles["small"]),
            Paragraph("Engagements futurs : plan détaillé, objectifs mesurables, vérification indépendante", styles["small"]),
        ],
        [
            Paragraph("Loi AGEC",                 styles["small"]),
            Paragraph("Loi n° 2020-105",          styles["small"]),
            Paragraph("Interdiction mentions « biodégradable » et « respectueux de l'environnement » (Art. 13)", styles["small"]),
        ],
        [
            Paragraph("Code de la consommation",  styles["small"]),
            Paragraph("Art. L121-1+",             styles["small"]),
            Paragraph("Pratiques commerciales trompeuses", styles["small"]),
        ],
    ]
    t = Table(
        data,
        colWidths=[page_width * 0.20, page_width * 0.20, page_width * 0.60],
        repeatRows=1,
    )
    ts = TableStyle([
        ("BACKGROUND",    (0, 0), (-1, 0),  colors.HexColor(_C_NAVY)),
        ("TEXTCOLOR",     (0, 0), (-1, 0),  colors.white),
        ("FONTNAME",      (0, 0), (-1, 0),  "Helvetica-Bold"),
        ("FONTSIZE",      (0, 0), (-1, -1), 8),
        ("VALIGN",        (0, 0), (-1, -1), "TOP"),
        ("GRID",          (0, 0), (-1, -1), 0.5, colors.HexColor(_C_BORDER)),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING",    (0, 0), (-1, -1), 6),
        ("LEFTPADDING",   (0, 0), (-1, -1), 5),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 5),
    ])
    for row_i in range(1, len(data)):
        if row_i % 2 == 1:
            ts.add("BACKGROUND", (0, row_i), (-1, row_i), colors.HexColor(_C_ALT))
    t.setStyle(ts)
    elements.append(KeepTogether([Paragraph("7. Références réglementaires", styles["h1"]), t]))
    return elements


def _disclaimer_elements(partner: Partner, styles: dict, is_starter: bool = False) -> list:
    """Section avertissement final."""
    elements = []
    elements.append(Spacer(1, 10 * mm))
    elements.append(HRFlowable(
        width="100%", thickness=0.5,
        color=colors.HexColor(_C_BORDER), spaceAfter=6 * mm,
    ))
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
            "de correction, le plan d'action priorisé, l'exposition aux sanctions et les références réglementaires. "
            "Contactez-nous sur green-audit.fr pour passer au plan Pro.",
            styles["disclaimer"],
        ))
    else:
        contact_parts = [
            p for p in [
                partner.name, partner.contact_name,
                _format_phone(partner.contact_phone or "") or None, partner.contact_email,
            ] if p
        ]
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

    claims  = sorted(audit.claims, key=lambda c: c.created_at)
    primary = _hex(partner.brand_primary_color)
    secondary = _hex(partner.brand_secondary_color, _C_STEEL)
    styles  = _build_styles(primary, secondary)

    storage_path = Path(settings.PDF_STORAGE_PATH)
    storage_path.mkdir(parents=True, exist_ok=True)

    import secrets as _secrets
    nonce    = _secrets.token_hex(8)
    filename = f"greenaudit_{audit.id}_{nonce}.pdf"
    filepath = str(storage_path / filename)

    doc = _build_doc(filepath, partner, is_starter=is_starter)

    _sep = lambda: Spacer(1, 10 * mm)

    elements = []
    elements.extend(_cover_elements(audit, partner, styles, is_starter=is_starter))
    elements.append(_sep())
    elements.extend(_summary_elements(audit, styles))
    elements.append(_sep())
    elements.extend(_radar_elements(claims, styles))
    elements.append(_sep())
    elements.extend(_claims_detail_elements(claims, styles, is_starter=is_starter))
    elements.append(_sep())
    if is_starter:
        elements.extend(_upgrade_banner_elements("4. Plan de correction priorisé", styles))
        elements.append(_sep())
        elements.extend(_upgrade_banner_elements("5. Exposition aux sanctions", styles))
        elements.append(_sep())
        elements.extend(_upgrade_banner_elements("7. Références réglementaires", styles))
    else:
        elements.extend(_correction_plan_elements(claims, styles))
        elements.append(_sep())
        elements.extend(_financial_risk_elements(audit, styles))
        elements.append(_sep())
        elements.extend(_labels_checklist_elements(claims, styles))
        elements.append(_sep())
        elements.extend(_references_elements(styles))
    elements.extend(_disclaimer_elements(partner, styles, is_starter=is_starter))

    doc.build(elements)

    sha256 = hashlib.sha256(Path(filepath).read_bytes()).hexdigest()
    _stamp_sha256(filepath, sha256, audit.id)

    return filename, sha256


def _stamp_sha256(filepath: str, sha256: str, audit_id) -> None:
    """Ajoute une ligne SHA-256 en bas de la dernière page du PDF."""
    try:
        from reportlab.pdfgen import canvas as rl_canvas
        from reportlab.lib.pagesizes import A4
        import io
        from pypdf import PdfReader, PdfWriter

        packet = io.BytesIO()
        c = rl_canvas.Canvas(packet, pagesize=A4)
        c.setFont("Helvetica", 6)
        c.setFillColorRGB(0.6, 0.6, 0.6)
        text = f"SHA-256 : {sha256} — Rapport #{str(audit_id)[:8].upper()}"
        c.drawCentredString(A4[0] / 2, 6 * mm, text)
        c.save()
        packet.seek(0)

        overlay_reader = PdfReader(packet)
        overlay_page   = overlay_reader.pages[0]

        reader = PdfReader(filepath)
        writer = PdfWriter()
        for i, page in enumerate(reader.pages):
            if i == len(reader.pages) - 1:
                page.merge_page(overlay_page)
            writer.add_page(page)

        with open(filepath, "wb") as f:
            writer.write(f)
    except Exception:
        pass  # Si pypdf n'est pas installé, le hash est quand même en base
