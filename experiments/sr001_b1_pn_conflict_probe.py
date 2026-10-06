"""Sonda Experimental Segregada B1 — Structured Part-Number Disagreement (SR-001 / Issue #158).

Implementação experimental contrafactual mínima e controlada sobre a Tranche 02 congelada.
MÓDULO EXCLUSIVAMENTE EXPERIMENTAL — NÃO É REGRA DE PRODUÇÃO.
src/agent_lab/ permanece 100% intocado.
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

from agent_lab.domain import MaterialRecord
from agent_lab.duplicates import is_possible_duplicate
from agent_lab.normalization import (
    category_token,
    normalize_text,
    numeric_tokens,
    word_tokens,
)
from experiments.sr001_baseline_b_harness_v2 import (
    CandidateSelectionOutcome,
    DetectorOutcome,
    TrancheDescriptor,
    _to_json_native,
    classify_candidate_selection_outcome,
    classify_detector_outcome,
    compute_canonical_lf_sha256,
    evaluate_candidate_selection,
    load_and_validate_tranche,
)


class DetectorRoute(str, Enum):
    """Rota de decisão observada no detector do produto."""

    ROUTE_1 = "ROUTE_1"
    ROUTE_2 = "ROUTE_2"
    NONE = "NONE"


@dataclass(frozen=True, slots=True)
class B1CaseObservation:
    """Observação comparativa e rastreável de um par sob B0 vs intervenção B1."""

    evaluation_case_id: str
    stratum: str
    challenge_class: str
    material_id_a: str
    material_id_b: str
    ground_truth_is_duplicate: bool
    # Candidate Selection
    is_candidate: bool
    selection_outcome: CandidateSelectionOutcome
    # B0 (Baseline Original)
    prediction_original: bool
    outcome_original: DetectorOutcome
    route_original: DetectorRoute
    # S1 / PN Conflict Probe
    normalized_pn_a: str
    normalized_pn_b: str
    pn_conflict: bool
    # B1 (Intervenção Segregada)
    prediction_b1: bool
    outcome_b1: DetectorOutcome
    decision_changed: bool
    # Visão Condicionada (Candidatos Retidos)
    conditioned_prediction_original: bool | None
    conditioned_outcome_original: DetectorOutcome | None
    conditioned_prediction_b1: bool | None
    conditioned_outcome_b1: DetectorOutcome | None


@dataclass(frozen=True, slots=True)
class ConfusionMetrics:
    """Métricas clássicas de matriz de confusão."""

    tp: int
    fp: int
    tn: int
    fn: int
    precision: float
    recall: float
    f1: float


def _full_description(record: MaterialRecord) -> str:
    """Reutiliza a semântica canônica de descrição composta do produto."""
    return f"{record.description_short} {record.long_description}".strip()


def check_pn_conflict(
    record_a: MaterialRecord,
    record_b: MaterialRecord,
) -> tuple[bool, str, str]:
    """Predicado operacional mínimo de conflito estruturado de part number (S1).

    Retorna (has_conflict, pn_a_normalizado, pn_b_normalizado).
    pn_conflict == True somente quando:
    1. manufacturer_part_number de A é preenchido após normalização;
    2. manufacturer_part_number de B é preenchido após normalização;
    3. os dois PNs normalizados são diferentes.
    Ausência de PN em qualquer lado resulta em False.
    """
    norm_pn_a = normalize_text(record_a.manufacturer_part_number)
    norm_pn_b = normalize_text(record_b.manufacturer_part_number)

    has_conflict = bool(norm_pn_a) and bool(norm_pn_b) and (norm_pn_a != norm_pn_b)
    return has_conflict, norm_pn_a, norm_pn_b


def detect_original_decision(
    incoming: MaterialRecord,
    existing: MaterialRecord,
) -> tuple[bool, DetectorRoute]:
    """Executa a decisão original do detector registrando deterministicamente a rota utilizada.

    Garante equivalência estrita:
    detect_original_decision(a, b)[0] == is_possible_duplicate(a, b).
    """
    if incoming.material_id == existing.material_id:
        return False, DetectorRoute.NONE

    incoming_part = normalize_text(incoming.manufacturer_part_number)
    existing_part = normalize_text(existing.manufacturer_part_number)
    incoming_manufacturer = normalize_text(incoming.manufacturer)
    existing_manufacturer = normalize_text(existing.manufacturer)

    # Rota 1: PN e fabricante preenchidos e coincidentes
    if (
        incoming_part
        and incoming_part == existing_part
        and incoming_manufacturer
        and incoming_manufacturer == existing_manufacturer
    ):
        return True, DetectorRoute.ROUTE_1

    # Rota 2: Grupo, Category Token e sobreposição numérica/lexical
    if normalize_text(incoming.material_group) != normalize_text(
        existing.material_group
    ):
        return False, DetectorRoute.NONE

    incoming_description = _full_description(incoming)
    existing_description = _full_description(existing)

    if category_token(incoming_description) != category_token(existing_description):
        return False, DetectorRoute.NONE

    shared_numbers = numeric_tokens(incoming_description) & numeric_tokens(
        existing_description
    )
    shared_words = word_tokens(incoming_description) & word_tokens(existing_description)

    if len(shared_numbers) >= 2 and len(shared_words) >= 1:
        return True, DetectorRoute.ROUTE_2

    return False, DetectorRoute.NONE


def evaluate_decision_b1(
    record_a: MaterialRecord,
    record_b: MaterialRecord,
) -> tuple[bool, bool, DetectorRoute, bool, str, str]:
    """Avalia o par sob o modelo contrafactual B1.

    Modelo conceitual:
    original_prediction = detector_original(A, B)
    if original_prediction is True
       AND decisão original ocorreu pela Rota 2
       AND pn_conflict(A, B):
           prediction_B1 = False
    else:
           prediction_B1 = original_prediction

    Retorna:
    (prediction_b1, prediction_original, route_original, pn_conflict, pn_a, pn_b)
    """
    pred_orig, route_orig = detect_original_decision(record_a, record_b)
    has_conflict, pn_a, pn_b = check_pn_conflict(record_a, record_b)

    if pred_orig and route_orig == DetectorRoute.ROUTE_2 and has_conflict:
        pred_b1 = False
    else:
        pred_b1 = pred_orig

    return pred_b1, pred_orig, route_orig, has_conflict, pn_a, pn_b


def compute_confusion_metrics(
    pairs: Sequence[tuple[bool, bool]],
) -> ConfusionMetrics:
    """Calcula TP, FP, TN, FN, Precision, Recall e F1 para uma sequência de (gt_is_dup, pred)."""
    tp = sum(1 for gt, pred in pairs if gt and pred)
    fp = sum(1 for gt, pred in pairs if not gt and pred)
    tn = sum(1 for gt, pred in pairs if not gt and not pred)
    fn = sum(1 for gt, pred in pairs if gt and not pred)

    prec = (tp / (tp + fp)) if (tp + fp) > 0 else 0.0
    rec = (tp / (tp + fn)) if (tp + fn) > 0 else 0.0
    f1 = (2 * prec * rec / (prec + rec)) if (prec + rec) > 0 else 0.0

    return ConfusionMetrics(
        tp=tp,
        fp=fp,
        tn=tn,
        fn=fn,
        precision=prec,
        recall=rec,
        f1=f1,
    )


def get_tranche_02_descriptor(repo_root: Path | None = None) -> TrancheDescriptor:
    """Constrói o descritor imutável auditado da Tranche 02 congelada."""
    if repo_root is None:
        repo_root = Path(__file__).resolve().parent.parent

    return TrancheDescriptor(
        tranche_id="02_EXPANDED_40_PAIRS",
        catalog_path=repo_root / "experiments" / "baseline_b" / "draft_tranche_02_catalog.csv",
        ground_truth_path=repo_root / "experiments" / "baseline_b" / "draft_tranche_02_ground_truth.json",
        manifest_path=repo_root / "experiments" / "baseline_b" / "draft_tranche_02_manifest.json",
        expected_catalog_sha256="74e1389f66fd14155dba1b3be9b16ef2ef9fe79b04e16232d2c2fb142e1c218b",
        expected_ground_truth_sha256="052bd6fec3f165cea9cdbf686cb961af4eccf962f4689d938a00fdc459b92008",
        expected_manifest_sha256="cab0732e83594111522e5edfd8c4bc1ff310c4be2df0b1d4c282b40a4f48a88b",
        expected_material_count=80,
        expected_pair_count=40,
    )


def evaluate_tranche_b1(
    descriptor: TrancheDescriptor,
) -> tuple[tuple[B1CaseObservation, ...], dict[str, Any]]:
    """Executa a avaliação experimental completa B0 vs B1 sobre a tranche congelada."""
    catalog_records, gt_records, manifest_by_case_id = load_and_validate_tranche(descriptor)
    records_by_id = {r.material_id: r for r in catalog_records}

    # Ordenação determinística estrita por evaluation_case_id
    sorted_gt = sorted(gt_records, key=lambda g: g.evaluation_case_id)
    observations: list[B1CaseObservation] = []

    for gt in sorted_gt:
        rec_a = records_by_id[gt.material_id_a]
        rec_b = records_by_id[gt.material_id_b]
        meta = manifest_by_case_id[gt.evaluation_case_id]

        # Candidate Selection permanece estritamente idêntico ao Baseline B v2
        sel_dec = evaluate_candidate_selection(rec_a, rec_b)
        sel_outcome = classify_candidate_selection_outcome(gt.is_duplicate, sel_dec.is_candidate)

        # Avaliação B0 e B1
        pred_b1, pred_orig, route_orig, has_conflict, pn_a, pn_b = evaluate_decision_b1(
            rec_a, rec_b
        )

        outcome_orig = classify_detector_outcome(gt.is_duplicate, pred_orig)
        outcome_b1 = classify_detector_outcome(gt.is_duplicate, pred_b1)

        # Visão condicionada aos pares retidos por Candidate Selection
        cond_pred_orig = pred_orig if sel_dec.is_candidate else None
        cond_outcome_orig = outcome_orig if sel_dec.is_candidate else None
        cond_pred_b1 = pred_b1 if sel_dec.is_candidate else None
        cond_outcome_b1 = outcome_b1 if sel_dec.is_candidate else None

        observations.append(
            B1CaseObservation(
                evaluation_case_id=gt.evaluation_case_id,
                stratum=meta["stratum"],
                challenge_class=meta["challenge_taxonomy_class"],
                material_id_a=gt.material_id_a,
                material_id_b=gt.material_id_b,
                ground_truth_is_duplicate=gt.is_duplicate,
                is_candidate=sel_dec.is_candidate,
                selection_outcome=sel_outcome,
                prediction_original=pred_orig,
                outcome_original=outcome_orig,
                route_original=route_orig,
                normalized_pn_a=pn_a,
                normalized_pn_b=pn_b,
                pn_conflict=has_conflict,
                prediction_b1=pred_b1,
                outcome_b1=outcome_b1,
                decision_changed=(pred_orig != pred_b1),
                conditioned_prediction_original=cond_pred_orig,
                conditioned_outcome_original=cond_outcome_orig,
                conditioned_prediction_b1=cond_pred_b1,
                conditioned_outcome_b1=cond_outcome_b1,
            )
        )

    # 1. Métricas B0
    b0_uncond_metrics = compute_confusion_metrics(
        [(o.ground_truth_is_duplicate, o.prediction_original) for o in observations]
    )
    b0_cond_obs = [o for o in observations if o.is_candidate]
    b0_cond_metrics = compute_confusion_metrics(
        [(o.ground_truth_is_duplicate, o.prediction_original) for o in b0_cond_obs]
    )

    # 2. Métricas B1
    b1_uncond_metrics = compute_confusion_metrics(
        [(o.ground_truth_is_duplicate, o.prediction_b1) for o in observations]
    )
    b1_cond_metrics = compute_confusion_metrics(
        [(o.ground_truth_is_duplicate, o.prediction_b1) for o in b0_cond_obs]
    )

    # 3. Métricas Comparativas
    delta_fp = b0_uncond_metrics.fp - b1_uncond_metrics.fp
    delta_recall_p = b0_uncond_metrics.recall - b1_uncond_metrics.recall

    conflicts = [o for o in observations if o.pn_conflict]
    conflict_breakdown_b0 = {
        "TP": sum(1 for o in conflicts if o.outcome_original == DetectorOutcome.TRUE_POSITIVE),
        "FP": sum(1 for o in conflicts if o.outcome_original == DetectorOutcome.FALSE_POSITIVE),
        "TN": sum(1 for o in conflicts if o.outcome_original == DetectorOutcome.TRUE_NEGATIVE),
        "FN": sum(1 for o in conflicts if o.outcome_original == DetectorOutcome.FALSE_NEGATIVE),
    }

    changed_cases = [
        {
            "evaluation_case_id": o.evaluation_case_id,
            "stratum": o.stratum,
            "challenge_class": o.challenge_class,
            "material_id_a": o.material_id_a,
            "material_id_b": o.material_id_b,
            "ground_truth_is_duplicate": o.ground_truth_is_duplicate,
            "route_original": o.route_original.value,
            "normalized_pn_a": o.normalized_pn_a,
            "normalized_pn_b": o.normalized_pn_b,
            "outcome_b0": o.outcome_original.value,
            "outcome_b1": o.outcome_b1.value,
        }
        for o in observations
        if o.decision_changed
    ]

    # Breakdown por Modos de Falha Empíricos FM-1 a FM-4
    fm_mapping = {
        "FM-1": ("HN-DIM", "Divergência Dimensional"),
        "FM-2": ("HN-MAT", "Divergência de Materialidade"),
        "FM-3": ("HN-VAR", "Variante Construtiva / Montagem"),
        "FM-4": ("HN-DISTINCT", "Subtipo / Princípio Físico"),
    }
    fm_breakdown: dict[str, dict[str, Any]] = {}
    for fm_key, (chal_cls, desc_label) in fm_mapping.items():
        fm_cases = [o for o in observations if o.challenge_class == chal_cls]
        fp_b0 = sum(1 for o in fm_cases if o.outcome_original == DetectorOutcome.FALSE_POSITIVE)
        fp_b1 = sum(1 for o in fm_cases if o.outcome_b1 == DetectorOutcome.FALSE_POSITIVE)
        suppressed = fp_b0 - fp_b1
        rate = (suppressed / fp_b0) if fp_b0 > 0 else 0.0
        fm_breakdown[fm_key] = {
            "label": desc_label,
            "challenge_class": chal_cls,
            "total_cases": len(fm_cases),
            "fp_b0": fp_b0,
            "fp_b1": fp_b1,
            "suppressed_fp": suppressed,
            "suppression_rate": rate,
            "case_ids": [o.evaluation_case_id for o in fm_cases],
        }

    # Breakdown por Classes Positivas (para análise de perda de Recall)
    positive_classes = sorted({o.challenge_class for o in observations if o.ground_truth_is_duplicate})
    pos_breakdown: dict[str, dict[str, Any]] = {}
    for p_cls in positive_classes:
        p_cases = [o for o in observations if o.challenge_class == p_cls]
        tp_b0 = sum(1 for o in p_cases if o.outcome_original == DetectorOutcome.TRUE_POSITIVE)
        tp_b1 = sum(1 for o in p_cases if o.outcome_b1 == DetectorOutcome.TRUE_POSITIVE)
        sacrificed = tp_b0 - tp_b1
        pos_breakdown[p_cls] = {
            "total_cases": len(p_cases),
            "tp_b0": tp_b0,
            "tp_b1": tp_b1,
            "sacrificed_tp": sacrificed,
            "case_ids": [o.evaluation_case_id for o in p_cases],
        }

    summary = {
        "tranche_id": descriptor.tranche_id,
        "total_pairs_evaluated": len(observations),
        "b0_unconditioned_metrics": _to_json_native(b0_uncond_metrics),
        "b0_conditioned_metrics": _to_json_native(b0_cond_metrics),
        "b1_unconditioned_metrics": _to_json_native(b1_uncond_metrics),
        "b1_conditioned_metrics": _to_json_native(b1_cond_metrics),
        "comparative_metrics": {
            "delta_fp": delta_fp,
            "delta_recall_p": delta_recall_p,
            "safety_goal_delta_recall_zero_satisfied": bool(delta_recall_p == 0.0),
            "total_pairs_with_pn_conflict": len(conflicts),
            "conflict_breakdown_in_b0": conflict_breakdown_b0,
            "changed_decisions_count": len(changed_cases),
            "changed_cases": changed_cases,
        },
        "failure_mode_breakdown": fm_breakdown,
        "positive_classes_breakdown": pos_breakdown,
    }

    return tuple(observations), summary


def build_b1_evidence_payload(
    summary: dict[str, Any],
    observations: Sequence[B1CaseObservation],
    descriptor: TrancheDescriptor,
    run_id: str,
    evaluated_at: datetime,
    probe_script_path: Path | None = None,
    git_head: str | None = None,
) -> dict[str, Any]:
    """Constrói o envelope de evidência segregado para a Sonda B1."""
    if probe_script_path is None:
        probe_script_path = Path(__file__).resolve()
    probe_sha = compute_canonical_lf_sha256(probe_script_path)

    metadata: dict[str, Any] = {
        "probe_identifier": "SR001-B1-PN-CONFLICT-PROBE",
        "probe_sha256": probe_sha,
        "catalog_sha256": descriptor.expected_catalog_sha256,
        "ground_truth_sha256": descriptor.expected_ground_truth_sha256,
        "manifest_sha256": descriptor.expected_manifest_sha256,
        "tranche_id": descriptor.tranche_id,
        "run_id": run_id,
        "evaluated_at": evaluated_at.isoformat(),
    }
    if git_head is not None:
        metadata["git_head"] = git_head

    scientific_payload = {
        "summary": _to_json_native(summary),
        "observations": [_to_json_native(o) for o in observations],
    }

    return {
        "metadata": metadata,
        "scientific_payload": scientific_payload,
    }


if __name__ == "__main__":
    print("SR-001 — Sonda Experimental B1 (PN Conflict Probe)")
    desc = get_tranche_02_descriptor()
    obs, sum_data = evaluate_tranche_b1(desc)
    print(f"B0 Unconditioned: {sum_data['b0_unconditioned_metrics']}")
    print(f"B1 Unconditioned: {sum_data['b1_unconditioned_metrics']}")
    print(f"Delta FP: {sum_data['comparative_metrics']['delta_fp']}")
    print(f"Delta Recall_P: {sum_data['comparative_metrics']['delta_recall_p']}")
    print(f"Decisões alteradas: {sum_data['comparative_metrics']['changed_decisions_count']}")
