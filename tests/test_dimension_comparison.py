import unittest

from agent_lab.dimension_comparison import (
    DimensionPairRelation,
    compare_ordered_dimensions,
)


class DimensionComparisonTests(unittest.TestCase):
    def test_alias_and_case_are_lexically_equivalent(self):
        self.assertEqual(
            compare_ordered_dimensions("PARAF 1/2 X 2 POL", "parafuso 1/2x2 polegadas"),
            DimensionPairRelation.MATCH,
        )

    def test_order_reversal_is_a_mismatch(self):
        self.assertEqual(
            compare_ordered_dimensions("PARAFUSO 1/2 X 2 POL", "PARAFUSO 2 X 1/2 POL"),
            DimensionPairRelation.MISMATCH,
        )

    def test_cross_unit_comparison_requires_governed_conversion(self):
        self.assertEqual(
            compare_ordered_dimensions("BARRA 10 X 30 MM", "BARRA 10 X 30 IN"),
            DimensionPairRelation.UNKNOWN,
        )

    def test_potentially_equivalent_cross_unit_values_do_not_claim_mismatch(self):
        self.assertEqual(
            compare_ordered_dimensions("BARRA 25.4 X 50.8 MM", "BARRA 1 X 2 IN"),
            DimensionPairRelation.UNKNOWN,
        )

    def test_same_unit_explicit_dimension_mismatch(self):
        self.assertEqual(
            compare_ordered_dimensions("BARRA 10 X 30 MM", "BARRA 10 X 40 MM"),
            DimensionPairRelation.MISMATCH,
        )

    def test_equivalent_fraction_and_decimal_spellings_match(self):
        self.assertEqual(
            compare_ordered_dimensions("BARRA 1/2 X 2 MM", "BARRA 0.5 X 2.0 MM"),
            DimensionPairRelation.MATCH,
        )

    def test_invalid_zero_denominator_fails_closed(self):
        self.assertEqual(
            compare_ordered_dimensions("BARRA 1/0 X 2 MM", "BARRA 1 X 2 MM"),
            DimensionPairRelation.UNKNOWN,
        )

    def test_missing_unit_is_unknown_instead_of_match(self):
        self.assertEqual(
            compare_ordered_dimensions("BARRA 10 X 30", "BARRA 10 X 30 MM"),
            DimensionPairRelation.UNKNOWN,
        )

    def test_missing_or_ambiguous_pair_is_unknown(self):
        self.assertEqual(
            compare_ordered_dimensions("BARRA 10 MM", "BARRA 10 X 30 MM"),
            DimensionPairRelation.UNKNOWN,
        )
        self.assertEqual(
            compare_ordered_dimensions("BARRA 10 X 30 X 40 MM", "BARRA 10 X 30 MM"),
            DimensionPairRelation.UNKNOWN,
        )

    def test_result_is_symmetric(self):
        left, right = "PARAFUSO 1/2 X 2 POL", "PARAFUSO 2 X 1/2 POL"
        self.assertEqual(
            compare_ordered_dimensions(left, right),
            compare_ordered_dimensions(right, left),
        )


if __name__ == "__main__":
    unittest.main()
