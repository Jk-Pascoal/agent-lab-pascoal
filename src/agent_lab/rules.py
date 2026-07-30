"""Regras explícitas de governança usadas antes de qualquer LLM."""

import re

from .domain import (
    GovernanceIssue,
    IssueSeverity,
    IssueType,
    MaterialRecord,
)
from .normalization import normalize_text


ALLOWED_STATUSES = {"ACTIVE", "INACTIVE", "UNDER_REVIEW"}
ALLOWED_UNITS = {"PC", "UN", "M", "KG", "L"}
LIQUID_KEYWORDS = {"OLEO", "LUBRIFICANTE", "FLUIDO"}
GENERIC_KEYWORDS = {"DIVERSO", "GERAL", "INDUSTRIAL", "OUTROS"}


def validate_required_fields(record: MaterialRecord) -> list[GovernanceIssue]:
    issues: list[GovernanceIssue] = []
    required = {
        "material_id": record.material_id,
        "description_short": record.description_short,
        "unit": record.unit,
        "status": record.status,
    }
    for field_name, value in required.items():
        if not value.strip():
            issues.append(
                GovernanceIssue(
                    issue_type=IssueType.MISSING_CRITICAL_FIELD,
                    field_name=field_name,
                    message=f"Campo obrigatório ausente: {field_name}",
                    severity=IssueSeverity.BLOCKING,
                )
            )
    return issues


def validate_unit(record: MaterialRecord) -> list[GovernanceIssue]:
    unit = normalize_text(record.unit)
    description = normalize_text(
        f"{record.description_short} {record.long_description}"
    )

    if unit and unit not in ALLOWED_UNITS:
        return [
            GovernanceIssue(
                issue_type=IssueType.INVALID_UNIT,
                field_name="unit",
                message=f"Unidade não reconhecida: {record.unit}",
                severity=IssueSeverity.BLOCKING,
            )
        ]

    if unit in {"PC", "UN"} and any(
        keyword in description.split() for keyword in LIQUID_KEYWORDS
    ):
        return [
            GovernanceIssue(
                issue_type=IssueType.SUSPICIOUS_UNIT,
                field_name="unit",
                message="Material líquido cadastrado em unidade de peça",
            )
        ]
    return []


def validate_status(record: MaterialRecord) -> list[GovernanceIssue]:
    status = record.status.strip().upper()
    if status and status not in ALLOWED_STATUSES:
        return [
            GovernanceIssue(
                issue_type=IssueType.INVALID_STATUS,
                field_name="status",
                message=f"Status não reconhecido: {record.status}",
                severity=IssueSeverity.BLOCKING,
            )
        ]
    return []


def validate_ambiguity(record: MaterialRecord) -> list[GovernanceIssue]:
    short = normalize_text(record.description_short)
    if (
        not record.long_description.strip()
        and not record.manufacturer_part_number.strip()
        and any(keyword in short.split() for keyword in GENERIC_KEYWORDS)
    ):
        return [
            GovernanceIssue(
                issue_type=IssueType.AMBIGUOUS_DESCRIPTION,
                field_name="description_short",
                message="Descrição usa termo genérico sem especificação adicional",
            )
        ]
    return []


def validate_technical_attributes(record: MaterialRecord) -> list[GovernanceIssue]:
    """Aplica requisitos mínimos por família técnica."""

    description = normalize_text(
        f"{record.description_short} {record.long_description}"
    )
    missing_reason = ""

    if "CABO" in description.split() and not re.search(r"\b\d+\s*(?:V|KV)\b", description):
        missing_reason = "tensão nominal"
    elif "MOTOR" in description.split() and not (
        re.search(r"\b\d+\s*(?:V|KV)\b", description)
        and re.search(r"\b(?:50|60)\s*HZ\b", description)
    ):
        missing_reason = "tensão e frequência"
    elif "FILTRO" in description.split() and not (
        record.manufacturer_part_number.strip()
        or any(term in description.split() for term in {"MICRA", "MICRON", "ELEMENTO"})
    ):
        missing_reason = "elemento, micragem ou código do fabricante"
    elif "MANOMETRO" in description.split() and not any(
        term in description.split() for term in {"CONEXAO", "ROSCA"}
    ):
        missing_reason = "conexão ao processo"

    if not missing_reason:
        return []

    return [
        GovernanceIssue(
            issue_type=IssueType.MISSING_TECHNICAL_ATTRIBUTE,
            field_name="long_description",
            message=f"Atributo técnico ausente: {missing_reason}",
        )
    ]


def run_rules(record: MaterialRecord) -> list[GovernanceIssue]:
    """Executa todas as regras locais na ordem de governança."""

    issues: list[GovernanceIssue] = []
    for rule in (
        validate_required_fields,
        validate_unit,
        validate_status,
        validate_ambiguity,
        validate_technical_attributes,
    ):
        issues.extend(rule(record))
    return issues
