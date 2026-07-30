"""Normalização lexical simples para o baseline determinístico."""

import re
import unicodedata


ABBREVIATIONS = {
    "AC": "ACO",
    "ESF": "ESFERA",
    "PARAF": "PARAFUSO",
    "POL": "POLEGADA",
    "ROLAM": "ROLAMENTO",
    "SCH": "SCHEDULE",
    "SEXT": "SEXTAVADO",
    "VALV": "VALVULA",
}

IGNORED_WORDS = {
    "A",
    "DE",
    "DO",
    "DA",
    "EM",
    "PARA",
    "COM",
    "SEM",
    "ROSCA",
    "METRICA",
    "COMPRIMENTO",
    "DIAMETRO",
    "CLASSE",
    "CABECA",
}


def normalize_text(value: str) -> str:
    """Remove acentos, padroniza caixa e reduz pontuação a espaços."""

    decomposed = unicodedata.normalize("NFKD", value)
    without_accents = "".join(
        character for character in decomposed if not unicodedata.combining(character)
    )
    upper = without_accents.upper()
    return " ".join(re.sub(r"[^A-Z0-9]+", " ", upper).split())


def word_tokens(value: str) -> set[str]:
    """Extrai tokens lexicais e expande abreviações conhecidas."""

    normalized = normalize_text(value)
    tokens: set[str] = set()
    for token in normalized.split():
        canonical = ABBREVIATIONS.get(token, token)
        if canonical.startswith("SEXTAVAD"):
            canonical = "SEXTAVADO"
        if canonical.startswith("POLEGAD"):
            canonical = "POLEGADA"
        if canonical not in IGNORED_WORDS and not canonical.isdigit():
            tokens.add(canonical)
    return tokens


def numeric_tokens(value: str) -> set[str]:
    """Extrai números técnicos, inclusive quando unidos a letras."""

    return set(re.findall(r"\d+(?:[.,]\d+)?", normalize_text(value)))


def category_token(value: str) -> str:
    """Retorna o primeiro substantivo técnico normalizado."""

    normalized = normalize_text(value)
    for token in normalized.split():
        canonical = ABBREVIATIONS.get(token, token)
        if canonical.startswith("SEXTAVAD"):
            canonical = "SEXTAVADO"
        if canonical not in IGNORED_WORDS and not canonical.isdigit():
            return canonical
    return ""
