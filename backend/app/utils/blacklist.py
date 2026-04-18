"""
Liste des termes et patterns interdits par la directive EmpCo (EU 2024/825).

Références :
- Annexe I, point 4bis : allégations environnementales génériques
- Annexe I, point 4quater : neutralité carbone par compensation
- Annexe I, point 10bis : exigences légales présentées comme distinctives
"""

from __future__ import annotations

import unicodedata

def _normalize(text: str) -> str:
    """Supprime les accents et passe en minuscules pour comparaison insensible."""
    nfkd = unicodedata.normalize("NFKD", text.lower())
    return "".join(c for c in nfkd if not unicodedata.combining(c))

BLACKLIST_TERMS: list = [
    # --- Annexe I, point 4bis + considérant 9 de la directive EmpCo ---
    "écologique",
    "écoresponsable",
    "éco-responsable",
    "éco responsable",
    "eco-responsable",
    "eco responsable",
    "ecoresponsable",
    "éco-friendly",
    "eco-friendly",
    "vert",
    "green",
    "respectueux de l'environnement",
    "respectueux de la planète",
    "respectueux de la nature",
    "ami de la nature",
    "ami de l'environnement",
    "nature friendly",
    "planet friendly",
    "earth friendly",
    "durable",
    "sustainable",
    "biodégradable",
    "biosourcé",
    "naturel",
    "natural",
    "climate friendly",
    "bon pour la planète",
    "bon pour l'environnement",
    "bon pour le climat",
    "favorable à l'environnement",
    "zéro déchet",
    "zero waste",
    "propre",
    "clean",
    "à faible intensité de carbone",
    "bas carbone",
    "low carbon",
    "économe en énergie",
    # --- Variantes typographiques éco- (Bug 5)
    "éco-conçu",
    "ecoconçu",
    "eco-conçu",
    "écoconçu",
    "éco-design",
    "ecodesign",
    "eco-design",
    "écodesign",
    "écofriendly",
    "ecofriendly",
    "zéro-déchet",
    "zero-déchet",
    "zéro-dechet",
    "zero-dechet",
    "zero déchet",
    "zéro-émission",
    "zero-émission",
    "zéro-emission",
    "zero-emission",
    # --- Couverture élargie ---
    "ecolo",
    "éthique",
    "ethical",
    "responsable",
    "responsible",
    "non toxique",
    "non-toxique",
    "non toxic",
    "sans produit chimique",
    "chemical free",
    "conscious",
    "conscient",
    "vertueux",
    "virtuous",
]

# Version normalisée (sans accents) pour comparaison insensible
BLACKLIST_TERMS_NORMALIZED: list = [(_normalize(t), t) for t in BLACKLIST_TERMS]

CARBON_NEUTRAL_TERMS: list = [
    "neutre en carbone",
    "carbon neutral",
    "neutralité carbone",
    "climate neutral",
    "zéro émission",
    "zero emission",
    "impact neutre",
    "compensé carbone",
    "compensation carbone",
    "net zero",
    "net zéro",
    # Termes ajoutés
    "carbon positive",
    "climate positive",
    "carbone positif",
    "empreinte carbone nulle",
    "zéro carbone",
    "zero carbone",
    # Variantes compensation CO2 (Bug 2 — Raffinerie du Midi)
    "compensé en co2",
    "compensé co2",
    "compensation co2",
    "compensation en co2",
    "compensé carbone",
    "compensation carbone",
    "carbone compensé",
    "co2 compensé",
    "émissions compensées",
    "émissions sont compensées",
    "émissions seront compensées",
    "émissions ont été compensées",
    "compenser nos émissions",
    "compenser les émissions",
]

# Patterns détectant des exigences légales présentées comme avantage distinctif
# (Annexe I, point 10bis de la directive 2005/29/CE modifiée par EmpCo)
LEGAL_REQUIREMENT_PATTERNS: list = [
    # Substances interdites par la réglementation EU
    r"\bsans\s+bpa\b",
    r"\bbpa[\s-]*free\b",
    r"\bsans\s+phtalates?\b",
    r"\bsans\s+parab[eè]n[es]?\b",
    r"\bparaben[\s-]*free\b",
    r"\bsans\s+plomb\b",
    r"\blead[\s-]*free\b",
    r"\bsans\s+mercure\b",
    r"\bsans\s+cadmium\b",
    r"\bsans\s+amiante\b",
    r"\bsans\s+cfc\b",
    # Conformité réglementaire présentée comme avantage
    r"\bconforme\s+(à\s+)?(reach|rohs|ce|weee)\b",
    r"\bcertifi[ée]\s+(reach|rohs|ce)\b",
    r"\brespecte\s+(la|les)\s+(réglementation|norme|loi)",
    r"\bconforme\s+à\s+la\s+réglementation\b",
    r"\bconformément\s+à\s+la\s+loi\b",
    r"\brespecte\s+les\s+normes\s+en\s+vigueur\b",
    # Obligations présentées comme engagement volontaire
    r"\bnos\s+produits\s+respectent\s+la\s+loi\b",
    r"\bgaranti\s+sans\s+substance[s]?\s+interdit",
]

