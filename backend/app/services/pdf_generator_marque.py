"""
Rapport PDF commercial marque — GreenAudit
4 pages, brandé GreenAudit, destiné à la marque auditée en direct.
Livrable payant — NE PAS confondre avec le rapport cabinet (pdf_generator.py).
"""

from __future__ import annotations

import hashlib
import json
import logging
import math
import re
import secrets
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from urllib.parse import urlparse

logger = logging.getLogger(__name__)

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (
    BaseDocTemplate,
    Frame,
    HRFlowable,
    KeepTogether,
    PageBreak,
    PageTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
)

from app.config import settings
from app.models.audit import Audit
from app.services.pdf_generator import (
    REGULATORY_BASIS_LABELS,
    GaugeFlowable,
    _reformulation_hint,
    _rl_escape,
)

# ── Palette GreenAudit ──────────────────────────────────────────────────────

_GA_GREEN    = "#1B5E20"
_GA_GREEN2   = "#2E7D32"
_GA_GREEN_LT = "#E8F5E9"
_GA_GREEN_BD = "#C8E6C9"
_GA_TEXT     = "#1e293b"
_GA_SLATE    = "#64748b"
_GA_WHITE    = "#FFFFFF"
_GA_RED      = "#b91c1c"
_GA_RED_LT   = "#FEF2F2"
_GA_AMBER    = "#b45309"
_GA_AMBER_LT = "#FFFBEB"
_GA_FOREST   = "#15803d"

_EMPCO_DEADLINE = "27 septembre 2026"

# ── Helpers ─────────────────────────────────────────────────────────────────

def _c(hex_str: str) -> colors.Color:
    return colors.HexColor(hex_str)


def _message_cle(score: float, non_conforming: int) -> str:
    if score <= 40:
        return (
            f"Votre communication environnementale présente une exposition réglementaire "
            f"importante à l'approche de l'échéance du {_EMPCO_DEADLINE}. "
            f"{non_conforming} allégation(s) relèvent directement de la liste noire EmpCo "
            f"et requièrent une action immédiate pour éviter des sanctions DGCCRF."
        )
    elif score <= 60:
        return (
            f"Votre diagnostic révèle des allégations à risque qui nécessitent une attention "
            f"prioritaire avant l'entrée en vigueur de la directive EmpCo. "
            f"Des reformulations ciblées permettront de sécuriser votre communication "
            f"environnementale avant le {_EMPCO_DEADLINE}."
        )
    elif score <= 80:
        return (
            f"Votre communication présente des points d'amélioration ciblés. "
            f"Les allégations identifiées peuvent être corrigées sans refonte majeure "
            f"de votre stratégie environnementale. Une mise à jour avant le {_EMPCO_DEADLINE} "
            f"suffit à sécuriser votre exposition réglementaire."
        )
    else:
        return (
            f"Votre communication environnementale est globalement conforme aux exigences EmpCo. "
            f"Quelques ajustements mineurs permettront de consolider votre dossier "
            f"de conformité avant l'échéance du {_EMPCO_DEADLINE}."
        )


def _risk_label_upper(risk_level: Optional[str]) -> str:
    labels = {
        "faible": "FAIBLE",
        "modere": "MODÉRÉ",
        "eleve": "ÉLEVÉ",
        "critique": "CRITIQUE",
    }
    return labels.get(risk_level or "", (risk_level or "—").upper())


def _risk_color(risk_level: Optional[str]) -> str:
    return {
        "faible": _GA_FOREST,
        "modere": _GA_AMBER,
        "eleve": "#c2410c",
        "critique": _GA_RED,
    }.get(risk_level or "", _GA_RED)


def _reg_basis_short(basis: Optional[str]) -> str:
    full = REGULATORY_BASIS_LABELS.get(basis or "", basis or "—")
    return full.split(" — ")[0] if " — " in full else full


def _sanitize_text(text: str) -> str:
    """Remplace les caractères Unicode hors palette Helvetica par leurs équivalents ASCII.
    Helvetica dans ReportLab ne supporte pas les indices/exposants Unicode (U+2080–U+209F) —
    ils s'affichent en ■. On normalise en texte plain.
    """
    _SUBSCRIPT_MAP = str.maketrans(
        "₀₁₂₃₄₅₆₇₈₉",
        "0123456789",
    )
    return text.translate(_SUBSCRIPT_MAP)


