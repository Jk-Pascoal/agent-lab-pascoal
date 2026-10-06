"""Testes contratuais e unitários da Sonda Experimental B1 (SR-001 / Issue #158).

Validação estrita de:
1. ambos PNs preenchidos e diferentes -> conflict=True;
2. PNs iguais -> conflict=False;
3. A vazio -> False;
4. B vazio -> False;
5. ambos vazios -> False;
6. B1 não interfere em prediction=False original;
7. B1 não interfere em decisão positiva proveniente exclusivamente da Rota 1;
8. B1 suprime somente uma decisão Route 2 + PN conflict;
9. B0 permanece idêntico ao detector original (prova par-a-par nos 40 pares reais da T02);
10. determinismo do payload científico.
"""

from __future__ import annotations

import json
import unittest
from datetime import datetime, timezone
from pathlib import Path

from agent_lab.domain import MaterialRecord
from agent_lab.duplicates import is_possible_duplicate
from experiments.sr001_baseline_b_harness_v2 import load_and_validate_tranche
from experiments.sr001_b1_pn_conflict_probe import (
    B1CaseObservation,
    ConfusionMetrics,
    DetectorRoute,
    build_b1_evidence_payload,
    check_pn_conflict,
    compute_confusion_metrics,
    detect_original_decision,
    evaluate_decision_b1,
    evaluate_tranche_b1,
    get_tranche_02_descriptor,
)


class TestB1PnConflictPredicate(unittest.TestCase):
    """Testes dos requisitos 1 a 5: Semântica estrita de check_pn_conflict."""

    def _make_record(self, material_id: str, pn: str, mfg: str = "BOSCH") -> MaterialRecord:
        return MaterialRecord(
            material_id=material_id,
            description_short="DESC SHORT",
            long_description="DESC LONG",
            material_group="GRP1",
            unit="UN",
            manufacturer=mfg,
            manufacturer_part_number=pn,
        )

    def test_req_1_both_pns_populated_and_different_returns_conflict_true(self) -> None:
        """1. Ambos PNs preenchidos e diferentes -> conflict=True."""
        rec_a = self._make_record("M1", "ABC-123")
        rec_b = self._make_record("M2", "DEF-456")

        has_conf, pn_a, pn_b = check_pn_conflict(rec_a, rec_b)
        self.assertTrue(has_conf)
        self.assertEqual(pn_a, "ABC 123")
        self.assertEqual(pn_b, "DEF 456")

    def test_req_2_both_pns_identical_returns_conflict_false(self) -> None:
        """2. PNs iguais após normalização -> conflict=False."""
        rec_a = self._make_record("M1", "ABC-123")
        rec_b = self._make_record("M2", "abc 123")

        has_conf, pn_a, pn_b = check_pn_conflict(rec_a, rec_b)
        self.assertFalse(has_conf)
        self.assertEqual(pn_a, "ABC 123")
        self.assertEqual(pn_b, "ABC 123")

    def test_req_3_pn_a_empty_returns_conflict_false(self) -> None:
        """3. PN de A vazio -> False."""
        rec_a = self._make_record("M1", "")
        rec_b = self._make_record("M2", "ABC-123")
        has_conf, pn_a, pn_b = check_pn_conflict(rec_a, rec_b)
        self.assertFalse(has_conf)
        self.assertEqual(pn_a, "")
        self.assertEqual(pn_b, "ABC 123")

        # Whitespace only
        rec_a_ws = self._make_record("M1", "   \t\n  ")
        has_conf_ws, pn_a_ws, _ = check_pn_conflict(rec_a_ws, rec_b)
        self.assertFalse(has_conf_ws)
        self.assertEqual(pn_a_ws, "")

    def test_req_4_pn_b_empty_returns_conflict_false(self) -> None:
        """4. PN de B vazio -> False."""
        rec_a = self._make_record("M1", "ABC-123")
        rec_b = self._make_record("M2", "")
        has_conf, pn_a, pn_b = check_pn_conflict(rec_a, rec_b)
        self.assertFalse(has_conf)
        self.assertEqual(pn_a, "ABC 123")
        self.assertEqual(pn_b, "")

        # Whitespace only
        rec_b_ws = self._make_record("M2", "   ")
        has_conf_ws, _, pn_b_ws = check_pn_conflict(rec_a, rec_b_ws)
        self.assertFalse(has_conf_ws)
        self.assertEqual(pn_b_ws, "")

    def test_req_5_both_pns_empty_returns_conflict_false(self) -> None:
        """5. Ambos vazios -> False."""
        rec_a = self._make_record("M1", "")
        rec_b = self._make_record("M2", "")
        has_conf, pn_a, pn_b = check_pn_conflict(rec_a, rec_b)
        self.assertFalse(has_conf)
        self.assertEqual(pn_a, "")
        self.assertEqual(pn_b, "")

        rec_a_ws = self._make_record("M1", "   ")
        rec_b_ws = self._make_record("M2", "   ")
        has_conf_ws, pn_a_ws, pn_b_ws = check_pn_conflict(rec_a_ws, rec_b_ws)
        self.assertFalse(has_conf_ws)
        self.assertEqual(pn_a_ws, "")
        self.assertEqual(pn_b_ws, "")


