"""Adaptador de infraestrutura para ingestão de catálogos CSV operacionais."""

from pathlib import Path

from .domain import MaterialRecord


def load_catalog_materials(
    path: str | Path,
) -> tuple[MaterialRecord, ...]:
    """Carrega um arquivo CSV operacional de catálogo."""
    raise NotImplementedError
