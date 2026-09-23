"""Application use case para diagnóstico de qualidade de catálogo."""

from collections.abc import Sequence
from typing import Protocol

from .catalog_quality import (
    CatalogQualityReport,
    diagnose_catalog_quality,
)
from .domain import MaterialRecord


class CatalogDiagnosticPipeline(Protocol):
    """Protocolo estrutural para pipelines de diagnóstico de catálogo."""

    def __call__(
        self,
        catalog: Sequence[MaterialRecord],
        *,
        catalog_id: str,
    ) -> CatalogQualityReport:
        ...


class DiagnoseCatalogQualityUseCase:
    """Coordena a execução do diagnóstico de qualidade de catálogo."""

    def __init__(
        self,
        pipeline: CatalogDiagnosticPipeline | None = None,
    ) -> None:
        self._pipeline = (
            pipeline
            if pipeline is not None
            else diagnose_catalog_quality
        )

    def execute(
        self,
        catalog: Sequence[MaterialRecord],
        *,
        catalog_id: str,
    ) -> CatalogQualityReport:
        if not isinstance(catalog, Sequence) or isinstance(
            catalog,
            (str, bytes, bytearray),
        ):
            raise TypeError(
                "catalog must be a Sequence of MaterialRecord, excluding str and bytes"
            )

        for record in catalog:
            if not isinstance(record, MaterialRecord):
                raise TypeError(
                    "all items in catalog must be MaterialRecord instances"
                )

        if not isinstance(catalog_id, str) or isinstance(catalog_id, bool):
            raise TypeError("catalog_id must be a str")

        canonical_catalog_id = catalog_id.strip()
        if not canonical_catalog_id:
            raise ValueError("catalog_id must not be empty or whitespace")

        result = self._pipeline(
            catalog,
            catalog_id=canonical_catalog_id,
        )

        if not isinstance(result, CatalogQualityReport):
            raise TypeError(
                "pipeline must return a CatalogQualityReport"
            )

        if result.catalog_id != canonical_catalog_id:
            raise ValueError(
                "pipeline result catalog_id does not match requested catalog_id"
            )

        expected_material_ids = tuple(
            sorted(record.material_id for record in catalog)
        )
        actual_material_ids = tuple(
            assessment.material_id
            for assessment in result.assessments
        )

        if actual_material_ids != expected_material_ids:
            raise ValueError(
                "pipeline result assessment identities do not match input catalog"
            )

        return result
