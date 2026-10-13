"""SR-001 B2/FM-1: conservative typed dimensional-disagreement probe.

EXPERIMENT ONLY. No product changes, no data mutation, no composition with B1.
Unknown and no-disagreement are non-vetoes. Ground truth is used only in evaluation.
"""
from __future__ import annotations

import json
import re
from dataclasses import asdict
from enum import Enum
from pathlib import Path

from agent_lab.duplicates import is_possible_duplicate
from experiments.sr001_b1_pn_conflict_probe import (
    DetectorRoute, compute_confusion_metrics, detect_original_decision,
    get_tranche_02_descriptor,
)
from experiments.sr001_baseline_b_harness_v2 import (
    evaluate_candidate_selection, load_and_validate_tranche,
)


class DimensionalSignal(str, Enum):
    DISAGREEMENT = "DISAGREEMENT"
    NO_DISAGREEMENT = "NO_DISAGREEMENT"
    UNKNOWN = "UNKNOWN"


# A bounded, explicit grammar. These patterns are not a general dimensional parser.
# Source is description_short ONLY; PN, Ground Truth and IDs never enter the predicate.
# Each named key includes an attribute's physical role, avoiding comparisons of
# arbitrary numbers from distinct roles or unrelated industrial standards.
_GRAMMAR = (
    ("fastener_length_mm", re.compile(
        r"\bPARAFUSO\b.*?\bM\s*\d+\s*[X-]\s*(\d+)\b", re.I)),
    ("valve_nominal_inch", re.compile(
        r"\bVALVULA\b.*?\bDN\s*\d+\s+POL\b|\bVALVULA\b.*?\bDN\s*(\d+)\s*POL\b", re.I)),
    ("cable_section_mm2", re.compile(
        r"\bCABO\b.*?\bSECAO\s+(\d+)\s*MM\s*2\b", re.I)),
    ("belt_length_inch", re.compile(
        r"\bCORREIA\b.*?\bCOMPRIMENTO\s+(\d+)\s*POL\b", re.I)),
)

# Valve pattern deliberately handles plain 'DN 3 POL' only, without DN100 -> inch
# conversion. The explicit specialized matcher is simpler and unambiguous.
_VALVE_INCH = re.compile(r"\bDN\s+(\d+)\s+POL\b", re.I)


def extract_typed_dimension(record):
    """Return (physical_role, integer_value), or None for ambiguous/unsupported."""
    text = record.description_short.upper()
    # Avoid picking up numbers when a short description is truncation-prone.
    if text.startswith("VALVULA ") and "DN " in text:
        match = _VALVE_INCH.search(text)
        if match:
            return ("valve_nominal_inch", int(match.group(1)))
    for role, pattern in _GRAMMAR:
        if role == "valve_nominal_inch":
            continue
        match = pattern.search(text)
        if match:
            return (role, int(match.group(1)))
    return None


def dimensional_signal(record_a, record_b):
    a = extract_typed_dimension(record_a)
    b = extract_typed_dimension(record_b)
    if a is None or b is None or a[0] != b[0]:
        return DimensionalSignal.UNKNOWN, a, b
    return (DimensionalSignal.DISAGREEMENT if a[1] != b[1]
            else DimensionalSignal.NO_DISAGREEMENT), a, b


def evaluate_b2_pair(record_a, record_b):
    original, route = detect_original_decision(record_a, record_b)
    signal, typed_a, typed_b = dimensional_signal(record_a, record_b)
    intervened = bool(original and route == DetectorRoute.ROUTE_2
                      and signal == DimensionalSignal.DISAGREEMENT)
    return original, (False if intervened else original), route, signal, typed_a, typed_b


def evaluate_frozen_t02():
    descriptor = get_tranche_02_descriptor()
    catalog, truth, manifest = load_and_validate_tranche(descriptor)  # hash gate
    materials = {r.material_id: r for r in catalog}
    observations = []
    for gt in sorted(truth, key=lambda row: row.evaluation_case_id):
        a, b = materials[gt.material_id_a], materials[gt.material_id_b]
        original, proposed, route, signal, typed_a, typed_b = evaluate_b2_pair(a, b)
        # Independent pairwise B0 identity gate against production detector.
        if original != is_possible_duplicate(a, b):
            raise AssertionError("B0 detector divergence: " + gt.evaluation_case_id)
        selected = evaluate_candidate_selection(a, b).is_candidate
        observations.append({
            "case_id": gt.evaluation_case_id,
            "stratum": manifest[gt.evaluation_case_id]["stratum"],
            "family": manifest[gt.evaluation_case_id]["challenge_taxonomy_class"],
            "truth": gt.is_duplicate,
            "candidate": selected,
            "b0": original, "b2": proposed,
            "route": route.value, "signal": signal.value,
            "typed_a": typed_a, "typed_b": typed_b,
        })
    if len(observations) != 40:
        raise AssertionError("Wrong T02 pair count")
    b0 = compute_confusion_metrics([(o["truth"], o["b0"]) for o in observations])
    b2 = compute_confusion_metrics([(o["truth"], o["b2"]) for o in observations])
    if (b0.tp, b0.fp, b0.tn, b0.fn) != (19, 17, 3, 1):
        raise AssertionError("B0 aggregate gate mismatch")
    if sum(o["candidate"] for o in observations) != 39:
        raise AssertionError("Candidate Selection gate mismatch")
    if any(o["truth"] and o["b0"] and not o["b2"] for o in observations):
        raise AssertionError("SAFETY FAILED: a B0 TP was sacrificed")
    selected = [o for o in observations if o["candidate"]]
    return {
        "protocol": "SR001-B2-FM1-POSTHOC-T02",
        "source": "T02 FROZEN / descriptor hash validation",
        "counts": {"pairs": 40, "selected": len(selected)},
        "input_sha256": {
            "catalog": descriptor.expected_catalog_sha256,
            "ground_truth": descriptor.expected_ground_truth_sha256,
            "manifest": descriptor.expected_manifest_sha256,
        },
        "b0_unconditioned": asdict(b0),
        "b2_unconditioned": asdict(b2),
        "b0_conditioned": asdict(compute_confusion_metrics(
            [(o["truth"], o["b0"]) for o in selected])),
        "b2_conditioned": asdict(compute_confusion_metrics(
            [(o["truth"], o["b2"]) for o in selected])),
        "changed": [o for o in observations if o["b0"] != o["b2"]],
        "observations": observations,
        "safety_goal": "PASS" if b2.tp == 19 else "FAILED",
        "production_eligible": False,
        "interpretation": "POST-HOC only; not independent validation",
    }


if __name__ == "__main__":
    print(json.dumps(evaluate_frozen_t02(), ensure_ascii=False, indent=2))