# Mots-clés indiquant une qualification mesurable (atténue la blacklist)
QUALIFICATION_PATTERNS: list = [
    r"\d+\s*%",           # pourcentage (ex: "30%")
    r"\d+\s*g\b",         # grammes
    r"\d+\s*kg\b",        # kilogrammes
    r"\d+\s*t\b",         # tonnes
    r"\d+\s*kwh\b",       # kWh
    r"certifi[ée]",       # certification mentionnée
    r"label[lisé]*",      # label mentionné
    r"norme\s+\w+",       # norme ISO, NF, etc.
    r"iso\s*\d+",         # ISO 14001, etc.
    r"selon\s+(le|la|les|une|un)", # "selon le rapport..."
    r"mesur[ée]",         # mesuré / mesurée
    r"vérifi[ée]",        # vérifié / vérifiée
    r"audit[ée]",         # audité / auditée
]

# Mots-clés indiquant un aspect partiel de l'entreprise (pour la règle de proportionnalité scope=entreprise)
PARTIAL_SCOPE_PATTERNS: list = [
    r"\bemballage[s]?\b",
    r"\bpackaging\b",
    r"\btransport[s]?\b",
    r"\blogistique[s]?\b",
    r"\boutil[s]?\s+logistique[s]?\b",
    r"\bproduit[s]?\b",
    r"\bfabrication\b",
    r"\bproduction\b",
    r"\bmatière[s]?\s+première[s]?\b",
    r"\bénergie\b",
    r"\bdéchet[s]?\b",
    r"\beau\b",
    r"\bcarbone\b",
    r"\bco2\b",
    r"\bémission[s]?\b",
    # Ajouts Bug 6
    r"\bsupply\s+chain\b",
    r"\bchaîne\s+d['']approvisionnement\b",
    r"\bentrepôt[s]?\b",
    r"\bflotte\b",
    r"\bvéhicule[s]?\b",
    r"\busine[s]?\b",
    r"\bsite[s]?\b",
    r"\binformatique\b",
    r"\bnumérique\b",
    r"\bdigital\b",
    r"\brestauration\b",
    r"\bcantine[s]?\b",
]

# Composants mineurs d'un produit (pour la règle de proportionnalité scope=produit)
# Si la claim porte sur le produit entier mais ne cite qu'un composant mineur → non conforme
MINOR_COMPONENT_PATTERNS: list = [
    r"\bbouchon[s]?\b",
    r"\bcouvercle[s]?\b",
    r"\bétiquette[s]?\b",
    r"\blabel[s]?\b",
    r"\blogo[s]?\b",
    r"\bfilm[s]?\s+(plastique|d'emballage)?\b",
    r"\bsachet[s]?\b",
    r"\bsuremballage[s]?\b",
    r"\bpalette[s]?\b",
    r"\brunner[s]?\b",
    r"\bpoignée[s]?\b",
    r"\bvis\b",
    r"\bboulons?\b",
    r"\bsangle[s]?\b",
    r"\bfil[s]?\s+d'emballage\b",
    r"\bcalage[s]?\b",
    r"\bprotège[\s-]?coin[s]?\b",
]

# Termes absolument interdits en France par la loi AGEC (Art. 13) + EmpCo
# Interdits même avec preuve, même avec qualification — AUCUNE exception
AGEC_ABSOLUTE_FORBIDDEN: list = [
    "biodégradable",
    "biodegradable",
    "respectueux de l'environnement",
    "respectueux de la nature",
    "respectueux de la planète",
]
AGEC_ABSOLUTE_FORBIDDEN_NORMALIZED: list = [(_normalize(t), t) for t in AGEC_ABSOLUTE_FORBIDDEN]

# Types de documents reconnus comme Écolabel officiel (Annexe I, point 4bis + Art. 2(s))
# Ces types débloquent le verdict "conforme" pour une allégation générique
OFFICIAL_ECOLABEL_DOCUMENT_TYPE = "ecolabel"
