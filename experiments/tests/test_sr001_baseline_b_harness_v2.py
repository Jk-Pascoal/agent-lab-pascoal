"""Testes contratuais e unitários do Harness Experimental Baseline B v2 (SR-001).

Estes testes validam a instrumentação metrológica e integridade do harness
sem constituir execução experimental contra dados congelados.
"""

from __future__ import annotations

import unittest
from pathlib import Path

from experiments.sr001_baseline_b_harness_v2 import (
    CandidateSelectionDecision,
    CandidateSelectionOutcome,
    CaseObservationV2,
    DetectorOutcome,
    TrancheDescriptor,
)


class TestHarnessV2ContractsAndTyping(unittest.TestCase):
    """Fase 1: Contratos e Tipagem do Harness v2."""

    def test_candidate_selection_outcome_enum_values(self) -> None:
        self.assertEqual(CandidateSelectionOutcome.POSITIVE_RETAINED.value, "POSITIVE_RETAINED")
        self.assertEqual(CandidateSelectionOutcome.POSITIVE_DROPPED.value, "POSITIVE_DROPPED")
        self.assertEqual(CandidateSelectionOutcome.NEGATIVE_RETAINED.value, "NEGATIVE_RETAINED")
        self.assertEqual(CandidateSelectionOutcome.NEGATIVE_DROPPED.value, "NEGATIVE_DROPPED")
        self.assertEqual(len(CandidateSelectionOutcome), 4)

    def test_detector_outcome_enum_values(self) -> None:
        self.assertEqual(DetectorOutcome.TRUE_POSITIVE.value, "TP")
        self.assertEqual(DetectorOutcome.FALSE_POSITIVE.value, "FP")
        self.assertEqual(DetectorOutcome.TRUE_NEGATIVE.value, "TN")
        self.assertEqual(DetectorOutcome.FALSE_NEGATIVE.value, "FN")
        self.assertEqual(len(DetectorOutcome), 4)

    def test_candidate_selection_decision_immutability(self) -> None:
        decision = CandidateSelectionDecision(
            is_candidate=True,
            matched_families=("FAMILY_1", "FAMILY_2"),
            family_1_key=("PN123", "BOSCH"),
            family_2_key=("PARAFUSOS", "PARAFUSO"),
        )
        self.assertTrue(decision.is_candidate)
        self.assertEqual(decision.matched_families, ("FAMILY_1", "FAMILY_2"))
        self.assertEqual(decision.family_1_key, ("PN123", "BOSCH"))
        self.assertEqual(decision.family_2_key, ("PARAFUSOS", "PARAFUSO"))
        with self.assertRaises((AttributeError, TypeError)):
            decision.is_candidate = False  # type: ignore[misc]

    def test_case_observation_v2_structure_and_immutability(self) -> None:
        decision = CandidateSelectionDecision(
            is_candidate=True,
            matched_families=("FAMILY_1",),
            family_1_key=("PN1", "M1"),
            family_2_key=None,
        )
        obs = CaseObservationV2(
            evaluation_case_id="CASE-001",
            stratum="FASTENERS",
            challenge_class="P-ABBR",
            material_id_a="MAT-A",
            material_id_b="MAT-B",
            ground_truth_is_duplicate=True,
            selection_decision=decision,
            selection_outcome=CandidateSelectionOutcome.POSITIVE_RETAINED,
            unconditioned_detector_prediction=True,
            unconditioned_detector_outcome=DetectorOutcome.TRUE_POSITIVE,
            conditioned_detector_prediction=True,
            conditioned_detector_outcome=DetectorOutcome.TRUE_POSITIVE,
        )
        self.assertEqual(obs.evaluation_case_id, "CASE-001")
        self.assertEqual(obs.selection_outcome, CandidateSelectionOutcome.POSITIVE_RETAINED)
        self.assertEqual(obs.unconditioned_detector_outcome, DetectorOutcome.TRUE_POSITIVE)
        self.assertEqual(obs.conditioned_detector_outcome, DetectorOutcome.TRUE_POSITIVE)
        with self.assertRaises((AttributeError, TypeError)):
            obs.evaluation_case_id = "MUTATED"  # type: ignore[misc]

    def test_case_observation_v2_supports_dropped_candidate_none_condition(self) -> None:
        decision = CandidateSelectionDecision(
            is_candidate=False,
            matched_families=(),
            family_1_key=None,
            family_2_key=None,
        )
        obs = CaseObservationV2(
            evaluation_case_id="CASE-002",
            stratum="GENERAL",
            challenge_class="HN-UNT",
            material_id_a="MAT-C",
            material_id_b="MAT-D",
            ground_truth_is_duplicate=False,
            selection_decision=decision,
            selection_outcome=CandidateSelectionOutcome.NEGATIVE_DROPPED,
            unconditioned_detector_prediction=False,
            unconditioned_detector_outcome=DetectorOutcome.TRUE_NEGATIVE,
            conditioned_detector_prediction=None,
            conditioned_detector_outcome=None,
        )
        self.assertIsNone(obs.conditioned_detector_prediction)
        self.assertIsNone(obs.conditioned_detector_outcome)
        self.assertEqual(obs.selection_outcome, CandidateSelectionOutcome.NEGATIVE_DROPPED)

    def test_tranche_descriptor_structure_and_immutability(self) -> None:
        desc = TrancheDescriptor(
            tranche_id="01",
            catalog_path=Path("cat.csv"),
            ground_truth_path=Path("gt.json"),
            manifest_path=Path("manifest.json"),
            expected_catalog_sha256="cat_sha",
            expected_ground_truth_sha256="gt_sha",
            expected_manifest_sha256="mf_sha",
            expected_material_count=20,
            expected_pair_count=10,
        )
        self.assertEqual(desc.tranche_id, "01")
        self.assertEqual(desc.expected_material_count, 20)
        self.assertEqual(desc.expected_pair_count, 10)
        with self.assertRaises((AttributeError, TypeError)):
            desc.tranche_id = "02"  # type: ignore[misc]


