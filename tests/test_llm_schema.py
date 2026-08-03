import unittest

from pydantic import ValidationError

from agent_lab.llm_schema import GovernanceAgentOutput


VALID_OUTPUT = {
    "material_id": "MAT-0002",
    "decision": "REVIEW",
    "confidence": 0.82,
    "issues": ["POSSIBLE_DUPLICATE"],
    "summary": "O material pode estar duplicado.",
    "evidence": ["Descrição e fabricante semelhantes."],
}


class GovernanceAgentOutputTests(unittest.TestCase):
    def test_accepts_valid_structured_output(self) -> None:
        output = GovernanceAgentOutput.model_validate(VALID_OUTPUT)

        self.assertEqual(output.material_id, "MAT-0002")
        self.assertEqual(output.decision.value, "REVIEW")
        self.assertEqual(
            output.issues[0].value,
            "POSSIBLE_DUPLICATE",
        )

    def test_rejects_confidence_above_one(self) -> None:
        invalid_output = {
            **VALID_OUTPUT,
            "confidence": 1.10,
        }

        with self.assertRaises(ValidationError):
            GovernanceAgentOutput.model_validate(invalid_output)

    def test_rejects_unexpected_fields(self) -> None:
        invalid_output = {
            **VALID_OUTPUT,
            "invented_field": "informação não permitida",
        }

        with self.assertRaises(ValidationError):
            GovernanceAgentOutput.model_validate(invalid_output)


if __name__ == "__main__":
    unittest.main()