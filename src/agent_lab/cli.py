"""Interface de linha de comando para executar o baseline."""

import argparse
from pathlib import Path

from .baseline import evaluate_baseline
from .data_io import load_labeled_materials


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Executa o baseline determinístico de governança PDM."
    )
    parser.add_argument(
        "csv_path",
        type=Path,
        help="Caminho para o CSV de materiais rotulados.",
    )
    return parser


def main() -> None:
    args = build_parser().parse_args()
    materials = load_labeled_materials(args.csv_path)
    assessments, report = evaluate_baseline(materials)

    print("material_id | decisão | completude | confiança | alertas")
    print("-" * 78)
    for assessment in assessments:
        labels = ",".join(issue.issue_type.value for issue in assessment.issues)
        print(
            f"{assessment.material_id:11} | "
            f"{assessment.decision.value:7} | "
            f"{assessment.completeness:10.2f} | "
            f"{assessment.confidence:9.2f} | "
            f"{labels or 'VALID'}"
        )

    print("\nMétricas do baseline")
    print(f"- Registros: {report.total}")
    print(f"- Acertos: {report.correct}")
    print(f"- Correspondência exata: {report.exact_match_accuracy:.1%}")
    print(f"- Cobertura do rótulo esperado: {report.label_hit_rate:.1%}")
    print(f"- Precisão de duplicidade: {report.duplicate_precision:.1%}")
    print(f"- Recall de duplicidade: {report.duplicate_recall:.1%}")
    print(f"- Decisões: {report.decisions}")

    if report.errors:
        print("- Erros:")
        for error in report.errors:
            print(f"  - {error}")


if __name__ == "__main__":
    main()