class TestHarnessV2CandidateSelection(unittest.TestCase):
    """Fase 2: Candidate Selection (Famílias 1 e 2)."""

    def _make_record(
        self,
        material_id: str,
        pn: str = "",
        mfg: str = "",
        group: str = "",
        short_desc: str = "",
        long_desc: str = "",
    ):
        from agent_lab.domain import MaterialRecord
        return MaterialRecord(
            material_id=material_id,
            description_short=short_desc,
            long_description=long_desc,
            material_group=group,
            unit="UN",
            manufacturer=mfg,
            manufacturer_part_number=pn,
        )

    def test_extract_candidate_family_keys_complete(self) -> None:
        from experiments.sr001_baseline_b_harness_v2 import extract_candidate_family_keys
        rec = self._make_record(
            material_id="M1",
            pn="ABC-123",
            mfg="Siemens",
            group="ELETRICA",
            short_desc="DISJUNTOR BIPOLAR 20A",
            long_desc="DISJUNTOR TERMOMAGNETICO",
        )
        p1, p2 = extract_candidate_family_keys(rec)
        self.assertEqual(p1, ("ABC 123", "SIEMENS"))
        self.assertEqual(p2, ("ELETRICA", "DISJUNTOR"))

    def test_extract_candidate_family_keys_missing_fields_returns_none(self) -> None:
        from experiments.sr001_baseline_b_harness_v2 import extract_candidate_family_keys
        # Sem PN -> Family 1 é None
        rec_no_pn = self._make_record(
            material_id="M2",
            pn="",
            mfg="Siemens",
            group="ELETRICA",
            short_desc="DISJUNTOR 20A",
        )
        p1, p2 = extract_candidate_family_keys(rec_no_pn)
        self.assertIsNone(p1)
        self.assertEqual(p2, ("ELETRICA", "DISJUNTOR"))

        # Sem fabricante -> Family 1 é None
        rec_no_mfg = self._make_record(
            material_id="M3",
            pn="ABC-123",
            mfg="",
            group="ELETRICA",
            short_desc="DISJUNTOR 20A",
        )
        p1, p2 = extract_candidate_family_keys(rec_no_mfg)
        self.assertIsNone(p1)

        # Sem category token na descrição -> Family 2 é None
        rec_no_token = self._make_record(
            material_id="M4",
            pn="ABC-123",
            mfg="Siemens",
            group="ELETRICA",
            short_desc="",
            long_desc="",
        )
        p1, p2 = extract_candidate_family_keys(rec_no_token)
        self.assertEqual(p1, ("ABC 123", "SIEMENS"))
        self.assertIsNone(p2)

    def test_evaluate_candidate_selection_family_1_only(self) -> None:
        from experiments.sr001_baseline_b_harness_v2 import evaluate_candidate_selection
        rec_a = self._make_record("MA", pn="SKF-6204", mfg="SKF", group="GRP1", short_desc="ROLAMENTO A")
        rec_b = self._make_record("MB", pn="skf 6204", mfg="skf", group="GRP2", short_desc="PARAFUSO B")
        dec = evaluate_candidate_selection(rec_a, rec_b)
        self.assertTrue(dec.is_candidate)
        self.assertEqual(dec.matched_families, ("FAMILY_1",))
        self.assertEqual(dec.family_1_key, ("SKF 6204", "SKF"))
        self.assertIsNone(dec.family_2_key)

    def test_evaluate_candidate_selection_family_2_only(self) -> None:
        from experiments.sr001_baseline_b_harness_v2 import evaluate_candidate_selection
        rec_a = self._make_record("MA", pn="PN-1", mfg="MFG-1", group="FIXADORES", short_desc="PARAFUSO SEXTAVADO")
        rec_b = self._make_record("MB", pn="PN-2", mfg="MFG-2", group="fixadores", short_desc="parafuso frances")
        dec = evaluate_candidate_selection(rec_a, rec_b)
        self.assertTrue(dec.is_candidate)
        self.assertEqual(dec.matched_families, ("FAMILY_2",))
        self.assertIsNone(dec.family_1_key)
        self.assertEqual(dec.family_2_key, ("FIXADORES", "PARAFUSO"))

    def test_evaluate_candidate_selection_both_families(self) -> None:
        from experiments.sr001_baseline_b_harness_v2 import evaluate_candidate_selection
        rec_a = self._make_record("MA", pn="6204", mfg="SKF", group="ROLAMENTOS", short_desc="ROLAMENTO RADIAL")
        rec_b = self._make_record("MB", pn="6204", mfg="SKF", group="ROLAMENTOS", short_desc="ROLAMENTO ESFERAS")
        dec = evaluate_candidate_selection(rec_a, rec_b)
        self.assertTrue(dec.is_candidate)
        self.assertEqual(dec.matched_families, ("FAMILY_1", "FAMILY_2"))
        self.assertEqual(dec.family_1_key, ("6204", "SKF"))
        self.assertEqual(dec.family_2_key, ("ROLAMENTOS", "ROLAMENTO"))

    def test_evaluate_candidate_selection_neither_family(self) -> None:
        from experiments.sr001_baseline_b_harness_v2 import evaluate_candidate_selection, is_candidate_pair
        rec_a = self._make_record("MA", pn="PNA", mfg="MFGA", group="G1", short_desc="PARAFUSO A")
        rec_b = self._make_record("MB", pn="PNB", mfg="MFGB", group="G2", short_desc="VALVULA B")
        dec = evaluate_candidate_selection(rec_a, rec_b)
        self.assertFalse(dec.is_candidate)
        self.assertEqual(dec.matched_families, ())
        self.assertIsNone(dec.family_1_key)
        self.assertIsNone(dec.family_2_key)
        self.assertFalse(is_candidate_pair(rec_a, rec_b))


