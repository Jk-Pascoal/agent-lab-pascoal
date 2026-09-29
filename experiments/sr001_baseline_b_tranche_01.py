"""Harness experimental para avaliação metrológica da Tranche 01 (SR-001 Baseline B).

Avalia a Tranche 01 congelada frente a:
1. Candidate Blocking (preservação do espaço de candidatos);
2. Detector determinístico is_possible_duplicate.

Preserva estritamente:
Ground Truth != Candidate Blocking != Detector Prediction != Evaluator / Metrics.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from agent_lab.catalog_csv_adapter import load_catalog_materials
from agent_lab.domain import MaterialRecord
from agent_lab.duplicates import is_possible_duplicate
from agent_lab.ground_truth_serialization import duplicate_pair_ground_truth_from_record
from agent_lab.normalization import category_token, normalize_text

EXPECTED_CATALOG_SHA256 = "ba82fce8903888255f8f9be0f97c7c2838b1f3d9733ef1a891aedbc6cf1be003"
EXPECTED_GROUND_TRUTH_SHA256 = "8eb6758ddcf68f3e4cf48ead8ad4a24c8adcf526983c72db1460a21ebe5249ef"
EXPECTED_MANIFEST_SHA256 = "686e98328a47673f492301894faf0d265d48c782c53c51fc6f69fe1f5dc9468a"


def _canonical_lf_sha256(path: Path) -> str:
    """Calcula SHA-256 normalizado para bytes Unix LF (independente de checkout CRLF no Windows)."""
    raw_bytes = path.read_bytes().replace(b"\r\n", b"\n")
    return hashlib.sha256(raw_bytes).hexdigest()


def extract_candidate_family_keys(
    record: MaterialRecord,
) -> tuple[tuple[str, str] | None, tuple[str, str] | None]:
    """Extrai as chaves das duas famílias de candidatos conforme protocolo do Baseline A / SPEC-0158.

    Família 1 (Rota 1): (part_number normalizado, fabricante normalizado) se ambos não-vazios.
    Família 2 (Rota 2): (grupo normalizado, category_token) se category_token não-vazio.
    """
    norm_pn = normalize_text(record.manufacturer_part_number)
    norm_mfg = normalize_text(record.manufacturer)
    p1_key = (norm_pn, norm_mfg) if (norm_pn and norm_mfg) else None

    full_desc = f"{record.description_short} {record.long_description}".strip()
    cat_tok = category_token(full_desc)
    norm_grp = normalize_text(record.material_group)
    p2_key = (norm_grp, cat_tok) if cat_tok else None

    return p1_key, p2_key


def is_candidate_pair(
    record_a: MaterialRecord,
    record_b: MaterialRecord,
) -> bool:
    """Predicado puro de Candidate Blocking.

    Retorna True se o par (A, B) pertence à união deduplicada das Famílias 1 e 2.
    """
    p1_a, p2_a = extract_candidate_family_keys(record_a)
    p1_b, p2_b = extract_candidate_family_keys(record_b)

    fam1_match = (p1_a is not None) and (p1_a == p1_b)
    fam2_match = (p2_a is not None) and (p2_a == p2_b)

    return fam1_match or fam2_match


@dataclass(frozen=True, slots=True)
class Tranche01CaseObservation:
    evaluation_case_id: str
    stratum: str
    challenge_class: str
    material_id_a: str
    material_id_b: str
    ground_truth_is_duplicate: bool
    is_candidate: bool
    is_possible_duplicate: bool
    detector_classification: str  # TP, FP, TN, FN
    blocking_classification: str  # CANDIDATE_TP, CANDIDATE_FN, CANDIDATE_FP, CANDIDATE_TN


def evaluate_tranche_01(
    base_dir: Path,
) -> tuple[list[Tranche01CaseObservation], dict[str, Any]]:
    catalog_path = base_dir / "draft_tranche_01_catalog.csv"
    gt_path = base_dir / "draft_tranche_01_ground_truth.json"
    manifest_path = base_dir / "draft_tranche_01_manifest.json"

    # 1. Validação estrita de existência e hashes canônicos
    assert catalog_path.exists(), f"Catálogo ausente em {catalog_path}"
    assert gt_path.exists(), f"Ground Truth ausente em {gt_path}"
    assert manifest_path.exists(), f"Manifesto ausente em {manifest_path}"

    cat_sha = _canonical_lf_sha256(catalog_path)
    gt_sha = _canonical_lf_sha256(gt_path)
    mf_sha = _canonical_lf_sha256(manifest_path)

    assert (
        cat_sha == EXPECTED_CATALOG_SHA256
    ), f"Catalog SHA mismatch: {cat_sha} != {EXPECTED_CATALOG_SHA256}"
    assert (
        gt_sha == EXPECTED_GROUND_TRUTH_SHA256
    ), f"Ground Truth SHA mismatch: {gt_sha} != {EXPECTED_GROUND_TRUTH_SHA256}"
    assert (
        mf_sha == EXPECTED_MANIFEST_SHA256
    ), f"Manifest SHA mismatch: {mf_sha} != {EXPECTED_MANIFEST_SHA256}"

    # 2. Carga e validação de schema / contratos
    catalog_records = load_catalog_materials(catalog_path)
    assert len(catalog_records) == 20, f"Esperado 20 materiais, obtido {len(catalog_records)}"
    records_by_id = {rec.material_id: rec for rec in catalog_records}
    assert len(records_by_id) == 20, "Identificadores de material duplicados no catálogo"

    gt_data = json.loads(gt_path.read_text(encoding="utf-8"))
    gt_records = [duplicate_pair_ground_truth_from_record(r) for r in gt_data]
    assert len(gt_records) == 10, f"Esperado 10 pares no GT, obtido {len(gt_records)}"

    manifest_data = json.loads(manifest_path.read_text(encoding="utf-8"))
    ctrl = manifest_data.get("control_metadata", {})
    assert ctrl.get("status") == "DRAFT", f"Status inválido: {ctrl.get('status')}"
    assert ctrl.get("freeze_state") == "FROZEN", f"Freeze state inválido: {ctrl.get('freeze_state')}"
    assert ctrl.get("evaluation_state") == "NOT_YET_EVALUATED", f"Evaluation state inválido: {ctrl.get('evaluation_state')}"
    assert ctrl.get("freeze_sha256") == EXPECTED_GROUND_TRUTH_SHA256, "freeze_sha256 incorreto no manifesto"

    manifest_cases = manifest_data.get("cases", [])
    manifest_by_case_id = {c["evaluation_case_id"]: c for c in manifest_cases}
    assert len(manifest_by_case_id) == 10, "Casos de manifesto inconsistentes"

    # 3. Execução estrita read-only caso a caso
    observations: list[Tranche01CaseObservation] = []

    for gt in gt_records:
        rec_a = records_by_id[gt.material_id_a]
        rec_b = records_by_id[gt.material_id_b]
        meta = manifest_by_case_id[gt.evaluation_case_id]

        # A) Predição de Candidate Blocking
        cand = is_candidate_pair(rec_a, rec_b)

        # B) Predição do Detector Heurístico (is_possible_duplicate)
        det = is_possible_duplicate(rec_a, rec_b)

        # C) Classificação do Detector frente ao Ground Truth
        if gt.is_duplicate and det:
            det_class = "TP"
        elif not gt.is_duplicate and det:
            det_class = "FP"
        elif not gt.is_duplicate and not det:
            det_class = "TN"
        else:
            det_class = "FN"

        # D) Classificação de Blocking frente ao Ground Truth
        if gt.is_duplicate and cand:
            block_class = "CANDIDATE_TP"
        elif gt.is_duplicate and not cand:
            block_class = "CANDIDATE_FN"
        elif not gt.is_duplicate and cand:
            block_class = "CANDIDATE_FP"
        else:
            block_class = "CANDIDATE_TN"

        observations.append(
            Tranche01CaseObservation(
                evaluation_case_id=gt.evaluation_case_id,
                stratum=meta["stratum"],
                challenge_class=meta["challenge_taxonomy_class"],
                material_id_a=gt.material_id_a,
                material_id_b=gt.material_id_b,
                ground_truth_is_duplicate=gt.is_duplicate,
                is_candidate=cand,
                is_possible_duplicate=det,
                detector_classification=det_class,
                blocking_classification=block_class,
            )
        )

    # 4. Cômputo metrológico das métricas segregadas
    # Bloco A: Blocking
    positives = [o for o in observations if o.ground_truth_is_duplicate]
    candidate_tp = sum(1 for o in positives if o.is_candidate)
    candidate_fn = sum(1 for o in positives if not o.is_candidate)
    positive_count = len(positives)
    candidate_recall = (candidate_tp / positive_count) if positive_count > 0 else 0.0

    total_pairs_challenge = len(observations)
    retained_candidate_pairs = sum(1 for o in observations if o.is_candidate)
    challenge_reduction_ratio = (
        (1.0 - (retained_candidate_pairs / total_pairs_challenge)) * 100.0
        if total_pairs_challenge > 0
        else 0.0
    )

    # Bloco B: Detector
    tp = sum(1 for o in observations if o.detector_classification == "TP")
    fp = sum(1 for o in observations if o.detector_classification == "FP")
    tn = sum(1 for o in observations if o.detector_classification == "TN")
    fn = sum(1 for o in observations if o.detector_classification == "FN")

    precision = (tp / (tp + fp)) if (tp + fp) > 0 else 0.0
    recall = (tp / (tp + fn)) if (tp + fn) > 0 else 0.0
    f1 = (2 * precision * recall / (precision + recall)) if (precision + recall) > 0 else 0.0

    # Breakdown por Challenge Class
    breakdown_class: dict[str, dict[str, Any]] = {}
    for o in observations:
        c = o.challenge_class
        if c not in breakdown_class:
            breakdown_class[c] = {
                "stratum": o.stratum,
                "gt_is_dup": o.ground_truth_is_duplicate,
                "is_candidate": o.is_candidate,
                "is_possible_duplicate": o.is_possible_duplicate,
                "det_class": o.detector_classification,
            }

    # Breakdown por Estrato
    breakdown_stratum: dict[str, dict[str, int]] = {}
    for o in observations:
        s = o.stratum
        if s not in breakdown_stratum:
            breakdown_stratum[s] = {"TP": 0, "FP": 0, "TN": 0, "FN": 0}
        breakdown_stratum[s][o.detector_classification] += 1

    summary = {
        "metadata": {
            "tranche": "01_EXPLORATORY_10_PAIRS",
            "evaluated_at": datetime.now(timezone.utc).isoformat(),
            "catalog_sha256": cat_sha,
            "ground_truth_sha256": gt_sha,
            "manifest_sha256": mf_sha,
        },
        "blocking_metrics": {
            "positive_count": positive_count,
            "candidate_tp": candidate_tp,
            "candidate_fn": candidate_fn,
            "candidate_recall": candidate_recall,
            "challenge_total_pairs": total_pairs_challenge,
            "challenge_retained_candidates": retained_candidate_pairs,
            "challenge_reduction_ratio_pct": challenge_reduction_ratio,
        },
        "detector_metrics": {
            "TP": tp,
            "FP": fp,
            "TN": tn,
            "FN": fn,
            "precision": precision,
            "recall": recall,
            "f1": f1,
        },
        "breakdown_by_class": breakdown_class,
        "breakdown_by_stratum": breakdown_stratum,
    }

    return observations, summary


def main() -> None:
    repo_root = Path(__file__).resolve().parent.parent
    base_dir = repo_root / "experiments" / "baseline_b"
    checkpoints_dir = repo_root / "experiments" / "checkpoints"

    print("================================================================================")
    print("SR-001 BASELINE B — TRANCHE 01: AVALIAÇÃO EXPERIMENTAL")
    print("================================================================================")

    observations, summary = evaluate_tranche_01(base_dir)

    print("\n--- 1. TABELA DE OBSERVAÇÕES DOS 10 CASOS ---")
    header = f"{'Case ID':<20} | {'Estrato':<12} | {'Classe':<14} | {'GT':<5} | {'Cand':<5} | {'Det':<5} | {'Classif':<7}"
    print(header)
    print("-" * len(header))
    for o in observations:
        gt_s = "DUP" if o.ground_truth_is_duplicate else "NOT"
        cand_s = "YES" if o.is_candidate else "NO"
        det_s = "DUP" if o.is_possible_duplicate else "NOT"
        print(
            f"{o.evaluation_case_id:<20} | {o.stratum:<12} | {o.challenge_class:<14} | "
            f"{gt_s:<5} | {cand_s:<5} | {det_s:<5} | {o.detector_classification:<7}"
        )

    bm = summary["blocking_metrics"]
    print("\n--- 2. MÉTRICAS DE CANDIDATE BLOCKING (PRESERVAÇÃO DO ESPAÇO) ---")
    print(f"Total de pares positivos no Ground Truth : {bm['positive_count']}")
    print(f"Verdadeiros Positivos retidos pelo blocking : {bm['candidate_tp']}")
    print(f"Falsos Negativos descartados pelo blocking  : {bm['candidate_fn']}")
    print(
        f"Candidate Pair Recall (Recall_block)        : {bm['candidate_tp']}/{bm['positive_count']} "
        f"({bm['candidate_recall'] * 100.0:.1f}%)"
    )
    print(
        f"Pares retidos na amostra de desafio         : {bm['challenge_retained_candidates']}/{bm['challenge_total_pairs']}"
    )
    print(
        f"Taxa de redução no Challenge Set            : {bm['challenge_reduction_ratio_pct']:.1f}% "
        "(Nota: Challenge-Set Reduction != RR Catalog-Wide)"
    )

    dm = summary["detector_metrics"]
    print("\n--- 3. MÉTRICAS DO DETECTOR HEURÍSTICO (is_possible_duplicate) ---")
    print(f"Verdadeiros Positivos (TP) : {dm['TP']}")
    print(f"Falsos Positivos (FP)      : {dm['FP']}")
    print(f"Verdadeiros Negativos (TN) : {dm['TN']}")
    print(f"Falsos Negativos (FN)      : {dm['FN']}")
    p_denom = dm["TP"] + dm["FP"]
    r_denom = dm["TP"] + dm["FN"]
    print(
        f"Precision                  : {dm['TP']}/{p_denom} ({dm['precision'] * 100.0:.1f}%)"
        if p_denom > 0
        else "Precision: N/A"
    )
    print(
        f"Recall                     : {dm['TP']}/{r_denom} ({dm['recall'] * 100.0:.1f}%)"
        if r_denom > 0
        else "Recall: N/A"
    )
    print(f"F1-Score                   : {dm['f1']:.4f}")

    print("\n--- 4. BREAKDOWN POR TAXONOMIA DE DESAFIO (CHALLENGE CLASS) ---")
    for cls_name, info in summary["breakdown_by_class"].items():
        gt_s = "DUP" if info["gt_is_dup"] else "NOT"
        det_s = "DUP" if info["is_possible_duplicate"] else "NOT"
        print(
            f"  {cls_name:<14} ({info['stratum']:<10}): GT={gt_s} -> Det={det_s} [{info['det_class']}] "
            f"(Candidate={info['is_candidate']})"
        )

    print("\n--- 5. BREAKDOWN POR ESTRATO INDUSTRIAL ---")
    for st, counts in summary["breakdown_by_stratum"].items():
        print(f"  {st:<12} : TP={counts['TP']}, FP={counts['FP']}, TN={counts['TN']}, FN={counts['FN']}")

    # Persistência de checkpoint de evidência experimental (H-034)
    checkpoints_dir.mkdir(parents=True, exist_ok=True)
    out_file = checkpoints_dir / "sr001_baseline_b_tranche_01_evidence.json"
    evidence_payload = {
        "summary": summary,
        "observations": [asdict(o) for o in observations],
    }
    out_file.write_text(json.dumps(evidence_payload, indent=2), encoding="utf-8")
    print(f"\n[OK] Checkpoint experimental persistido em: {out_file}")
    print("================================================================================")


if __name__ == "__main__":
    main()
