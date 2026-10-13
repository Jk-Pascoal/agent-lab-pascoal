"""Contract gates for B2/FM-1; self-checking CI execution on frozen T02."""
import unittest
from agent_lab.domain import MaterialRecord
from experiments.sr001_b2_dimensional_probe import (
    DimensionalSignal, dimensional_signal, evaluate_b2_pair, evaluate_frozen_t02,
)


def record(identifier, description, pn=""):
    return MaterialRecord(
        material_id=identifier, description_short=description, long_description="",
        unit="UN", manufacturer="", manufacturer_part_number=pn,
        material_group="TEST",
    )


class B2DimensionalContractTests(unittest.TestCase):
    def test_conflicting_fastener_length(self):
        signal, a, b = dimensional_signal(
            record("A", "PARAFUSO SEXTAVADO M12X60 DIN 931"),
            record("B", "PARAFUSO SEXTAVADO M12X70 DIN 931"))
        self.assertEqual(signal, DimensionalSignal.DISAGREEMENT)
        self.assertEqual(a[0], "fastener_length_mm")
        self.assertEqual(b[0], "fastener_length_mm")

    def test_equivalent_delimiters(self):
        signal, _, _ = dimensional_signal(
            record("A", "PARAFUSO ALLEN DIN 912 M12X45"),
            record("B", "PARAFUSO ALLEN DIN 912 M12-45"))
        self.assertEqual(signal, DimensionalSignal.NO_DISAGREEMENT)

    def test_cable_section(self):
        signal, a, b = dimensional_signal(
            record("A", "CABO POTENCIA SECAO 16 MM2"),
            record("B", "CABO POTENCIA SECAO 25 MM2"))
        self.assertEqual(signal, DimensionalSignal.DISAGREEMENT)

    def test_belt_length(self):
        signal, _, _ = dimensional_signal(
            record("A", "CORREIA EM V COMPRIMENTO 60 POL"),
            record("B", "CORREIA EM V COMPRIMENTO 62 POL"))
        self.assertEqual(signal, DimensionalSignal.DISAGREEMENT)

    def test_valve_nominal(self):
        signal, _, _ = dimensional_signal(
            record("A", "VALVULA GAVETA CLASSE 150 DN 3 POL"),
            record("B", "VALVULA GAVETA CLASSE 150 DN 4 POL"))
        self.assertEqual(signal, DimensionalSignal.DISAGREEMENT)

    def test_unilateral_absence(self):
        signal, _, _ = dimensional_signal(
            record("A", "CABO POTENCIA SECAO 16 MM2"),
            record("B", "CABO POTENCIA"))
        self.assertEqual(signal, DimensionalSignal.UNKNOWN)

    def test_different_physical_roles_unknown(self):
        signal, _, _ = dimensional_signal(
            record("A", "PARAFUSO M12X60"),
            record("B", "CABO SECAO 60 MM2"))
        self.assertEqual(signal, DimensionalSignal.UNKNOWN)

    def test_part_number_only_unknown(self):
        signal, _, _ = dimensional_signal(
            record("A", "ROLAMENTO SKF 6305", "6305"),
            record("B", "ROLAMENTO SKF 6306", "6306"))
        self.assertEqual(signal, DimensionalSignal.UNKNOWN)

    def test_nominal_conversion_not_assumed(self):
        signal, _, _ = dimensional_signal(
            record("A", "VALVULA DN 100 MM 4 POL"),
            record("B", "VALVULA DN100 4 POL"))
        self.assertEqual(signal, DimensionalSignal.UNKNOWN)

    def test_symmetry(self):
        a, b = record("A", "CABO SECAO 16 MM2"), record("B", "CABO SECAO 25 MM2")
        self.assertEqual(dimensional_signal(a, b)[0], dimensional_signal(b, a)[0])

    def test_route_one_preservation(self):
        a = record("A", "CABO SECAO 16 MM2", "SAME")
        b = record("B", "CABO SECAO 25 MM2", "SAME")
        # Without matching manufacturer, R1 does not apply; nonpositive baseline
        self.assertFalse(evaluate_b2_pair(a, b)[1] if not evaluate_b2_pair(a, b)[0] else False)

    def test_frozen_t02_gate_and_all_four_quadrants(self):
        result = evaluate_frozen_t02()
        b0, b2 = result["b0_unconditioned"], result["b2_unconditioned"]
        self.assertEqual((b0["tp"], b0["fp"], b0["tn"], b0["fn"]), (19, 17, 3, 1))
        self.assertEqual(result["counts"], {"pairs": 40, "selected": 39})
        self.assertEqual(b2["tp"], 19)
        self.assertEqual(b2["fn"], 1)
        self.assertEqual(result["safety_goal"], "PASS")
        changed = result["changed"]
        self.assertTrue(all((not o["truth"]) and o["route"] == "ROUTE_2" for o in changed))
        self.assertEqual(len(changed), 4)
        self.assertEqual({o["case_id"][-3:] for o in changed}, {"005", "013", "029", "037"})
        self.assertEqual((b2["tp"], b2["fp"], b2["tn"], b2["fn"]), (19, 13, 7, 1))
        self.assertEqual(result["b2_conditioned"]["tp"], 19)
        self.assertEqual(result["b2_conditioned"]["fn"], 0)


if __name__ == "__main__":
    unittest.main()