class TestHarnessV2SegregatedMetrology(unittest.TestCase):
    """Fase 3: Metrologia Segregada (Blocos 1, 2, 3 e 4)."""

    def test_classify_candidate_selection_outcome_four_quadrants(self) -> None:
        from experiments.sr001_baseline_b_harness_v2 import (
            CandidateSelectionOutcome,
            classify_candidate_selection_outcome,
        )
        self.assertEqual(
            classify_candidate_selection_outcome(is_duplicate=True, is_candidate=True),
            CandidateSelectionOutcome.POSITIVE_RETAINED,
        )
        self.assertEqual(
            classify_candidate_selection_outcome(is_duplicate=True, is_candidate=False),
            CandidateSelectionOutcome.POSITIVE_DROPPED,
        )
        self.assertEqual(
            classify_candidate_selection_outcome(is_duplicate=False, is_candidate=True),
            CandidateSelectionOutcome.NEGATIVE_RETAINED,
        )
        self.assertEqual(
            classify_candidate_selection_outcome(is_duplicate=False, is_candidate=False),
            CandidateSelectionOutcome.NEGATIVE_DROPPED,
        )

    def test_classify_detector_outcome_four_quadrants(self) -> None:
        from experiments.sr001_baseline_b_harness_v2 import (
            DetectorOutcome,
            classify_detector_outcome,
        )
        self.assertEqual(
            classify_detector_outcome(is_duplicate=True, is_possible_duplicate=True),
            DetectorOutcome.TRUE_POSITIVE,
        )
        self.assertEqual(
            classify_detector_outcome(is_duplicate=False, is_possible_duplicate=True),
            DetectorOutcome.FALSE_POSITIVE,
        )
        self.assertEqual(
            classify_detector_outcome(is_duplicate=False, is_possible_duplicate=False),
            DetectorOutcome.TRUE_NEGATIVE,
        )
        self.assertEqual(
            classify_detector_outcome(is_duplicate=True, is_possible_duplicate=False),
            DetectorOutcome.FALSE_NEGATIVE,
        )

    def _make_dummy_obs(
        self,
        case_id: str,
        gt_dup: bool,
        is_cand: bool,
        det_pred: bool,
    ):
        from experiments.sr001_baseline_b_harness_v2 import (
            CandidateSelectionDecision,
            CaseObservationV2,
            classify_candidate_selection_outcome,
            classify_detector_outcome,
        )
        dec = CandidateSelectionDecision(
            is_candidate=is_cand,
            matched_families=("FAMILY_1",) if is_cand else (),
            family_1_key=("P", "M") if is_cand else None,
            family_2_key=None,
        )
        sel_outcome = classify_candidate_selection_outcome(gt_dup, is_cand)
        uncond_outcome = classify_detector_outcome(gt_dup, det_pred)
        cond_pred = det_pred if is_cand else None
        cond_outcome = classify_detector_outcome(gt_dup, cond_pred) if is_cand else None

        return CaseObservationV2(
            evaluation_case_id=case_id,
            stratum="TEST",
            challenge_class="C-TEST",
            material_id_a="A",
            material_id_b="B",
            ground_truth_is_duplicate=gt_dup,
            selection_decision=dec,
            selection_outcome=sel_outcome,
            unconditioned_detector_prediction=det_pred,
            unconditioned_detector_outcome=uncond_outcome,
            conditioned_detector_prediction=cond_pred,
            conditioned_detector_outcome=cond_outcome,
        )

    def test_compute_candidate_selection_metrics(self) -> None:
        from experiments.sr001_baseline_b_harness_v2 import compute_candidate_selection_metrics
        # 2 positivos: 1 retido, 1 descartado -> recall = 0.5, miss_rate = 0.5
        # 2 negativos: 1 retido, 1 descartado
        # Total: 4 pares, 2 retidos -> retention_rate = 0.5, reduction_ratio = 0.5
        obs = [
            self._make_dummy_obs("C1", gt_dup=True, is_cand=True, det_pred=True),
            self._make_dummy_obs("C2", gt_dup=True, is_cand=False, det_pred=False),
            self._make_dummy_obs("C3", gt_dup=False, is_cand=True, det_pred=True),
            self._make_dummy_obs("C4", gt_dup=False, is_cand=False, det_pred=False),
        ]
        metrics = compute_candidate_selection_metrics(obs)
        self.assertEqual(metrics.positive_count, 2)
        self.assertEqual(metrics.positive_retained, 1)
        self.assertEqual(metrics.positive_dropped, 1)
        self.assertEqual(metrics.negative_retained, 1)
        self.assertEqual(metrics.negative_dropped, 1)
        self.assertAlmostEqual(metrics.candidate_pair_recall, 0.5)
        self.assertAlmostEqual(metrics.candidate_pair_miss_rate, 0.5)
        self.assertEqual(metrics.challenge_total_pairs, 4)
        self.assertEqual(metrics.challenge_retained_pairs, 2)
        self.assertAlmostEqual(metrics.challenge_retention_rate, 0.5)
        self.assertAlmostEqual(metrics.challenge_reduction_ratio, 0.5)

    def test_compute_unconditioned_and_conditioned_detector_metrics(self) -> None:
        from experiments.sr001_baseline_b_harness_v2 import (
            compute_conditioned_detector_metrics,
            compute_unconditioned_detector_metrics,
        )
        # 10 casos idênticos à distribuição da Observation #1:
        # 5 positivos retidos pelo blocking e detectados (TP=5)
        # 4 hard negatives retidos pelo blocking e detectados (FP=4)
        # 1 hard negative descartado pelo blocking e não detectado (TN=1 incondicional)
        obs = [
            # 5 Positivos retidos e detectados
            self._make_dummy_obs(f"P{i}", gt_dup=True, is_cand=True, det_pred=True) for i in range(5)
        ] + [
            # 4 HN retidos e detectados como duplicata (FP)
            self._make_dummy_obs(f"HN_FP_{i}", gt_dup=False, is_cand=True, det_pred=True) for i in range(4)
        ] + [
            # 1 HN descartado pelo blocking e rejeitado pelo detector (TN)
            self._make_dummy_obs("HN_UNT", gt_dup=False, is_cand=False, det_pred=False)
        ]

        # Bloco 2: Detector Incondicional (todos os 10 pares)
        uncond = compute_unconditioned_detector_metrics(obs)
        self.assertEqual(uncond.tp, 5)
        self.assertEqual(uncond.fp, 4)
        self.assertEqual(uncond.tn, 1)
        self.assertEqual(uncond.fn, 0)
        self.assertAlmostEqual(uncond.precision, 5 / 9)
        self.assertAlmostEqual(uncond.recall, 1.0)
        self.assertAlmostEqual(uncond.f1, 2 * (5 / 9) * 1.0 / ((5 / 9) + 1.0))

        # Bloco 3: Detector Condicionado (somente os 9 pares com is_candidate == True)
        cond = compute_conditioned_detector_metrics(obs)
        self.assertEqual(cond.evaluated_pairs_count, 9)
        self.assertEqual(cond.tp, 5)
        self.assertEqual(cond.fp, 4)
        self.assertEqual(cond.tn, 0)  # O par TN foi podado no blocking!
        self.assertEqual(cond.fn, 0)
        self.assertAlmostEqual(cond.precision, 5 / 9)
        self.assertAlmostEqual(cond.recall, 1.0)

    def test_compute_end_to_end_pipeline_metrics(self) -> None:
        from experiments.sr001_baseline_b_harness_v2 import (
            compute_candidate_selection_metrics,
            compute_conditioned_detector_metrics,
            compute_end_to_end_metrics,
        )
        obs = [
            # 1 positivo descartado pelo blocking (POSITIVE_DROPPED)
            self._make_dummy_obs("P0", gt_dup=True, is_cand=False, det_pred=True),
            # 1 positivo retido pelo blocking e detectado pelo detector (TP)
            self._make_dummy_obs("P1", gt_dup=True, is_cand=True, det_pred=True),
            # 1 negativo retido pelo blocking e rejeitado pelo detector (TN)
            self._make_dummy_obs("N1", gt_dup=False, is_cand=True, det_pred=False),
            # 1 negativo descartado pelo blocking
            self._make_dummy_obs("N2", gt_dup=False, is_cand=False, det_pred=False),
        ]
        sel_metrics = compute_candidate_selection_metrics(obs)
        cond_metrics = compute_conditioned_detector_metrics(obs)
        e2e = compute_end_to_end_metrics(sel_metrics, cond_metrics)

        # Recall_block = 1/2 = 0.5
        # Recall_det|cand = 1/1 = 1.0
        # Overall Pipeline Recall = 0.5 * 1.0 = 0.5
        # Reduction Ratio = 2/4 descartados = 0.5
        self.assertAlmostEqual(e2e.recall_block, 0.5)
        self.assertAlmostEqual(e2e.recall_detector_conditioned, 1.0)
        self.assertAlmostEqual(e2e.overall_pipeline_recall, 0.5)
        self.assertAlmostEqual(e2e.challenge_reduction_ratio, 0.5)
        self.assertEqual(e2e.bidimensional_point, (0.5, 0.5))


