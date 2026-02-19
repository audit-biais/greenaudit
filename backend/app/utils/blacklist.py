"""Liste des termes génériques interdits par la directive EmpCo (EU 2024/825)."""

from __future__ import annotations

BLACKLIST_TERMS: list = [
    "écologique",
    "éco-responsable",
    "éco responsable",
    "eco-friendly",
    "vert",
    "green",
    "respectueux de l'environnement",
    "respectueux de la planète",
    "ami de la nature",
    "nature friendly",
    "durable",
    "sustainable",
    "biodégradable",
    "naturel",
    "natural",
    "climate friendly",
    "bon pour la planète",
    "zéro déchet",
    "zero waste",
    "propre",
    "clean",
]

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

# Mots-clés indiquant un aspect partiel (pour la règle de proportionnalité)
PARTIAL_SCOPE_PATTERNS: list = [
    r"\bemballage[s]?\b",
    r"\bpackaging\b",
    r"\btransport\b",
    r"\blogistique\b",
    r"\bproduit\b",
    r"\bfabrication\b",
    r"\bproduction\b",
    r"\bmatière[s]? première[s]?\b",
    r"\bénergie\b",
    r"\bdéchet[s]?\b",
    r"\beau\b",
    r"\bcarbone\b",
    r"\bco2\b",
    r"\bémission[s]?\b",
]