class TestB1CounterfactualModel(unittest.TestCase):
    """Testes dos requisitos 6 a 8: Modelo contrafactual B1."""

    def _make_pair(
        self,
        pn_a: str,
        pn_b: str,
        mfg_a: str,
        mfg_b: str,
        grp_a: str,
        grp_b: str,
        desc_a: str,
        desc_b: str,
    ) -> tuple[MaterialRecord, MaterialRecord]:
        rec_a = MaterialRecord(
            material_id="MAT-A",
            description_short=desc_a,
            long_description="",
            material_group=grp_a,
            unit="UN",
            manufacturer=mfg_a,
            manufacturer_part_number=pn_a,
        )
        rec_b = MaterialRecord(
            material_id="MAT-B",
            description_short=desc_b,
            long_description="",
            material_group=grp_b,
            unit="UN",
            manufacturer=mfg_b,
            manufacturer_part_number=pn_b,
        )
        return rec_a, rec_b

    def test_req_6_b1_does_not_interfere_with_original_negative_prediction(self) -> None:
        """6. B1 não interfere em prediction=False original."""
        rec_a, rec_b = self._make_pair(
            pn_a="PN-1",
            pn_b="PN-2",  # PN conflict é True
            mfg_a="M1",
            mfg_b="M2",
            grp_a="VALVULAS",
            grp_b="PARAFUSOS",
            desc_a="VALVULA ESFERA 2 POL 150",
            desc_b="PARAFUSO SEXTAVADO M12 60",
        )
        pred_b1, pred_orig, route_orig, has_conf, _, _ = evaluate_decision_b1(rec_a, rec_b)
        self.assertFalse(pred_orig)
        self.assertEqual(route_orig, DetectorRoute.NONE)
        self.assertTrue(has_conf)
        self.assertFalse(pred_b1)

    def test_req_7_b1_does_not_interfere_with_route_1_positive_decision(self) -> None:
        """7. B1 não interfere em decisão positiva proveniente exclusivamente da Rota 1."""
        rec_a, rec_b = self._make_pair(
            pn_a="6204-2RSH",
            pn_b="6204-2RSH",
            mfg_a="SKF",
            mfg_b="SKF",
            grp_a="ROLAMENTOS",
            grp_b="GERAL",
            desc_a="ROLAMENTO RIGIDO ESFERAS 20X47X14",
            desc_b="PECA MECANICA DIVERSA 100",
        )
        pred_b1, pred_orig, route_orig, has_conf, _, _ = evaluate_decision_b1(rec_a, rec_b)
        self.assertTrue(pred_orig)
        self.assertEqual(route_orig, DetectorRoute.ROUTE_1)
        self.assertFalse(has_conf)
        self.assertTrue(pred_b1)

    def test_req_8_b1_suppresses_only_route_2_with_pn_conflict(self) -> None:
        """8. B1 suprime somente uma decisão Route 2 + PN conflict."""
        # Caso A: Rota 2 com PN conflict -> Suprimido (pred_orig=True -> pred_b1=False)
        rec_a1, rec_b1 = self._make_pair(
            pn_a="931-12-060",
            pn_b="931-12-070",  # Diferentes -> conflict True
            mfg_a="CISER",
            mfg_b="CISER",
            grp_a="FIXADORES",
            grp_b="FIXADORES",
            desc_a="PARAFUSO SEXTAVADO DIN 931 M12X60 ACO 8.8",
            desc_b="PARAFUSO SEXTAVADO DIN 931 M12X70 ACO 8.8",
        )
        pred_b1_1, pred_orig_1, route_orig_1, has_conf_1, _, _ = evaluate_decision_b1(rec_a1, rec_b1)
        self.assertTrue(pred_orig_1)
        self.assertEqual(route_orig_1, DetectorRoute.ROUTE_2)
        self.assertTrue(has_conf_1)
        self.assertFalse(pred_b1_1)

        # Caso B: Rota 2 SEM PN conflict (um registro sem PN) -> NÃO suprimido
        rec_a2, rec_b2 = self._make_pair(
            pn_a="931-12-060",
            pn_b="",  # Sem PN em B -> conflict False
            mfg_a="CISER",
            mfg_b="",
            grp_a="FIXADORES",
            grp_b="FIXADORES",
            desc_a="PARAFUSO SEXTAVADO DIN 931 M12X60 ACO 8.8",
            desc_b="PARAFUSO SEXTAVADO DIN 931 M12X60 ACO 8.8",
        )
        pred_b1_2, pred_orig_2, route_orig_2, has_conf_2, _, _ = evaluate_decision_b1(rec_a2, rec_b2)
        self.assertTrue(pred_orig_2)
        self.assertEqual(route_orig_2, DetectorRoute.ROUTE_2)
        self.assertFalse(has_conf_2)
        self.assertTrue(pred_b1_2)