def _word_truncate(text: str, max_chars: int) -> str:
    """Tronque au dernier espace avant max_chars — jamais en milieu de mot."""
    if len(text) <= max_chars:
        return text
    cut = text[:max_chars]
    last_space = cut.rfind(" ")
    if last_space > max_chars // 2:
        return cut[:last_space] + "…"
    return cut + "…"


def _claim_problem_line(claim) -> str:
    """Retourne 1-2 phrases complètes depuis l'explication — jamais tronqué en milieu de phrase."""
    for r in (claim.results or []):
        if r.verdict in ("non_conforme", "risque") and r.explanation:
            exp = r.explanation.strip()
            # Split on sentence boundaries and take at most 2 complete sentences
            sentences = re.split(r"(?<=[.!?])\s+", exp)
            return " ".join(sentences[:2])
    return "Allégation non conforme aux exigences EmpCo."


def _select_priority_claims(claims: list, max_claims: int = 6) -> list:
    """Sélectionne les allégations les plus graves en priorité liste noire EmpCo."""
    PRIORITY = [
        ("non_conforme", "liste_noire", "annexe_I_4quater"),
        ("non_conforme", "liste_noire", "annexe_I_4bis"),
        ("non_conforme", "liste_noire", "annexe_I_4ter"),
        ("non_conforme", "liste_noire", "annexe_I_2bis"),
        ("non_conforme", "liste_noire", "annexe_I_10bis"),
        ("non_conforme", "cas_par_cas", None),
        ("risque", None, None),
    ]
    seen: list = []
    for verdict, regime, basis in PRIORITY:
        for claim in claims:
            if claim in seen or getattr(claim, "is_false_positive", False):
                continue
            if claim.overall_verdict != verdict:
                continue
            if regime and getattr(claim, "regime", None) != regime:
                continue
            if basis and getattr(claim, "regulatory_basis", None) != basis:
                continue
            seen.append(claim)
            if len(seen) >= max_claims:
                return seen
    if len(seen) < 4:
        for claim in claims:
            if (
                claim not in seen
                and not getattr(claim, "is_false_positive", False)
                and claim.overall_verdict == "non_conforme"
            ):
                seen.append(claim)
                if len(seen) >= max_claims:
                    break
    return seen[:max_claims]


# ── Styles ──────────────────────────────────────────────────────────────────

def _styles() -> Dict[str, ParagraphStyle]:
    return {
        "h1": ParagraphStyle("h1_m", fontSize=16, fontName="Helvetica-Bold",
                              textColor=_c(_GA_GREEN), spaceAfter=3),
        "h2": ParagraphStyle("h2_m", fontSize=11, fontName="Helvetica-Bold",
                              textColor=_c(_GA_GREEN), spaceAfter=3),
        "body": ParagraphStyle("body_m", fontSize=9, fontName="Helvetica",
                               textColor=_c(_GA_TEXT), leading=13, spaceAfter=2),
        "small": ParagraphStyle("small_m", fontSize=7.5, fontName="Helvetica",
                                textColor=_c(_GA_SLATE), leading=10, spaceAfter=1),
        "msg": ParagraphStyle("msg_m", fontSize=9, fontName="Helvetica",
                              textColor=_c(_GA_TEXT), leading=14),
    }


# ── Footer ───────────────────────────────────────────────────────────────────

def _footer(canvas, doc):
    canvas.saveState()
    left  = doc.leftMargin
    right = A4[0] - doc.rightMargin
    canvas.setStrokeColor(_c(_GA_GREEN_BD))
    canvas.setLineWidth(0.5)
    canvas.line(left, 18 * mm, right, 18 * mm)
    canvas.setFont("Helvetica", 7)
    canvas.setFillColor(_c(_GA_SLATE))
    canvas.drawString(left, 13 * mm, "GreenAudit — Diagnostic confidentiel")
    canvas.drawRightString(right, 13 * mm, f"Page {canvas.getPageNumber()}")
    canvas.restoreState()


# ── Page 1 — Synthèse exécutive ─────────────────────────────────────────────