class TestHarnessV2Integrity(unittest.TestCase):
    """Fase 4: Validação de Hashes, Integridade e Ingestão Paramétrica."""

    def test_canonical_lf_sha256_normalizes_crlf_and_lf(self) -> None:
        import tempfile
        from experiments.sr001_baseline_b_harness_v2 import compute_canonical_lf_sha256

        with tempfile.TemporaryDirectory() as tmpdir:
            p_lf = Path(tmpdir) / "test_lf.txt"
            p_crlf = Path(tmpdir) / "test_crlf.txt"

            p_lf.write_bytes(b"LINE 1\nLINE 2\n")
            p_crlf.write_bytes(b"LINE 1\r\nLINE 2\r\n")

            sha_lf = compute_canonical_lf_sha256(p_lf)
            sha_crlf = compute_canonical_lf_sha256(p_crlf)

            self.assertEqual(sha_lf, sha_crlf)

    def _create_minimal_tranche_files(
        self,
        tmpdir: Path,
        status: str = "DRAFT",
        freeze_state: str = "FROZEN",
        omit_material_from_catalog: bool = False,
    ):
        import hashlib
        import json

        # Catalog
        cat_file = tmpdir / "catalog.csv"
        if omit_material_from_catalog:
            cat_content = "material_id,description_short,long_description,material_group,unit,manufacturer,manufacturer_part_number,status\nM1,DESC1,LONG1,G1,UN,M1,PN1,ACTIVE\n"
        else:
            cat_content = (
                "material_id,description_short,long_description,material_group,unit,manufacturer,manufacturer_part_number,status\n"
                "M1,DESC1,LONG1,G1,UN,M1,PN1,ACTIVE\n"
                "M2,DESC2,LONG2,G1,UN,M2,PN2,ACTIVE\n"
            )
        cat_bytes = cat_content.encode("utf-8")
        cat_file.write_bytes(cat_bytes)
        cat_sha = hashlib.sha256(cat_bytes.replace(b"\r\n", b"\n")).hexdigest()

        # GT
        gt_file = tmpdir / "ground_truth.json"
        gt_data = [
            {
                "schema_version": 1,
                "record_type": "DUPLICATE_PAIR_GROUND_TRUTH",
                "ground_truth_id": "GT-1",
                "evaluation_case_id": "CASE-1",
                "material_id_a": "M1",
                "material_id_b": "M2",
                "is_duplicate": True,
                "provenance": "SYNTHETIC_SPECIFIED",
                "source_reference": "SPEC-0158 / P-ABBR",
                "annotator": None,
                "labeled_at": "2026-09-30T10:00:00+00:00",
                "rationale": "Test pair",
            }
        ]
        gt_bytes = json.dumps(gt_data, indent=2).encode("utf-8")
        gt_file.write_bytes(gt_bytes)
        gt_sha = hashlib.sha256(gt_bytes.replace(b"\r\n", b"\n")).hexdigest()

        # Manifest
        mf_file = tmpdir / "manifest.json"
        mf_data = {
            "control_metadata": {
                "status": status,
                "freeze_state": freeze_state,
                "evaluation_state": "NOT_YET_EVALUATED",
                "freeze_sha256": gt_sha,
            },
            "cases": [
                {
                    "evaluation_case_id": "CASE-1",
                    "stratum": "FASTENERS",
                    "challenge_taxonomy_class": "P-ABBR",
                }
            ],
        }
        mf_bytes = json.dumps(mf_data, indent=2).encode("utf-8")
        mf_file.write_bytes(mf_bytes)
        mf_sha = hashlib.sha256(mf_bytes.replace(b"\r\n", b"\n")).hexdigest()

        return cat_file, gt_file, mf_file, cat_sha, gt_sha, mf_sha

    def test_load_and_validate_tranche_success(self) -> None:
        import tempfile
        from experiments.sr001_baseline_b_harness_v2 import (
            TrancheDescriptor,
            load_and_validate_tranche,
        )

        with tempfile.TemporaryDirectory() as tmpdir_s:
            tmpdir = Path(tmpdir_s)
            cat_f, gt_f, mf_f, cat_sha, gt_sha, mf_sha = self._create_minimal_tranche_files(tmpdir)
            desc = TrancheDescriptor(
                tranche_id="test",
                catalog_path=cat_f,
                ground_truth_path=gt_f,
                manifest_path=mf_f,
                expected_catalog_sha256=cat_sha,
                expected_ground_truth_sha256=gt_sha,
                expected_manifest_sha256=mf_sha,
                expected_material_count=2,
                expected_pair_count=1,
            )
            records, gt_pairs, manifest_cases = load_and_validate_tranche(desc)
            self.assertEqual(len(records), 2)
            self.assertEqual(len(gt_pairs), 1)
            self.assertEqual(len(manifest_cases), 1)

    def test_load_and_validate_tranche_rejects_hash_mismatch(self) -> None:
        import tempfile
        from experiments.sr001_baseline_b_harness_v2 import (
            TrancheDescriptor,
            load_and_validate_tranche,
        )

        with tempfile.TemporaryDirectory() as tmpdir_s:
            tmpdir = Path(tmpdir_s)
            cat_f, gt_f, mf_f, cat_sha, gt_sha, mf_sha = self._create_minimal_tranche_files(tmpdir)
            desc = TrancheDescriptor(
                tranche_id="test",
                catalog_path=cat_f,
                ground_truth_path=gt_f,
                manifest_path=mf_f,
                expected_catalog_sha256="wrong_sha",
                expected_ground_truth_sha256=gt_sha,
                expected_manifest_sha256=mf_sha,
                expected_material_count=2,
                expected_pair_count=1,
            )
            with self.assertRaises(AssertionError):
                load_and_validate_tranche(desc)

    def test_load_and_validate_tranche_rejects_non_frozen_manifest(self) -> None:
        import tempfile
        from experiments.sr001_baseline_b_harness_v2 import (
            TrancheDescriptor,
            load_and_validate_tranche,
        )

        with tempfile.TemporaryDirectory() as tmpdir_s:
            tmpdir = Path(tmpdir_s)
            cat_f, gt_f, mf_f, cat_sha, gt_sha, mf_sha = self._create_minimal_tranche_files(
                tmpdir, freeze_state="UNFROZEN"
            )
            desc = TrancheDescriptor(
                tranche_id="test",
                catalog_path=cat_f,
                ground_truth_path=gt_f,
                manifest_path=mf_f,
                expected_catalog_sha256=cat_sha,
                expected_ground_truth_sha256=gt_sha,
                expected_manifest_sha256=mf_sha,
                expected_material_count=2,
                expected_pair_count=1,
            )
            with self.assertRaises(AssertionError):
                load_and_validate_tranche(desc)

    def test_load_and_validate_tranche_rejects_orphan_material(self) -> None:
        import tempfile
        from experiments.sr001_baseline_b_harness_v2 import (
            TrancheDescriptor,
            load_and_validate_tranche,
        )

        with tempfile.TemporaryDirectory() as tmpdir_s:
            tmpdir = Path(tmpdir_s)
            # M2 está no GT mas ausente no catálogo
            cat_f, gt_f, mf_f, cat_sha, gt_sha, mf_sha = self._create_minimal_tranche_files(
                tmpdir, omit_material_from_catalog=True
            )
            desc = TrancheDescriptor(
                tranche_id="test",
                catalog_path=cat_f,
                ground_truth_path=gt_f,
                manifest_path=mf_f,
                expected_catalog_sha256=cat_sha,
                expected_ground_truth_sha256=gt_sha,
                expected_manifest_sha256=mf_sha,
                expected_material_count=1,
                expected_pair_count=1,
            )
            with self.assertRaises(AssertionError):
                load_and_validate_tranche(desc)

    def test_load_and_validate_tranche_rejects_non_draft_status(self) -> None:
        import tempfile
        from experiments.sr001_baseline_b_harness_v2 import (
            TrancheDescriptor,
            load_and_validate_tranche,
        )

        with tempfile.TemporaryDirectory() as tmpdir_s:
            tmpdir = Path(tmpdir_s)
            cat_f, gt_f, mf_f, cat_sha, gt_sha, mf_sha = self._create_minimal_tranche_files(
                tmpdir, status="APPROVED"
            )
            desc = TrancheDescriptor(
                tranche_id="test",
                catalog_path=cat_f,
                ground_truth_path=gt_f,
                manifest_path=mf_f,
                expected_catalog_sha256=cat_sha,
                expected_ground_truth_sha256=gt_sha,
                expected_manifest_sha256=mf_sha,
                expected_material_count=2,
                expected_pair_count=1,
            )
            with self.assertRaises(AssertionError):
                load_and_validate_tranche(desc)

    def test_load_and_validate_tranche_rejects_duplicate_manifest_case_id(self) -> None:
        import hashlib
        import json
        import tempfile
        from experiments.sr001_baseline_b_harness_v2 import (
            TrancheDescriptor,
            load_and_validate_tranche,
        )

        with tempfile.TemporaryDirectory() as tmpdir_s:
            tmpdir = Path(tmpdir_s)
            cat_f, gt_f, mf_f, cat_sha, gt_sha, _ = self._create_minimal_tranche_files(tmpdir)
            mf_data = {
                "control_metadata": {
                    "status": "DRAFT",
                    "freeze_state": "FROZEN",
                    "evaluation_state": "NOT_YET_EVALUATED",
                    "freeze_sha256": gt_sha,
                },
                "cases": [
                    {
                        "evaluation_case_id": "CASE-1",
                        "stratum": "FASTENERS",
                        "challenge_taxonomy_class": "P-ABBR",
                    },
                    {
                        "evaluation_case_id": "CASE-1",
                        "stratum": "FASTENERS",
                        "challenge_taxonomy_class": "P-ABBR",
                    },
                ],
            }
            mf_bytes = json.dumps(mf_data, indent=2).encode("utf-8")
            mf_f.write_bytes(mf_bytes)
            mf_sha = hashlib.sha256(mf_bytes.replace(b"\r\n", b"\n")).hexdigest()

            desc = TrancheDescriptor(
                tranche_id="test",
                catalog_path=cat_f,
                ground_truth_path=gt_f,
                manifest_path=mf_f,
                expected_catalog_sha256=cat_sha,
                expected_ground_truth_sha256=gt_sha,
                expected_manifest_sha256=mf_sha,
                expected_material_count=2,
                expected_pair_count=2,
            )
            with self.assertRaises(AssertionError) as ctx:
                load_and_validate_tranche(desc)
            self.assertIn("Duplicidade de evaluation_case_id", str(ctx.exception))

    def test_load_and_validate_tranche_rejects_gt_manifest_case_set_mismatch(self) -> None:
        import hashlib
        import json
        import tempfile
        from experiments.sr001_baseline_b_harness_v2 import (
            TrancheDescriptor,
            load_and_validate_tranche,
        )

        with tempfile.TemporaryDirectory() as tmpdir_s:
            tmpdir = Path(tmpdir_s)
            # Catálogo com 3 materiais para permitir 2 pares válidos
            cat_file = tmpdir / "catalog.csv"
            cat_content = (
                "material_id,description_short,long_description,material_group,unit,manufacturer,manufacturer_part_number,status\n"
                "M1,DESC1,LONG1,G1,UN,M1,PN1,ACTIVE\n"
                "M2,DESC2,LONG2,G1,UN,M2,PN2,ACTIVE\n"
                "M3,DESC3,LONG3,G1,UN,M3,PN3,ACTIVE\n"
            )
            cat_bytes = cat_content.encode("utf-8")
            cat_file.write_bytes(cat_bytes)
            cat_sha = hashlib.sha256(cat_bytes.replace(b"\r\n", b"\n")).hexdigest()

            # GT com exatamente 2 casos: CASE-1 e CASE-GT-ONLY
            gt_file = tmpdir / "ground_truth.json"
            gt_data = [
                {
                    "schema_version": 1,
                    "record_type": "DUPLICATE_PAIR_GROUND_TRUTH",
                    "ground_truth_id": "GT-1",
                    "evaluation_case_id": "CASE-1",
                    "material_id_a": "M1",
                    "material_id_b": "M2",
                    "is_duplicate": True,
                    "provenance": "SYNTHETIC_SPECIFIED",
                    "source_reference": "SPEC-0158 / P-ABBR",
                    "annotator": None,
                    "labeled_at": "2026-09-30T10:00:00+00:00",
                    "rationale": "Pair 1",
                },
                {
                    "schema_version": 1,
                    "record_type": "DUPLICATE_PAIR_GROUND_TRUTH",
                    "ground_truth_id": "GT-2",
                    "evaluation_case_id": "CASE-GT-ONLY",
                    "material_id_a": "M2",
                    "material_id_b": "M3",
                    "is_duplicate": False,
                    "provenance": "SYNTHETIC_SPECIFIED",
                    "source_reference": "SPEC-0158 / HN-DIM",
                    "annotator": None,
                    "labeled_at": "2026-09-30T10:00:00+00:00",
                    "rationale": "Pair 2",
                },
            ]
            gt_bytes = json.dumps(gt_data, indent=2).encode("utf-8")
            gt_file.write_bytes(gt_bytes)
            gt_sha = hashlib.sha256(gt_bytes.replace(b"\r\n", b"\n")).hexdigest()

            # Manifesto com exatamente 2 casos: CASE-1 e CASE-MANIFEST-ONLY
            # (mesma cardinalidade 2, unicidade válida em ambos, mas conjuntos divergem)
            mf_file = tmpdir / "manifest.json"
            mf_data = {
                "control_metadata": {
                    "status": "DRAFT",
                    "freeze_state": "FROZEN",
                    "evaluation_state": "NOT_YET_EVALUATED",
                    "freeze_sha256": gt_sha,
                },
                "cases": [
                    {
                        "evaluation_case_id": "CASE-1",
                        "stratum": "FASTENERS",
                        "challenge_taxonomy_class": "P-ABBR",
                    },
                    {
                        "evaluation_case_id": "CASE-MANIFEST-ONLY",
                        "stratum": "FASTENERS",
                        "challenge_taxonomy_class": "P-ABBR",
                    },
                ],
            }
            mf_bytes = json.dumps(mf_data, indent=2).encode("utf-8")
            mf_file.write_bytes(mf_bytes)
            mf_sha = hashlib.sha256(mf_bytes.replace(b"\r\n", b"\n")).hexdigest()

            desc = TrancheDescriptor(
                tranche_id="test",
                catalog_path=cat_file,
                ground_truth_path=gt_file,
                manifest_path=mf_file,
                expected_catalog_sha256=cat_sha,
                expected_ground_truth_sha256=gt_sha,
                expected_manifest_sha256=mf_sha,
                expected_material_count=3,
                expected_pair_count=2,
            )
            with self.assertRaises(AssertionError):
                load_and_validate_tranche(desc)