class TestB1Tranche02ExecutionAndControl(unittest.TestCase):
    """Testes dos requisitos 9 e 10: Reprodução exata de B0 e Determinismo do Payload."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.descriptor = get_tranche_02_descriptor()
        cls.observations, cls.summary = evaluate_tranche_b1(cls.descriptor)

    def test_req_9_b0_matches_original_detector_exactly(self) -> None:
        """9. B0 permanece idêntico ao detector original em todos os 40 pares reais da T02.

        Prova equivalência estrita par-a-par:
        detect_original_decision(a, b)[0] == is_possible_duplicate(a, b) == obs.prediction_original
        para 40/40 pares reais do catálogo congelado.
        """
        catalog_records, gt_records, _ = load_and_validate_tranche(self.descriptor)
        records_by_id = {r.material_id: r for r in catalog_records}
        obs_by_case_id = {o.evaluation_case_id: o for o in self.observations}

        self.assertEqual(len(gt_records), 40)
        self.assertEqual(len(self.observations), 40)

        for gt in gt_records:
            rec_a = records_by_id[gt.material_id_a]
            rec_b = records_by_id[gt.material_id_b]

            direct_prediction = is_possible_duplicate(rec_a, rec_b)
            reconstructed_prediction, reconstructed_route = detect_original_decision(rec_a, rec_b)

            # Equivalência direta estrita par-a-par
            self.assertEqual(
                direct_prediction,
                reconstructed_prediction,
                f"Divergência par-a-par no caso {gt.evaluation_case_id}: "
                f"direct={direct_prediction} vs reconstructed={reconstructed_prediction}",
            )

            # Confronto com a observação armazenada no harness
            obs = obs_by_case_id[gt.evaluation_case_id]
            self.assertEqual(
                obs.prediction_original,
                direct_prediction,
                f"Divergência com observação armazenada no caso {gt.evaluation_case_id}: "
                f"stored={obs.prediction_original} vs direct={direct_prediction}",
            )

            # Validação da integridade de rota
            if direct_prediction:
                self.assertIn(reconstructed_route, [DetectorRoute.ROUTE_1, DetectorRoute.ROUTE_2])
            else:
                self.assertEqual(reconstructed_route, DetectorRoute.NONE)

        # Assertions agregadas incondicionais
        b0_uncond = self.summary["b0_unconditioned_metrics"]
        self.assertEqual(b0_uncond["tp"], 19)
        self.assertEqual(b0_uncond["fp"], 17)
        self.assertEqual(b0_uncond["tn"], 3)
        self.assertEqual(b0_uncond["fn"], 1)
        self.assertAlmostEqual(b0_uncond["precision"], 19 / 36, places=10)
        self.assertAlmostEqual(b0_uncond["recall"], 0.95, places=10)
        self.assertAlmostEqual(b0_uncond["f1"], 0.6785714285714285, places=10)

    def test_b1_execution_results_and_metrics(self) -> None:
        """Validação metrológica dos resultados de B1 na Tranche 02."""
        b1_uncond = self.summary["b1_unconditioned_metrics"]
        self.assertEqual(b1_uncond["tp"], 12)
        self.assertEqual(b1_uncond["fp"], 0)
        self.assertEqual(b1_uncond["tn"], 20)
        self.assertEqual(b1_uncond["fn"], 8)
        self.assertEqual(b1_uncond["precision"], 1.0)
        self.assertEqual(b1_uncond["recall"], 0.6)
        self.assertAlmostEqual(b1_uncond["f1"], 0.75, places=10)

        comp = self.summary["comparative_metrics"]
        self.assertEqual(comp["delta_fp"], 17)
        self.assertAlmostEqual(comp["delta_recall_p"], 0.35, places=10)
        self.assertFalse(comp["safety_goal_delta_recall_zero_satisfied"])
        self.assertEqual(comp["total_pairs_with_pn_conflict"], 27)
        self.assertEqual(comp["conflict_breakdown_in_b0"], {"TP": 7, "FP": 17, "TN": 3, "FN": 0})
        self.assertEqual(comp["changed_decisions_count"], 24)

    def test_failure_modes_and_sacrificed_positives_breakdown(self) -> None:
        """Verifica a supressão nos 4 modos de falha e os 7 TPs sacrificados."""
        fm = self.summary["failure_mode_breakdown"]
        self.assertEqual(fm["FM-1"]["suppressed_fp"], 4)
        self.assertEqual(fm["FM-2"]["suppressed_fp"], 4)
        self.assertEqual(fm["FM-3"]["suppressed_fp"], 5)
        self.assertEqual(fm["FM-4"]["suppressed_fp"], 4)

        pos = self.summary["positive_classes_breakdown"]
        self.assertEqual(pos["P-SEPARATOR"]["sacrificed_tp"], 4)
        self.assertEqual(pos["P-PN-STRUCTURAL"]["sacrificed_tp"], 3)
        self.assertEqual(pos["P-ABBR"]["sacrificed_tp"], 0)
        self.assertEqual(pos["P-CROSS-GRP"]["sacrificed_tp"], 0)
        self.assertEqual(pos["P-MFG-MISSING"]["sacrificed_tp"], 0)
        self.assertEqual(pos["P-TRUNCATED"]["sacrificed_tp"], 0)

    def test_req_10_scientific_payload_determinism(self) -> None:
        """10. Determinismo do payload científico."""
        evaluated_at = datetime(2026, 10, 6, 12, 0, 0, tzinfo=timezone.utc)
        payload1 = build_b1_evidence_payload(
            summary=self.summary,
            observations=self.observations,
            descriptor=self.descriptor,
            run_id="RUN-TEST-001",
            evaluated_at=evaluated_at,
        )
        payload2 = build_b1_evidence_payload(
            summary=self.summary,
            observations=self.observations,
            descriptor=self.descriptor,
            run_id="RUN-TEST-001",
            evaluated_at=evaluated_at,
        )

        json1 = json.dumps(payload1, sort_keys=True, ensure_ascii=False)
        json2 = json.dumps(payload2, sort_keys=True, ensure_ascii=False)
        self.assertEqual(json1, json2)

        # Imutabilidade de estruturas
        with self.assertRaises((AttributeError, TypeError)):
            self.observations[0].decision_changed = False  # type: ignore[misc]
