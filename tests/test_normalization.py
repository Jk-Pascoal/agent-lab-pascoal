import unittest

from agent_lab.normalization import category_token, normalize_text, numeric_tokens, ordered_dimension_pair


class NormalizationTests(unittest.TestCase):
    def test_removes_accents_and_punctuation(self) -> None:
        self.assertEqual(normalize_text("Válvula, esfera!"), "VALVULA ESFERA")

    def test_expands_category_abbreviation(self) -> None:
        self.assertEqual(category_token("VALV ESF 2IN"), "VALVULA")

    def test_extracts_numbers_joined_to_letters(self) -> None:
        self.assertEqual(numeric_tokens("M10X30 CL8.8"), {"10", "30", "8"})

    def test_ordered_fractions_are_not_interchangeable(self) -> None:
        first = ordered_dimension_pair("PARAFUSO 1/2 X 2 POL")
        inverted = ordered_dimension_pair("PARAFUSO 2 X 1/2 POL")
        self.assertEqual(first, ("1/2", "2", "IN"))
        self.assertEqual(inverted, ("2", "1/2", "IN"))
        self.assertNotEqual(first, inverted)

    def test_dimension_unit_alias_and_spacing(self) -> None:
        self.assertEqual(
            ordered_dimension_pair("parafuso 1/2x2 polegadas"),
            ordered_dimension_pair("PARAFUSO 1/2 X 2 POL"),
        )

    def test_ambiguous_or_absent_dimensions_do_not_infer_roles(self) -> None:
        self.assertIsNone(ordered_dimension_pair("PARAFUSO 1/2 POL"))
        self.assertIsNone(ordered_dimension_pair("PARAFUSO 1/2 X 2 X 4 POL"))

    def test_compact_or_spaced_dimension_chain_is_rejected(self) -> None:
        for description in (
            "PARAF 10X30X40MM",
            "PARAF 10 X 30 X 40 MM",
            "PARAF 10×30×40MM",
            "PARAF 10 X30X40 MM",
        ):
            with self.subTest(description=description):
                self.assertIsNone(ordered_dimension_pair(description))

    def test_single_compact_dimension_pair_remains_supported(self) -> None:
        self.assertEqual(ordered_dimension_pair("PARAF 10X30MM"), ("10", "30", "MM"))

    def test_dimension_pair_keeps_millimeter_unit(self) -> None:
        self.assertEqual(ordered_dimension_pair("PARAF M10X30MM"), ("10", "30", "MM"))


if __name__ == "__main__":
    unittest.main()