class TestHarnessV2OrchestrationAndDeterminism(unittest.TestCase):
    """Fase 5: Orquestração e Determinismo do Scientific Payload."""

    def _create_synthetic_tranche(self, tmpdir: Path):
        import hashlib
        import json

        cat_file = tmpdir / "catalog.csv"
        # 3 materiais: M1 e M2 compartilham PN e fabricante (positivo retido e detectado)
        # M3 não compartilha nada com M1 (negativo)
        cat_content = (
            "material_id,description_short,long_description,material_group,unit,manufacturer,manufacturer_part_number,status\n"
            "M1,PARAFUSO SEXTAVADO M10X30,PARAFUSO ACO 8.8,FIXADORES,UN,FAB1,PN-100,ACTIVE\n"
            "M2,PARAFUSO SEXTAVADO M10X30,PARAFUSO ACO 8.8,FIXADORES,UN,FAB1,PN-100,ACTIVE\n"
            "M3,VALVULA GAVETA 2POL,VALVULA ESFERA,VALVULAS,UN,FAB2,PN-200,ACTIVE\n"
        )
        cat_bytes = cat_content.encode("utf-8")
        cat_file.write_bytes(cat_bytes)
        cat_sha = hashlib.sha256(cat_bytes.replace(b"\r\n", b"\n")).hexdigest()

        gt_file = tmpdir / "ground_truth.json"
        gt_data = [
            {
                "schema_version": 1,
                "record_type": "DUPLICATE_PAIR_GROUND_TRUTH",
                "ground_truth_id": "GT-1",
                "evaluation_case_id": "CASE-1",
                "material_id_a": "M1",
                "material_id_b": "M2",
                "is_duplicate": True,
                "provenance": "SYNTHETIC_SPECIFIED",
                "source_reference": "SPEC-0158 / P-ABBR",
                "annotator": None,
                "labeled_at": "2026-09-30T10:00:00+00:00",
                "rationale": "True duplicate",
            },
            {
                "schema_version": 1,
                "record_type": "DUPLICATE_PAIR_GROUND_TRUTH",
                "ground_truth_id": "GT-2",
                "evaluation_case_id": "CASE-2",
                "material_id_a": "M1",
                "material_id_b": "M3",
                "is_duplicate": False,
                "provenance": "SYNTHETIC_SPECIFIED",
                "source_reference": "SPEC-0158 / HN-UNT",
                "annotator": None,
                "labeled_at": "2026-09-30T10:00:00+00:00",
                "rationale": "Hard negative",
            },
        ]
        gt_bytes = json.dumps(gt_data, indent=2).encode("utf-8")
        gt_file.write_bytes(gt_bytes)
        gt_sha = hashlib.sha256(gt_bytes.replace(b"\r\n", b"\n")).hexdigest()

        mf_file = tmpdir / "manifest.json"
        mf_data = {
            "control_metadata": {
                "status": "DRAFT",
                "freeze_state": "FROZEN",
                "evaluation_state": "NOT_YET_EVALUATED",
                "freeze_sha256": gt_sha,
            },
            "cases": [
                {
                    "evaluation_case_id": "CASE-1",
                    "stratum": "FASTENERS",
                    "challenge_taxonomy_class": "P-ABBR",
                },
                {
                    "evaluation_case_id": "CASE-2",
                    "stratum": "GENERAL",
                    "challenge_taxonomy_class": "HN-UNT",
                },
            ],
        }
        mf_bytes = json.dumps(mf_data, indent=2).encode("utf-8")
        mf_file.write_bytes(mf_bytes)
        mf_sha = hashlib.sha256(mf_bytes.replace(b"\r\n", b"\n")).hexdigest()

        from experiments.sr001_baseline_b_harness_v2 import TrancheDescriptor

        return TrancheDescriptor(
            tranche_id="synthetic",
            catalog_path=cat_file,
            ground_truth_path=gt_file,
            manifest_path=mf_file,
            expected_catalog_sha256=cat_sha,
            expected_ground_truth_sha256=gt_sha,
            expected_manifest_sha256=mf_sha,
            expected_material_count=3,
            expected_pair_count=2,
        )

    def test_evaluate_tranche_produces_consistent_results(self) -> None:
        import tempfile
        from experiments.sr001_baseline_b_harness_v2 import (
            CandidateSelectionOutcome,
            DetectorOutcome,
            evaluate_tranche,
        )

        with tempfile.TemporaryDirectory() as tmpdir_s:
            desc = self._create_synthetic_tranche(Path(tmpdir_s))
            observations, summary = evaluate_tranche(desc)

            self.assertEqual(len(observations), 2)
            # Caso 1 (Positivo retido e detectado):
            obs1 = observations[0]
            self.assertEqual(obs1.evaluation_case_id, "CASE-1")
            self.assertEqual(obs1.selection_outcome, CandidateSelectionOutcome.POSITIVE_RETAINED)
            self.assertEqual(obs1.unconditioned_detector_outcome, DetectorOutcome.TRUE_POSITIVE)
            self.assertEqual(obs1.conditioned_detector_outcome, DetectorOutcome.TRUE_POSITIVE)

            # Caso 2 (Negativo podado e rejeitado):
            obs2 = observations[1]
            self.assertEqual(obs2.evaluation_case_id, "CASE-2")
            self.assertEqual(obs2.selection_outcome, CandidateSelectionOutcome.NEGATIVE_DROPPED)
            self.assertEqual(obs2.unconditioned_detector_outcome, DetectorOutcome.TRUE_NEGATIVE)
            self.assertIsNone(obs2.conditioned_detector_outcome)

            # Métricas no summary
            self.assertIn("candidate_selection_metrics", summary)
            self.assertIn("unconditioned_detector_metrics", summary)
            self.assertIn("conditioned_detector_metrics", summary)
            self.assertIn("end_to_end_pipeline_metrics", summary)

            # Breakdown por classe preserva strata agregado ordenado
            c1_info = summary["breakdown_by_class"]["P-ABBR"]
            self.assertEqual(c1_info["strata"], ["FASTENERS"])
            self.assertEqual(c1_info["total_cases"], 1)

    def test_scientific_payload_strict_determinism(self) -> None:
        import tempfile
        from datetime import datetime, timezone
        from experiments.sr001_baseline_b_harness_v2 import (
            build_evidence_payload,
            evaluate_tranche,
        )

        with tempfile.TemporaryDirectory() as tmpdir_s:
            desc = self._create_synthetic_tranche(Path(tmpdir_s))

            obs1, summary1 = evaluate_tranche(desc)
            payload1 = build_evidence_payload(
                summary=summary1,
                observations=obs1,
                descriptor=desc,
                run_id="RUN-AAA-111",
                evaluated_at=datetime(2026, 10, 1, 10, 0, 0, tzinfo=timezone.utc),
            )

            obs2, summary2 = evaluate_tranche(desc)
            payload2 = build_evidence_payload(
                summary=summary2,
                observations=obs2,
                descriptor=desc,
                run_id="RUN-BBB-222",
                evaluated_at=datetime(2026, 10, 1, 10, 5, 0, tzinfo=timezone.utc),
            )

            # Igualdade científica estrita
            self.assertEqual(payload1["scientific_payload"], payload2["scientific_payload"])

            # Diferença esperada nos metadados de execução
            self.assertNotEqual(payload1["metadata"]["run_id"], payload2["metadata"]["run_id"])
            self.assertNotEqual(payload1["metadata"]["evaluated_at"], payload2["metadata"]["evaluated_at"])

    def test_evidence_payload_json_serializability(self) -> None:
        import json
        import tempfile
        from datetime import datetime, timezone
        from experiments.sr001_baseline_b_harness_v2 import (
            build_evidence_payload,
            evaluate_tranche,
        )

        with tempfile.TemporaryDirectory() as tmpdir_s:
            desc = self._create_synthetic_tranche(Path(tmpdir_s))
            obs, summary = evaluate_tranche(desc)
            payload = build_evidence_payload(
                summary=summary,
                observations=obs,
                descriptor=desc,
                run_id="RUN-JSON-TEST",
                evaluated_at=datetime(2026, 10, 1, 10, 0, 0, tzinfo=timezone.utc),
            )

            # Executa json.dumps sem TypeError e sem custom encoder
            serialized = json.dumps(payload, sort_keys=True, indent=2)
            self.assertIsInstance(serialized, str)

            # Round-trip de verificação
            deserialized = json.loads(serialized)
            self.assertEqual(deserialized["metadata"]["run_id"], "RUN-JSON-TEST")
            self.assertIn("scientific_payload", deserialized)
            self.assertEqual(len(deserialized["scientific_payload"]["observations"]), 2)


if __name__ == "__main__":
    unittest.main()