def _page1(audit: Audit, st: dict) -> list:
    score = float(audit.global_score or 0)
    risk  = audit.risk_level or "critique"
    total = audit.total_claims or 0
    conf  = audit.conforming_claims or 0
    rc    = audit.at_risk_claims or 0
    nc    = audit.non_conforming_claims or 0
    date  = audit.completed_at.strftime("%d/%m/%Y") if audit.completed_at else "—"

    elems: list = []

    # Header band
    hdr = Table([[
        Paragraph(
            f"<font color='{_GA_WHITE}'><b>DIAGNOSTIC DE CONFORMITÉ EmpCo</b></font>",
            ParagraphStyle("hdr_l", fontSize=13, fontName="Helvetica-Bold",
                           textColor=_c(_GA_WHITE), leading=16),
        ),
        Paragraph(
            f"<font color='{_GA_WHITE}'><b>{_rl_escape(audit.company_name or '')}</b><br/>"
            f"<font size='8'>{date}</font></font>",
            ParagraphStyle("hdr_r", fontSize=10, fontName="Helvetica",
                           textColor=_c(_GA_WHITE), leading=13, alignment=2),
        ),
    ]], colWidths=["60%", "40%"])
    hdr.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), _c(_GA_GREEN)),
        ("TOPPADDING",    (0, 0), (-1, -1), 10),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
        ("LEFTPADDING",   (0, 0), (0, -1), 12),
        ("RIGHTPADDING",  (-1, 0), (-1, -1), 12),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ]))
    elems.append(hdr)
    elems.append(Spacer(1, 14))

    # Gauge — centred
    gauge_row = Table([[GaugeFlowable(score, 200, 130)]], colWidths=["100%"])
    gauge_row.setStyle(TableStyle([("ALIGN", (0, 0), (-1, -1), "CENTER")]))
    elems.append(gauge_row)
    elems.append(Spacer(1, 8))

    # Risk level chip
    rc_color  = _risk_color(risk)
    risk_chip = Table([[
        Paragraph(
            f"<font color='{_GA_WHITE}'><b>NIVEAU DE RISQUE : {_risk_label_upper(risk)}</b></font>",
            ParagraphStyle("chip", fontSize=10, fontName="Helvetica-Bold",
                           textColor=_c(_GA_WHITE), alignment=1),
        )
    ]], colWidths=["100%"])
    risk_chip.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, -1), _c(rc_color)),
        ("TOPPADDING",    (0, 0), (-1, -1), 7),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
    ]))
    elems.append(risk_chip)
    elems.append(Spacer(1, 12))

    # Distribution — 4 boxes in one row
    num_style = ParagraphStyle("num_d", fontSize=20, fontName="Helvetica-Bold", alignment=1)
    lbl_style = ParagraphStyle("lbl_d", fontSize=7.5, fontName="Helvetica",
                               textColor=_c(_GA_SLATE), alignment=1)
    boxes = [
        (total, "analysées",    _GA_TEXT),
        (conf,  "conformes",    _GA_FOREST),
        (rc,    "à risque",     _GA_AMBER),
        (nc,    "non conformes", _GA_RED),
    ]
    row1, row2 = [], []
    for val, lbl, col in boxes:
        row1.append(Paragraph(f"<font color='{col}'><b>{val}</b></font>", num_style))
        row2.append(Paragraph(lbl, lbl_style))
    dist = Table([row1, row2], colWidths=["25%"] * 4)
    dist.setStyle(TableStyle([
        ("BOX", (c, 0), (c, 1), 0.5, _c(_GA_GREEN_BD)) for c in range(4)
    ] + [
        ("TOPPADDING",    (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("ALIGN",  (0, 0), (-1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ]))
    elems.append(dist)
    elems.append(Spacer(1, 14))

    # Message clé
    msg_box = Table([[
        Paragraph("MESSAGE CLÉ",
                  ParagraphStyle("mk_lbl", fontSize=7, fontName="Helvetica-Bold",
                                 textColor=_c(_GA_SLATE))),
        Paragraph(_rl_escape(_message_cle(score, nc)), st["msg"]),
    ]], colWidths=["16%", "84%"])
    msg_box.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, -1), _c(_GA_GREEN_LT)),
        ("BOX",           (0, 0), (-1, -1), 1,  _c(_GA_GREEN2)),
        ("LINEBEFORE",    (0, 0), (0, -1),  3,  _c(_GA_GREEN)),
        ("TOPPADDING",    (0, 0), (-1, -1), 10),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
        ("LEFTPADDING",   (0, 0), (-1, -1), 10),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 10),
        ("VALIGN",        (0, 0), (-1, -1), "TOP"),
    ]))
    elems.append(msg_box)
    elems.append(PageBreak())
    return elems


# ── Page 2 — Allégations prioritaires ───────────────────────────────────────

