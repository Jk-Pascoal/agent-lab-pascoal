"""Execute a synthetic CSV structural PoC and write an auditable report.

Usage: python -m agent_lab.poc_audit_cli INPUT.csv OUTPUT.json --catalog-id DEMO
"""
import argparse

from .catalog_csv_adapter import load_catalog_materials
from .catalog_quality_use_case import DiagnoseCatalogQualityUseCase
from .poc_audit_report import write_poc_audit_report


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input_csv")
    parser.add_argument("output_json")
    parser.add_argument("--catalog-id", required=True)
    args = parser.parse_args(argv)
    # Deliberately do not claim source-byte or physical-row custody:
    # current CSV adapter does not return an atomic captured snapshot.
    catalog = load_catalog_materials(args.input_csv)
    report = DiagnoseCatalogQualityUseCase().execute(catalog, catalog_id=args.catalog_id)
    write_poc_audit_report(report, args.output_json)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
