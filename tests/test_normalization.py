import unittest

from agent_lab.normalization import category_token, normalize_text, numeric_tokens


class NormalizationTests(unittest.TestCase):
    def test_removes_accents_and_punctuation(self) -> None:
        self.assertEqual(normalize_text("Válvula, esfera!"), "VALVULA ESFERA")

    def test_expands_category_abbreviation(self) -> None:
        self.assertEqual(category_token("VALV ESF 2IN"), "VALVULA")

    def test_extracts_numbers_joined_to_letters(self) -> None:
        self.assertEqual(numeric_tokens("M10X30 CL8.8"), {"10", "30", "8"})


if __name__ == "__main__":
    unittest.main()