def _page2(audit: Audit, st: dict) -> list:
    elems: list = []
    priority = _select_priority_claims(audit.claims or [], max_claims=6)
    count = len(priority)

    elems.append(Paragraph("Les allégations qui exposent votre marque", st["h1"]))
    elems.append(HRFlowable(width="100%", color=_c(_GA_GREEN2), thickness=1.5))
    elems.append(Spacer(1, 5))

    if count == 0:
        elems.append(Paragraph("Aucune allégation critique détectée.", st["body"]))
        elems.append(PageBreak())
        return elems

    ln_sel  = sum(1 for c in priority if getattr(c, "regime", None) == "liste_noire")
    cpc_sel = count - ln_sel
    if ln_sel > 0 and cpc_sel > 0:
        subtitle = (
            f"Sélection des allégations les plus exposées : "
            f"{ln_sel} relèvent de la liste noire (Annexe I), "
            f"{cpc_sel} relève{'nt' if cpc_sel > 1 else ''} de l'article 6."
        )
    elif ln_sel > 0:
        subtitle = (
            f"Sélection des {ln_sel} allégation{'s' if ln_sel > 1 else ''} "
            f"les plus exposées — toutes relèvent de la liste noire (Annexe I)."
        )
    else:
        subtitle = (
            f"Sélection des {count} allégation{'s' if count > 1 else ''} "
            f"les plus exposées — article 6 EmpCo."
        )
    elems.append(Paragraph(subtitle, st["small"]))
    elems.append(Spacer(1, 8))

    for i, claim in enumerate(priority):
        nc_color = _GA_RED if claim.overall_verdict == "non_conforme" else _GA_AMBER
        nc_bg    = _GA_RED_LT if claim.overall_verdict == "non_conforme" else _GA_AMBER_LT

        claim_text = _sanitize_text(claim.claim_text or "")
        if len(claim_text) > 130:
            claim_text = _word_truncate(claim_text, 130)

        source_line = ""
        if getattr(claim, "source_url", None):
            try:
                parsed = urlparse(claim.source_url)
                path   = parsed.path[:35] + "…" if len(parsed.path) > 35 else parsed.path
                source_line = (
                    f"<br/><font size='7' color='{_GA_SLATE}'>Source : {parsed.netloc}{path}</font>"
                )
            except Exception:
                pass

        problem    = _sanitize_text(_claim_problem_line(claim))
        reg_basis  = _reg_basis_short(claim.regulatory_basis)

        block = Table(
            [
                [
                    Paragraph(
                        f"<font color='{nc_color}'><b>#{i+1}</b></font>",
                        ParagraphStyle(f"n{i}", fontSize=13, fontName="Helvetica-Bold",
                                       textColor=_c(nc_color), alignment=1),
                    ),
                    Paragraph(
                        f"<i>« {_rl_escape(claim_text)} »</i>{source_line}",
                        ParagraphStyle(f"ct{i}", fontSize=9, fontName="Helvetica-BoldOblique",
                                       textColor=_c(_GA_TEXT), leading=13),
                    ),
                ],
                [
                    "",
                    Paragraph(f"<b>Problème :</b> {_rl_escape(problem)}", st["body"]),
                ],
                [
                    "",
                    Paragraph(f"Référence EmpCo : <b>{reg_basis}</b>", st["small"]),
                ],
            ],
            colWidths=["7%", "93%"],
        )
        block.setStyle(TableStyle([
            ("BACKGROUND",    (0, 0), (-1, -1), _c(nc_bg)),
            ("BOX",           (0, 0), (-1, -1), 0.5, _c(nc_color)),
            ("LINEBEFORE",    (0, 0), (0, -1),  3,   _c(nc_color)),
            ("SPAN",          (0, 0), (0, 2)),
            ("VALIGN",        (0, 0), (0, -1),  "MIDDLE"),
            ("VALIGN",        (1, 0), (1, -1),  "TOP"),
            ("TOPPADDING",    (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ("LEFTPADDING",   (0, 0), (0, -1),  6),
            ("LEFTPADDING",   (1, 0), (1, -1),  8),
            ("RIGHTPADDING",  (0, 0), (-1, -1), 8),
        ]))
        elems.append(block)
        if i < count - 1:
            elems.append(Spacer(1, 6))

    elems.append(PageBreak())
    return elems


# ── Page 3 — Actions prioritaires ───────────────────────────────────────────

def _page3(audit: Audit, st: dict, reformulations_map: Dict[str, str]) -> list:
    elems: list = []
    all_claims = audit.claims or []
    priority   = _select_priority_claims(all_claims, max_claims=6)

    ln_count  = sum(
        1 for c in all_claims
        if not getattr(c, "is_false_positive", False)
        and c.overall_verdict == "non_conforme"
        and getattr(c, "regime", None) == "liste_noire"
    )
    cpc_count = sum(
        1 for c in all_claims
        if not getattr(c, "is_false_positive", False)
        and c.overall_verdict in ("non_conforme", "risque")
        and getattr(c, "regime", None) == "cas_par_cas"
    )

    elems.append(Paragraph("Vos actions prioritaires", st["h1"]))
    elems.append(HRFlowable(width="100%", color=_c(_GA_GREEN2), thickness=1.5))
    elems.append(Spacer(1, 8))

    actions = []
    if ln_count > 0:
        s = "s" if ln_count > 1 else ""
        nt = "nt" if ln_count > 1 else ""
        actions.append((
            "1. Supprimer ou reformuler immédiatement",
            f"{ln_count} allégation{s} relève{nt} de la liste noire EmpCo (Annexe I). "
            f"Ces allégations sont interdites sans exception dès le {_EMPCO_DEADLINE}. "
            f"Elles doivent être supprimées ou remplacées par des formulations vérifiables avant cette date.",
            _GA_RED,
        ))
    if cpc_count > 0:
        s  = "s" if cpc_count > 1 else ""
        nt = "nt" if cpc_count > 1 else ""
        actions.append((
            f"{'2' if ln_count > 0 else '1'}. Documenter et prouver",
            f"{cpc_count} allégation{s} nécessite{nt} une justification solide (Art. 6 EmpCo). "
            f"Rassemblez les preuves, certifications ou données mesurables qui soutiennent chaque allégation "
            f"et archivez-les dans un dossier de conformité.",
            _GA_AMBER,
        ))
    num = len(actions) + 1
    actions.append((
        f"{num}. Mettre en place un processus de validation",
        f"Avant le {_EMPCO_DEADLINE}, établissez un circuit de validation interne pour toute "
        f"nouvelle communication environnementale (validation juridique ou expert ESG avant publication). "
        f"Ce processus réduit le risque de nouvelles non-conformités.",
        _GA_FOREST,
    ))

    for title, desc, color in actions[:3]:
        act = Table(
            [
                [Paragraph(f"<font color='{color}'><b>{title}</b></font>",
                           ParagraphStyle(f"at_{color}", fontSize=10, fontName="Helvetica-Bold",
                                          textColor=_c(color), leading=14))],
                [Paragraph(_rl_escape(desc), st["body"])],
            ],
            colWidths=["100%"],
        )
        act.setStyle(TableStyle([
            ("LINEBEFORE",    (0, 0), (0, -1), 3,  _c(color)),
            ("BOX",           (0, 0), (-1, -1), 0.5, _c(_GA_GREEN_BD)),
            ("TOPPADDING",    (0, 0), (-1, -1), 8),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
            ("LEFTPADDING",   (0, 0), (-1, -1), 10),
            ("RIGHTPADDING",  (0, 0), (-1, -1), 10),
        ]))
        elems.append(act)
        elems.append(Spacer(1, 6))

    elems.append(Spacer(1, 4))

    # Reformulation table — 3-4 allégations prioritaires
    # Priorité : Haiku secteur-spécifique > Option B générique non trompeuse
    # _reformulation_hint() est intentionnellement EXCLU : ses exemples sont hors secteur
    reformulations = []
    for claim in priority[:4]:
        hint = reformulations_map.get(str(claim.id)) or _FALLBACK_REFORMULATION
        reformulations.append((claim, hint))

    if reformulations:
        elems.append(Paragraph("Exemples de reformulation", st["h2"]))
        elems.append(Spacer(1, 4))

        hdr_style = ParagraphStyle("ref_h", fontSize=8, fontName="Helvetica-Bold",
                                   textColor=_c(_GA_WHITE))
        rows = [[Paragraph("<b>Allégation actuelle</b>", hdr_style),
                 Paragraph("<b>Reformulation recommandée</b>", hdr_style)]]
        for claim, hint in reformulations:
            ct = _word_truncate(claim.claim_text or "", 80)   # C3 : troncature propre
            clean_hint = _sanitize_text(hint)                 # C2 : CO₂ → CO2
            rows.append([
                Paragraph(f"<i>{_rl_escape(ct)}</i>", st["small"]),
                Paragraph(_rl_escape(clean_hint), st["small"]),
            ])
        ref_tbl = Table(rows, colWidths=["40%", "60%"])
        ref_tbl.setStyle(TableStyle([
            ("BACKGROUND",    (0, 0), (-1, 0),  _c(_GA_GREEN)),
            ("ROWBACKGROUNDS",(0, 1), (-1, -1), [_c(_GA_WHITE), _c(_GA_GREEN_LT)]),
            ("BOX",           (0, 0), (-1, -1), 0.5, _c(_GA_GREEN_BD)),
            ("INNERGRID",     (0, 0), (-1, -1), 0.3, _c(_GA_GREEN_BD)),
            ("TOPPADDING",    (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ("LEFTPADDING",   (0, 0), (-1, -1), 7),
            ("RIGHTPADDING",  (0, 0), (-1, -1), 7),
            ("VALIGN",        (0, 0), (-1, -1), "TOP"),
        ]))
        elems.append(ref_tbl)
        elems.append(Spacer(1, 5))

        # C1 : mention chiffres illustratifs
        elems.append(Paragraph(
            "<i>Les reformulations ci-dessus sont des exemples de formulation conforme à la "
            "directive. Les données chiffrées (pourcentages, volumes, normes) sont illustratives "
            "et doivent être remplacées par vos données réelles et vérifiables.</i>",
            ParagraphStyle("ref_disc", fontSize=7, fontName="Helvetica-Oblique",
                           textColor=_c(_GA_SLATE), leading=9),
        ))
        elems.append(Spacer(1, 8))

    # Deadline box
    dl = Table([[
        Paragraph(
            f"<b>Échéance réglementaire : {_EMPCO_DEADLINE}</b><br/>"
            f"<font size='8' color='{_GA_TEXT}'>La directive EmpCo (UE) 2024/825 entre en vigueur le "
            f"{_EMPCO_DEADLINE}. À compter de cette date, les allégations non conformes exposent votre "
            f"entreprise à des sanctions administratives et à des poursuites pour pratique commerciale "
            f"trompeuse.</font>",
            ParagraphStyle("dl", fontSize=9, fontName="Helvetica-Bold",
                           textColor=_c(_GA_RED), leading=14),
        )
    ]], colWidths=["100%"])
    dl.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, -1), _c(_GA_RED_LT)),
        ("BOX",           (0, 0), (-1, -1), 1, _c(_GA_RED)),
        ("TOPPADDING",    (0, 0), (-1, -1), 10),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
        ("LEFTPADDING",   (0, 0), (-1, -1), 12),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 12),
    ]))
    elems.append(dl)
    elems.append(PageBreak())
    return elems


