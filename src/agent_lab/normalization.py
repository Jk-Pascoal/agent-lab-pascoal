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


# Conserva a sequência física de dois valores ligados por X (diâmetro × comprimento).
# Não atribui papéis dimensionais quando a descrição não permite inferi-los.
_DIMENSION_PAIR = re.compile(
    r"(?<![0-9])(?P<first>\d+(?:/\d+|[.,]\d+)?)"
    r"\s*[X×]\s*"
    r"(?P<second>\d+(?:/\d+|[.,]\d+)?)"
    r"(?:\s*(?P<unit>POLEGADAS?|POL|IN|MM))?"
    r"(?![A-Z0-9])"
)


def ordered_dimension_pair(value: str) -> tuple[str, str, str] | None:
    """Lê um par dimensional explícito sem perder frações, ordem ou unidade.

    Retorna None quando não há exatamente um par reconhecível. A assinatura
    é apenas evidência lexical; NÃO decide equivalência nem duplicidade.
    """

    upper = unicodedata.normalize("NFKD", value)
    upper = "".join(c for c in upper if not unicodedata.combining(c)).upper()
    matches = list(_DIMENSION_PAIR.finditer(upper))
    if len(matches) != 1:
        return None
    match = matches[0]
    # Rejeita cadeias de 3+ dimensões em vez de ler só o primeiro par.
    if re.search(r"\bX\s*\d", upper[match.end():]):
        return None
    unit = match.group("unit") or ""
    canonical_unit = "IN" if unit in {"POL", "POLEGADA", "POLEGADAS", "IN"} else unit
    first = match.group("first").replace(",", ".")
    second = match.group("second").replace(",", ".")
    return first, second, canonical_unit
