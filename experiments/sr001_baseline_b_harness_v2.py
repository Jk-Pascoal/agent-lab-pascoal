"""Harness Experimental Sucessor v2 para avaliação metrológica (SR-001 Baseline B).

Implementação conforme SPEC-0158-HARNESS-V2.
Preserva estritamente:
Ground Truth != Candidate Selection != Detector != Metrology.
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Sequence
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any

from agent_lab.catalog_csv_adapter import load_catalog_materials
from agent_lab.domain import MaterialRecord
from agent_lab.duplicates import is_possible_duplicate
from agent_lab.ground_truth import DuplicatePairGroundTruth
from agent_lab.ground_truth_serialization import duplicate_pair_ground_truth_from_record
from agent_lab.normalization import category_token, normalize_text


class CandidateSelectionOutcome(str, Enum):
    """Nomenclatura canônica de retenção/descarte do filtro de candidatos."""

    POSITIVE_RETAINED = "POSITIVE_RETAINED"
    POSITIVE_DROPPED = "POSITIVE_DROPPED"
    NEGATIVE_RETAINED = "NEGATIVE_RETAINED"
    NEGATIVE_DROPPED = "NEGATIVE_DROPPED"


class DetectorOutcome(str, Enum):
    """Nomenclatura clássica de matriz de confusão aplicada exclusivamente ao detector."""

    TRUE_POSITIVE = "TP"
    FALSE_POSITIVE = "FP"
    TRUE_NEGATIVE = "TN"
    FALSE_NEGATIVE = "FN"


@dataclass(frozen=True, slots=True)
class CandidateSelectionDecision:
    """Decisão topológica de Candidate Selection em memória."""

    is_candidate: bool
    matched_families: tuple[str, ...]
    family_1_key: tuple[str, str] | None
    family_2_key: tuple[str, str] | None


@dataclass(frozen=True, slots=True)
class CaseObservationV2:
    """Observação quadripartite de caso de avaliação no Harness v2."""

    evaluation_case_id: str
    stratum: str
    challenge_class: str
    material_id_a: str
    material_id_b: str
    ground_truth_is_duplicate: bool
    selection_decision: CandidateSelectionDecision
    selection_outcome: CandidateSelectionOutcome
    unconditioned_detector_prediction: bool
    unconditioned_detector_outcome: DetectorOutcome
    conditioned_detector_prediction: bool | None
    conditioned_detector_outcome: DetectorOutcome | None


@dataclass(frozen=True, slots=True)
class TrancheDescriptor:
    """Descritor imutável de tranche auditada e congelada."""

    tranche_id: str
    catalog_path: Path
    ground_truth_path: Path
    manifest_path: Path
    expected_catalog_sha256: str
    expected_ground_truth_sha256: str
    expected_manifest_sha256: str
    expected_material_count: int
    expected_pair_count: int


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


def evaluate_candidate_selection(
    record_a: MaterialRecord,
    record_b: MaterialRecord,
) -> CandidateSelectionDecision:
    """Predicado topológico puro de Candidate Selection.

    Retorna CandidateSelectionDecision contendo is_candidate, matched_families,
    e as chaves correspondentes.
    """
    p1_a, p2_a = extract_candidate_family_keys(record_a)
    p1_b, p2_b = extract_candidate_family_keys(record_b)

    fam1_match = (p1_a is not None) and (p1_a == p1_b)
    fam2_match = (p2_a is not None) and (p2_a == p2_b)

    matched: list[str] = []
    f1_key: tuple[str, str] | None = None
    f2_key: tuple[str, str] | None = None

    if fam1_match:
        matched.append("FAMILY_1")
        f1_key = p1_a
    if fam2_match:
        matched.append("FAMILY_2")
        f2_key = p2_a

    is_cand = fam1_match or fam2_match
    return CandidateSelectionDecision(
        is_candidate=is_cand,
        matched_families=tuple(matched),
        family_1_key=f1_key,
        family_2_key=f2_key,
    )


def is_candidate_pair(
    record_a: MaterialRecord,
    record_b: MaterialRecord,
) -> bool:
    """Helper booleano de Candidate Selection."""
    return evaluate_candidate_selection(record_a, record_b).is_candidate


def classify_candidate_selection_outcome(
    is_duplicate: bool,
    is_candidate: bool,
) -> CandidateSelectionOutcome:
    """Classifica o resultado de Candidate Selection frente ao Ground Truth."""
    if is_duplicate and is_candidate:
        return CandidateSelectionOutcome.POSITIVE_RETAINED
    if is_duplicate and not is_candidate:
        return CandidateSelectionOutcome.POSITIVE_DROPPED
    if not is_duplicate and is_candidate:
        return CandidateSelectionOutcome.NEGATIVE_RETAINED
    return CandidateSelectionOutcome.NEGATIVE_DROPPED


def classify_detector_outcome(
    is_duplicate: bool,
    is_possible_duplicate: bool,
) -> DetectorOutcome:
    """Classifica a decisão semântica do detector downstream."""
    if is_duplicate and is_possible_duplicate:
        return DetectorOutcome.TRUE_POSITIVE
    if not is_duplicate and is_possible_duplicate:
        return DetectorOutcome.FALSE_POSITIVE
    if not is_duplicate and not is_possible_duplicate:
        return DetectorOutcome.TRUE_NEGATIVE
    return DetectorOutcome.FALSE_NEGATIVE


@dataclass(frozen=True, slots=True)
class CandidateSelectionMetrics:
    """Bloco 1: Métricas de Candidate Selection."""

    positive_count: int
    positive_retained: int
    positive_dropped: int
    negative_retained: int
    negative_dropped: int
    candidate_pair_recall: float
    candidate_pair_miss_rate: float
    challenge_total_pairs: int
    challenge_retained_pairs: int
    challenge_retention_rate: float
    challenge_reduction_ratio: float


@dataclass(frozen=True, slots=True)
class DetectorMetrics:
    """Bloco 2: Métricas do Detector Incondicional."""

    tp: int
    fp: int
    tn: int
    fn: int
    precision: float
    recall: float
    f1: float


@dataclass(frozen=True, slots=True)
class ConditionedDetectorMetrics:
    """Bloco 3: Métricas do Detector Condicionado aos Candidatos."""

    evaluated_pairs_count: int
    tp: int
    fp: int
    tn: int
    fn: int
    precision: float
    recall: float
    f1: float


@dataclass(frozen=True, slots=True)
class EndToEndPipelineMetrics:
    """Bloco 4: Métricas do Pipeline End-to-End."""

    recall_block: float
    recall_detector_conditioned: float
    overall_pipeline_recall: float
    challenge_reduction_ratio: float
    bidimensional_point: tuple[float, float]


def compute_candidate_selection_metrics(
    observations: Sequence[CaseObservationV2],
) -> CandidateSelectionMetrics:
    """Calcula métricas do Bloco 1 (Candidate Selection)."""
    total_pairs = len(observations)
    positives = [o for o in observations if o.ground_truth_is_duplicate]
    positive_count = len(positives)
    pos_retained = sum(
        1 for o in observations if o.selection_outcome == CandidateSelectionOutcome.POSITIVE_RETAINED
    )
    pos_dropped = sum(
        1 for o in observations if o.selection_outcome == CandidateSelectionOutcome.POSITIVE_DROPPED
    )
    neg_retained = sum(
        1 for o in observations if o.selection_outcome == CandidateSelectionOutcome.NEGATIVE_RETAINED
    )
    neg_dropped = sum(
        1 for o in observations if o.selection_outcome == CandidateSelectionOutcome.NEGATIVE_DROPPED
    )

    recall_block = (pos_retained / positive_count) if positive_count > 0 else 0.0
    miss_rate = 1.0 - recall_block if positive_count > 0 else 0.0
    retained_pairs = pos_retained + neg_retained
    retention_rate = (retained_pairs / total_pairs) if total_pairs > 0 else 0.0
    reduction_ratio = 1.0 - retention_rate if total_pairs > 0 else 0.0

    return CandidateSelectionMetrics(
        positive_count=positive_count,
        positive_retained=pos_retained,
        positive_dropped=pos_dropped,
        negative_retained=neg_retained,
        negative_dropped=neg_dropped,
        candidate_pair_recall=recall_block,
        candidate_pair_miss_rate=miss_rate,
        challenge_total_pairs=total_pairs,
        challenge_retained_pairs=retained_pairs,
        challenge_retention_rate=retention_rate,
        challenge_reduction_ratio=reduction_ratio,
    )


def compute_unconditioned_detector_metrics(
    observations: Sequence[CaseObservationV2],
) -> DetectorMetrics:
    """Calcula métricas do Bloco 2 (Detector Incondicional sobre todos os pares)."""
    tp = sum(1 for o in observations if o.unconditioned_detector_outcome == DetectorOutcome.TRUE_POSITIVE)
    fp = sum(1 for o in observations if o.unconditioned_detector_outcome == DetectorOutcome.FALSE_POSITIVE)
    tn = sum(1 for o in observations if o.unconditioned_detector_outcome == DetectorOutcome.TRUE_NEGATIVE)
    fn = sum(1 for o in observations if o.unconditioned_detector_outcome == DetectorOutcome.FALSE_NEGATIVE)

    prec = (tp / (tp + fp)) if (tp + fp) > 0 else 0.0
    rec = (tp / (tp + fn)) if (tp + fn) > 0 else 0.0
    f1 = (2 * prec * rec / (prec + rec)) if (prec + rec) > 0 else 0.0

    return DetectorMetrics(
        tp=tp,
        fp=fp,
        tn=tn,
        fn=fn,
        precision=prec,
        recall=rec,
        f1=f1,
    )


def compute_conditioned_detector_metrics(
    observations: Sequence[CaseObservationV2],
) -> ConditionedDetectorMetrics:
    """Calcula métricas do Bloco 3 (Detector Condicionado aos pares retidos)."""
    cond_obs = [o for o in observations if o.selection_decision.is_candidate]
    eval_count = len(cond_obs)
    tp = sum(1 for o in cond_obs if o.conditioned_detector_outcome == DetectorOutcome.TRUE_POSITIVE)
    fp = sum(1 for o in cond_obs if o.conditioned_detector_outcome == DetectorOutcome.FALSE_POSITIVE)
    tn = sum(1 for o in cond_obs if o.conditioned_detector_outcome == DetectorOutcome.TRUE_NEGATIVE)
    fn = sum(1 for o in cond_obs if o.conditioned_detector_outcome == DetectorOutcome.FALSE_NEGATIVE)

    prec = (tp / (tp + fp)) if (tp + fp) > 0 else 0.0
    rec = (tp / (tp + fn)) if (tp + fn) > 0 else 0.0
    f1 = (2 * prec * rec / (prec + rec)) if (prec + rec) > 0 else 0.0

    return ConditionedDetectorMetrics(
        evaluated_pairs_count=eval_count,
        tp=tp,
        fp=fp,
        tn=tn,
        fn=fn,
        precision=prec,
        recall=rec,
        f1=f1,
    )


def compute_end_to_end_metrics(
    selection_metrics: CandidateSelectionMetrics,
    conditioned_detector_metrics: ConditionedDetectorMetrics,
) -> EndToEndPipelineMetrics:
    """Calcula métricas do Bloco 4 (Pipeline End-to-End)."""
    rec_block = selection_metrics.candidate_pair_recall
    rec_det = conditioned_detector_metrics.recall
    overall_pipeline_recall = rec_block * rec_det
    rr = selection_metrics.challenge_reduction_ratio

    return EndToEndPipelineMetrics(
        recall_block=rec_block,
        recall_detector_conditioned=rec_det,
        overall_pipeline_recall=overall_pipeline_recall,
        challenge_reduction_ratio=rr,
        bidimensional_point=(rr, overall_pipeline_recall),
    )


def compute_canonical_lf_sha256(path: Path) -> str:
    """Calcula SHA-256 normalizado para bytes Unix LF (independente de checkout CRLF no Windows)."""
    raw_bytes = path.read_bytes().replace(b"\r\n", b"\n")
    return hashlib.sha256(raw_bytes).hexdigest()


def load_and_validate_tranche(
    descriptor: TrancheDescriptor,
) -> tuple[tuple[MaterialRecord, ...], tuple[DuplicatePairGroundTruth, ...], dict[str, dict[str, Any]]]:
    """Valida integridade estrita de hashes, manifesto e referências de uma tranche.

    Retorna tuplas imutáveis de (catalog_records, ground_truth_records, manifest_cases_by_id).
    Falha imediatamente (fail-closed) com AssertionError caso haja qualquer divergência.
    """
    if not descriptor.catalog_path.exists():
        raise AssertionError(f"Catálogo ausente em {descriptor.catalog_path}")
    if not descriptor.ground_truth_path.exists():
        raise AssertionError(f"Ground Truth ausente em {descriptor.ground_truth_path}")
    if not descriptor.manifest_path.exists():
        raise AssertionError(f"Manifesto ausente em {descriptor.manifest_path}")

    cat_sha = compute_canonical_lf_sha256(descriptor.catalog_path)
    gt_sha = compute_canonical_lf_sha256(descriptor.ground_truth_path)
    mf_sha = compute_canonical_lf_sha256(descriptor.manifest_path)

    if cat_sha != descriptor.expected_catalog_sha256:
        raise AssertionError(
            f"Catalog SHA mismatch: {cat_sha} != {descriptor.expected_catalog_sha256}"
        )
    if gt_sha != descriptor.expected_ground_truth_sha256:
        raise AssertionError(
            f"Ground Truth SHA mismatch: {gt_sha} != {descriptor.expected_ground_truth_sha256}"
        )
    if mf_sha != descriptor.expected_manifest_sha256:
        raise AssertionError(
            f"Manifest SHA mismatch: {mf_sha} != {descriptor.expected_manifest_sha256}"
        )

    # 1. Manifesto: validação de controle e unicidade de casos ANTES do dict
    manifest_data = json.loads(descriptor.manifest_path.read_text(encoding="utf-8"))
    ctrl = manifest_data.get("control_metadata", {})
    if ctrl.get("status") != "DRAFT":
        raise AssertionError(f"Status inválido no manifesto: {ctrl.get('status')}")
    if ctrl.get("freeze_state") != "FROZEN":
        raise AssertionError(f"Freeze state inválido no manifesto: {ctrl.get('freeze_state')}")
    if ctrl.get("freeze_sha256") != descriptor.expected_ground_truth_sha256:
        raise AssertionError(
            f"freeze_sha256 incorreto no manifesto: {ctrl.get('freeze_sha256')} != {descriptor.expected_ground_truth_sha256}"
        )

    manifest_cases = manifest_data.get("cases", [])
    manifest_case_ids = [c["evaluation_case_id"] for c in manifest_cases]

    # Validação da quantidade bruta de casos no manifesto
    if len(manifest_case_ids) != descriptor.expected_pair_count:
        raise AssertionError(
            f"Casos de manifesto inconsistentes: esperado {descriptor.expected_pair_count}, obtido {len(manifest_case_ids)}"
        )

    # Validação de unicidade de evaluation_case_id no manifesto
    if len(set(manifest_case_ids)) != len(manifest_case_ids):
        raise AssertionError("Duplicidade de evaluation_case_id detectada no manifesto")

    # Somente após validação de unicidade constrói o dicionário
    manifest_by_case_id = {c["evaluation_case_id"]: c for c in manifest_cases}

    # 2. Catálogo: validação de cardinalidade e unicidade de materiais
    catalog_records = load_catalog_materials(descriptor.catalog_path)
    if len(catalog_records) != descriptor.expected_material_count:
        raise AssertionError(
            f"Esperado {descriptor.expected_material_count} materiais, obtido {len(catalog_records)}"
        )
    records_by_id = {rec.material_id: rec for rec in catalog_records}
    if len(records_by_id) != descriptor.expected_material_count:
        raise AssertionError("Identificadores de material duplicados no catálogo")

    # 3. Ground Truth: validação de cardinalidade e unicidade de casos
    gt_data = json.loads(descriptor.ground_truth_path.read_text(encoding="utf-8"))
    gt_records = tuple(duplicate_pair_ground_truth_from_record(r) for r in gt_data)
    if len(gt_records) != descriptor.expected_pair_count:
        raise AssertionError(
            f"Esperado {descriptor.expected_pair_count} pares no GT, obtido {len(gt_records)}"
        )

    # 4. Integridade referencial biunívoca (1:1)
    gt_case_ids: set[str] = set()
    for gt in gt_records:
        if gt.material_id_a not in records_by_id:
            raise AssertionError(f"Material {gt.material_id_a} do GT ausente no catálogo")
        if gt.material_id_b not in records_by_id:
            raise AssertionError(f"Material {gt.material_id_b} do GT ausente no catálogo")
        if gt.evaluation_case_id not in manifest_by_case_id:
            raise AssertionError(f"Caso {gt.evaluation_case_id} do GT ausente no manifesto")
        if gt.evaluation_case_id in gt_case_ids:
            raise AssertionError(f"Caso {gt.evaluation_case_id} duplicado no GT")
        gt_case_ids.add(gt.evaluation_case_id)

    if gt_case_ids != set(manifest_case_ids):
        raise AssertionError("Correspondência 1:1 violada entre GT e manifesto")

    return catalog_records, gt_records, manifest_by_case_id


def _to_json_native(obj: Any) -> Any:
    """Converte estruturas em tipos JSON-native primitivos de forma pura e determinística."""
    if isinstance(obj, Enum):
        return obj.value
    if isinstance(obj, (list, tuple)):
        return [_to_json_native(item) for item in obj]
    if isinstance(obj, set):
        return sorted(_to_json_native(item) for item in obj)
    if isinstance(obj, dict):
        return {str(k): _to_json_native(v) for k, v in obj.items()}
    if hasattr(obj, "__dataclass_fields__"):
        return {k: _to_json_native(v) for k, v in asdict(obj).items()}
    return obj


def evaluate_tranche(
    descriptor: TrancheDescriptor,
) -> tuple[tuple[CaseObservationV2, ...], dict[str, Any]]:
    """Executa a avaliação metrológica determinística de uma tranche congelada."""
    catalog_records, gt_records, manifest_by_case_id = load_and_validate_tranche(descriptor)
    records_by_id = {rec.material_id: rec for rec in catalog_records}

    # Ordenação determinística estrita por evaluation_case_id
    sorted_gt = sorted(gt_records, key=lambda g: g.evaluation_case_id)
    observations: list[CaseObservationV2] = []

    for gt in sorted_gt:
        rec_a = records_by_id[gt.material_id_a]
        rec_b = records_by_id[gt.material_id_b]
        meta = manifest_by_case_id[gt.evaluation_case_id]

        sel_dec = evaluate_candidate_selection(rec_a, rec_b)
        sel_outcome = classify_candidate_selection_outcome(gt.is_duplicate, sel_dec.is_candidate)

        uncond_pred = is_possible_duplicate(rec_a, rec_b)
        uncond_outcome = classify_detector_outcome(gt.is_duplicate, uncond_pred)

        cond_pred = uncond_pred if sel_dec.is_candidate else None
        cond_outcome = (
            classify_detector_outcome(gt.is_duplicate, cond_pred)
            if sel_dec.is_candidate
            else None
        )

        observations.append(
            CaseObservationV2(
                evaluation_case_id=gt.evaluation_case_id,
                stratum=meta["stratum"],
                challenge_class=meta["challenge_taxonomy_class"],
                material_id_a=gt.material_id_a,
                material_id_b=gt.material_id_b,
                ground_truth_is_duplicate=gt.is_duplicate,
                selection_decision=sel_dec,
                selection_outcome=sel_outcome,
                unconditioned_detector_prediction=uncond_pred,
                unconditioned_detector_outcome=uncond_outcome,
                conditioned_detector_prediction=cond_pred,
                conditioned_detector_outcome=cond_outcome,
            )
        )

    # 4 Blocos de métricas metrológicas segregadas
    sel_metrics = compute_candidate_selection_metrics(observations)
    uncond_metrics = compute_unconditioned_detector_metrics(observations)
    cond_metrics = compute_conditioned_detector_metrics(observations)
    e2e_metrics = compute_end_to_end_metrics(sel_metrics, cond_metrics)

    # Breakdown agregado por Challenge Class (ordenado deterministicamente sem colapsar casos)
    class_groups: dict[str, list[CaseObservationV2]] = {}
    for o in observations:
        class_groups.setdefault(o.challenge_class, []).append(o)

    breakdown_by_class: dict[str, dict[str, Any]] = {}
    for c in sorted(class_groups.keys()):
        c_obs = class_groups[c]
        breakdown_by_class[c] = {
            "strata": sorted({o.stratum for o in c_obs}),
            "total_cases": len(c_obs),
            "positive_count": sum(1 for o in c_obs if o.ground_truth_is_duplicate),
            "negative_count": sum(1 for o in c_obs if not o.ground_truth_is_duplicate),
            "candidate_retained_count": sum(1 for o in c_obs if o.selection_decision.is_candidate),
            "candidate_dropped_count": sum(1 for o in c_obs if not o.selection_decision.is_candidate),
            "tp": sum(1 for o in c_obs if o.unconditioned_detector_outcome == DetectorOutcome.TRUE_POSITIVE),
            "fp": sum(1 for o in c_obs if o.unconditioned_detector_outcome == DetectorOutcome.FALSE_POSITIVE),
            "tn": sum(1 for o in c_obs if o.unconditioned_detector_outcome == DetectorOutcome.TRUE_NEGATIVE),
            "fn": sum(1 for o in c_obs if o.unconditioned_detector_outcome == DetectorOutcome.FALSE_NEGATIVE),
            "case_ids": [o.evaluation_case_id for o in c_obs],
        }

    # Breakdown agregado por Estrato Industrial (ordenado deterministicamente)
    stratum_groups: dict[str, list[CaseObservationV2]] = {}
    for o in observations:
        stratum_groups.setdefault(o.stratum, []).append(o)

    breakdown_by_stratum: dict[str, dict[str, Any]] = {}
    for s in sorted(stratum_groups.keys()):
        s_obs = stratum_groups[s]
        breakdown_by_stratum[s] = {
            "total_cases": len(s_obs),
            "positive_count": sum(1 for o in s_obs if o.ground_truth_is_duplicate),
            "negative_count": sum(1 for o in s_obs if not o.ground_truth_is_duplicate),
            "candidate_retained_count": sum(1 for o in s_obs if o.selection_decision.is_candidate),
            "candidate_dropped_count": sum(1 for o in s_obs if not o.selection_decision.is_candidate),
            "tp": sum(1 for o in s_obs if o.unconditioned_detector_outcome == DetectorOutcome.TRUE_POSITIVE),
            "fp": sum(1 for o in s_obs if o.unconditioned_detector_outcome == DetectorOutcome.FALSE_POSITIVE),
            "tn": sum(1 for o in s_obs if o.unconditioned_detector_outcome == DetectorOutcome.TRUE_NEGATIVE),
            "fn": sum(1 for o in s_obs if o.unconditioned_detector_outcome == DetectorOutcome.FALSE_NEGATIVE),
            "case_ids": [o.evaluation_case_id for o in s_obs],
        }

    # Inventário exaustivo de casos críticos: POSITIVE_DROPPED ou FP
    critical_inventory = [
        _to_json_native(o)
        for o in observations
        if (
            o.selection_outcome == CandidateSelectionOutcome.POSITIVE_DROPPED
            or o.unconditioned_detector_outcome == DetectorOutcome.FALSE_POSITIVE
        )
    ]

    summary = {
        "tranche_id": descriptor.tranche_id,
        "candidate_selection_metrics": _to_json_native(sel_metrics),
        "unconditioned_detector_metrics": _to_json_native(uncond_metrics),
        "conditioned_detector_metrics": _to_json_native(cond_metrics),
        "end_to_end_pipeline_metrics": _to_json_native(e2e_metrics),
        "breakdown_by_class": breakdown_by_class,
        "breakdown_by_stratum": breakdown_by_stratum,
        "critical_inventory": critical_inventory,
    }

    return tuple(observations), summary


def build_evidence_payload(
    summary: dict[str, Any],
    observations: Sequence[CaseObservationV2],
    descriptor: TrancheDescriptor,
    run_id: str,
    evaluated_at: datetime,
    harness_script_path: Path | None = None,
) -> dict[str, Any]:
    """Constrói o envelope de evidência auditável segregando metadados de execução do payload científico em formato JSON-native."""
    if harness_script_path is None:
        harness_script_path = Path(__file__).resolve()
    harness_sha = compute_canonical_lf_sha256(harness_script_path)

    metadata = {
        "harness_identifier": "SR001-BASELINE-B-HARNESS-V2",
        "harness_sha256": harness_sha,
        "catalog_sha256": descriptor.expected_catalog_sha256,
        "ground_truth_sha256": descriptor.expected_ground_truth_sha256,
        "manifest_sha256": descriptor.expected_manifest_sha256,
        "run_id": run_id,
        "evaluated_at": evaluated_at.isoformat(),
    }

    scientific_payload = {
        "summary": _to_json_native(summary),
        "observations": [_to_json_native(o) for o in observations],
    }

    return {
        "metadata": metadata,
        "scientific_payload": scientific_payload,
    }


if __name__ == "__main__":
    print("SR-001 Baseline B Experimental Harness v2")
    print("Módulo experimental de instrumentação metrológica.")
    print("Execução experimental bloqueada: depende de autorização formal (Gate 4 HUMAN GO).")