# ── Page 4 — Exposition & Accompagnement ─────────────────────────────────────

def _page4(audit: Audit, st: dict) -> list:
    elems: list = []

    elems.append(Paragraph("Votre exposition réglementaire", st["h1"]))
    elems.append(HRFlowable(width="100%", color=_c(_GA_GREEN2), thickness=1.5))
    elems.append(Spacer(1, 10))

    # Sanctions
    sanc_body = Table(
        [
            [Paragraph("Pratique commerciale trompeuse (Art. L132-2 C. conso.)", st["body"]),
             Paragraph("Jusqu'à <b>300 000 €</b> + 2 ans (personne physique)<br/>"
                       "Jusqu'à <b>1,5 M€</b> (personne morale)",
                       ParagraphStyle("sv", fontSize=9, fontName="Helvetica", leading=13))],
            [Paragraph("Amende administrative DGCCRF", st["body"]),
             Paragraph("Jusqu'à <b>100 000 €</b> par infraction",
                       ParagraphStyle("sv", fontSize=9, fontName="Helvetica", leading=13))],
            [Paragraph("Injonction de cessation", st["body"]),
             Paragraph("Retrait immédiat de la communication obligatoire",
                       ParagraphStyle("sv", fontSize=9, fontName="Helvetica", leading=13))],
        ],
        colWidths=["55%", "45%"],
    )
    sanc_body.setStyle(TableStyle([
        ("INNERGRID",     (0, 0), (-1, -1), 0.3, _c(_GA_GREEN_BD)),
        ("BOX",           (0, 0), (-1, -1), 0.3, _c(_GA_GREEN_BD)),
        ("ROWBACKGROUNDS",(0, 0), (-1, -1), [_c(_GA_WHITE), _c(_GA_RED_LT)]),
        ("TOPPADDING",    (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING",   (0, 0), (-1, -1), 8),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 8),
        ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
    ]))
    sanc_wrapper = Table(
        [
            [Paragraph("<b>Sanctions encourues (DGCCRF &amp; Code de la consommation)</b>",
                       ParagraphStyle("sth", fontSize=9, fontName="Helvetica-Bold",
                                      textColor=_c(_GA_RED)))],
            [sanc_body],
        ],
        colWidths=["100%"],
    )
    sanc_wrapper.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, 0),  _c(_GA_RED_LT)),
        ("BOX",           (0, 0), (-1, -1), 0.5, _c(_GA_RED)),
        ("LINEBEFORE",    (0, 0), (0, -1),  3,   _c(_GA_RED)),
        ("TOPPADDING",    (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ("LEFTPADDING",   (0, 0), (-1, -1), 12),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 12),
    ]))
    elems.append(sanc_wrapper)
    elems.append(Spacer(1, 12))

    # Disclaimer
    disc = Table([[
        Paragraph(
            "Ce diagnostic est un outil d'aide à la conformité et ne constitue pas un conseil juridique. "
            "Pour toute situation complexe, consultez un avocat spécialisé en droit de la consommation "
            "ou en droit européen de l'environnement.",
            st["small"],
        )
    ]], colWidths=["100%"])
    disc.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, -1), _c("#F8FAFC")),
        ("BOX",           (0, 0), (-1, -1), 0.5, _c(_GA_GREEN_BD)),
        ("TOPPADDING",    (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ("LEFTPADDING",   (0, 0), (-1, -1), 10),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 10),
    ]))
    elems.append(disc)
    elems.append(Spacer(1, 14))

    # Pour aller plus loin
    elems.append(Paragraph("Pour aller plus loin", st["h2"]))
    elems.append(Spacer(1, 4))
    accomp = Table([[
        Paragraph(
            "GreenAudit propose des solutions de suivi pour pérenniser votre conformité EmpCo :<br/><br/>"
            "• <b>Réaudit de conformité</b> — Vérification après corrections pour valider vos reformulations.<br/>"
            "• <b>Monitoring continu</b> — Surveillance automatique de vos publications et détection "
            "des nouvelles allégations à risque.<br/>"
            "• <b>Dossier de conformité</b> — Constitution du dossier de preuves opposable pour la DGCCRF.",
            st["body"],
        )
    ]], colWidths=["100%"])
    accomp.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, -1), _c(_GA_GREEN_LT)),
        ("BOX",           (0, 0), (-1, -1), 1,  _c(_GA_GREEN2)),
        ("LINEBEFORE",    (0, 0), (0, -1),  3,  _c(_GA_GREEN)),
        ("TOPPADDING",    (0, 0), (-1, -1), 10),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
        ("LEFTPADDING",   (0, 0), (-1, -1), 12),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 12),
    ]))
    elems.append(accomp)
    elems.append(Spacer(1, 16))

    # Contact
    contact = Table([[
        Paragraph(
            f"<font color='{_GA_WHITE}'><b>GreenAudit</b> — Anthony Edmond</font><br/>"
            f"<font color='{_GA_WHITE}'>06 79 78 02 39  ·  contact@green-audit.fr</font>",
            ParagraphStyle("ctt", fontSize=9, fontName="Helvetica",
                           textColor=_c(_GA_WHITE), leading=14),
        )
    ]], colWidths=["100%"])
    contact.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, -1), _c(_GA_GREEN)),
        ("TOPPADDING",    (0, 0), (-1, -1), 10),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
        ("LEFTPADDING",   (0, 0), (-1, -1), 12),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 12),
    ]))
    elems.append(contact)
    return elems


# ── Reformulations Haiku (batch) ─────────────────────────────────────────────

# Texte de repli Option B — non trompeur, ne mentionne jamais d'exemple hors secteur
_FALLBACK_REFORMULATION = (
    "Reformuler avec une donnée précise, mesurable et vérifiable, propre à votre activité "
    "(ex. un pourcentage chiffré, une certification tierce reconnue, "
    "une réduction mesurée et datée par un organisme indépendant)."
)


def _generate_reformulations_batch(claims: list, sector: str) -> Dict[str, str]:
    """
    1 seul appel Haiku pour toutes les allégations prioritaires.
    Returns: {str(claim.id): "reformulation adaptée au secteur"}
    Dict vide si API indisponible — le code appelant tombe sur _FALLBACK_REFORMULATION.
    """
    if not claims:
        return {}
    try:
        import anthropic
        from app.config import settings as _settings

        api_key = getattr(_settings, "ANTHROPIC_API_KEY", None)
        if not api_key:
            logger.warning("ANTHROPIC_API_KEY absent — reformulations Haiku désactivées")
            return {}

        items = [
            {
                "idx": i + 1,
                "id": str(claim.id),
                "text": (claim.claim_text or "")[:200],
                "basis": REGULATORY_BASIS_LABELS.get(
                    getattr(claim, "regulatory_basis", "") or "", "—"
                ),
            }
            for i, claim in enumerate(claims)
        ]

        allegations_block = "\n".join(
            f'{it["idx"]}. "{it["text"]}" — problème : {it["basis"]}'
            for it in items
        )

        prompt = (
            "Tu es un expert en conformité de la directive EmpCo (UE 2024/825).\n"
            "Pour chaque allégation environnementale ci-dessous, propose une "
            "reformulation CONFORME à la directive.\n\n"
            f"Secteur de l'entreprise : {sector}\n\n"
            "Contraintes pour chaque reformulation :\n"
            f"- Elle doit être réaliste et plausible pour une entreprise du secteur \"{sector}\" "
            f"— n'utilise JAMAIS d'exemple hors secteur "
            f"(ex. ne parle pas d'emballage ou de packaging pour une raffinerie ou une entreprise d'énergie).\n"
            "- Elle doit être précise, mesurable, vérifiable.\n"
            "- Elle doit corriger le problème EmpCo identifié.\n"
            "- Maximum 2 phrases par reformulation.\n"
            "- Si l'allégation relève d'une interdiction absolue (annexe I), "
            "la reformulation doit expliquer brièvement qu'il faut soit supprimer, "
            "soit remplacer par une donnée factuelle précise — "
            "avec un exemple concret adapté au secteur.\n\n"
            "Allégations à reformuler :\n"
            f"{allegations_block}\n\n"
            'Réponds UNIQUEMENT en JSON, format :\n'
            '{"reformulations": [{"index": 1, "reformulation": "..."}, ...]}\n'
            "Pas de texte avant ou après le JSON."
        )

        logger.info("Appel Haiku batch — %d allégation(s), secteur : %s", len(items), sector)
        client = anthropic.Anthropic(api_key=api_key)
        resp = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=1000,
            messages=[{"role": "user", "content": prompt}],
        )

        raw = resp.content[0].text.strip()
        # Strip markdown fences if model wraps the JSON
        if "```" in raw:
            raw = raw.split("```")[1].lstrip("json").strip()

        data = json.loads(raw)
        ref_list = data.get("reformulations", [])

        result: Dict[str, str] = {}
        for entry in ref_list:
            idx = int(entry.get("index", 0))
            text = str(entry.get("reformulation", "")).strip()
            if 1 <= idx <= len(items) and text:
                result[items[idx - 1]["id"]] = text

        logger.info("Haiku : %d reformulation(s) générées", len(result))
        return result

    except Exception as exc:
        logger.warning("Haiku reformulations indisponibles : %s", exc)
        return {}


# ── Entry point ──────────────────────────────────────────────────────────────

def generate_marque_pdf(audit: Audit) -> Tuple[str, str]:
    """
    Génère le rapport commercial 4 pages pour la marque auditée.
    Returns: (filename, sha256_hash)
    """
    storage = Path(settings.PDF_STORAGE_PATH)
    storage.mkdir(parents=True, exist_ok=True)

    nonce    = secrets.token_hex(8)
    filename = f"greenaudit_marque_{audit.id}_{nonce}.pdf"
    filepath = str(storage / filename)

    st = _styles()

    left   = 20 * mm
    right  = 20 * mm
    top    = 20 * mm
    bottom = 22 * mm

    doc = BaseDocTemplate(
        filepath,
        pagesize=A4,
        leftMargin=left,
        rightMargin=right,
        topMargin=top,
        bottomMargin=bottom,
    )
    frame = Frame(
        x1=left, y1=bottom,
        width=A4[0] - left - right,
        height=A4[1] - top - bottom,
        leftPadding=0, bottomPadding=0, rightPadding=0, topPadding=0,
        id="main",
    )
    doc.addPageTemplates([PageTemplate(id="all", frames=[frame], onPage=_footer)])

    # Pré-générer les reformulations (1 appel Haiku pour toutes les allégations prioritaires)
    priority_claims = _select_priority_claims(audit.claims or [], max_claims=6)
    sector = getattr(audit, "sector", "") or "non précisé"
    reformulations_map = _generate_reformulations_batch(priority_claims[:4], sector)

    elements: list = []
    elements += _page1(audit, st)
    elements += _page2(audit, st)
    elements += _page3(audit, st, reformulations_map)
    elements += _page4(audit, st)

    doc.build(elements)

    sha256 = hashlib.sha256(Path(filepath).read_bytes()).hexdigest()
    return filename, sha256
